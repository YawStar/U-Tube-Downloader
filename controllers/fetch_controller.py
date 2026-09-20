# -*- coding: utf-8 -*-
"""
Fetch Controller

yt-dlp --dump-json ကို QProcess ဖြင့် run ပြီး Video Info ကို ရယူသည်။

main.py ထဲက ဒီ logic တွေကို စုစည်းထားသည်:
    • on_get_info_clicked() — process start
    • read_info_output() — stdout buffer
    • read_info_error() — stderr + cookies error detection
    • on_info_finished() — JSON parse + final result

View ကို signals ဖြင့် notify လုပ်သည်:

    fetch_started           — UI state ပြောင်းရန်
    fetch_output_received   — log buffer အတွက် (optional)
    fetch_completed(dict)   — info dict
    fetch_failed(str)       — error message
    fetch_cancelled         — user ဖျက်လိုက်
    cookies_required        — cookies error detect
"""
import json
from PySide6.QtCore import QObject, QProcess, Signal

from core.services.yt_dlp_service import YtDlpService
from utils.process_utils import kill_process_tree


class FetchController(QObject):
    """yt-dlp fetch info process ကို စီမံသည်။"""

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    fetch_started = Signal()
    fetch_completed = Signal(dict)      # parsed info dict
    fetch_failed = Signal(str)          # error message
    fetch_cancelled = Signal()
    cookies_required = Signal()

    def __init__(self, yt_dlp_service: YtDlpService, parent=None):
        """
        Args:
            yt_dlp_service: args builder service
            parent: Qt parent (MainWindow)
        """
        super().__init__(parent)
        self.yt_dlp_service = yt_dlp_service

        # QProcess
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)

        # State
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        self._cancelled = False
        self._cookies_error_detected = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_running(self) -> bool:
        """Process လုပ်နေဆဲလား"""
        return self.process.state() == QProcess.ProcessState.Running

    def start(self, url: str, settings: dict) -> None:
        """
        Fetch info စတင်သည်။

        Args:
            url: video URL
            settings: config settings dict
        """
        if self.is_running():
            return

        # State reset
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        self._cancelled = False
        self._cookies_error_detected = False

        # Args ဆောက်
        args = self.yt_dlp_service.build_info_args(url, settings)
        yt_dlp_path = self.yt_dlp_service.yt_dlp_path

        # Signal
        self.fetch_started.emit()

        # Process start
        self.process.start(yt_dlp_path, args)

    def cancel(self) -> None:
        """User က Stop Fetching နှိပ်လိုက်"""
        if not self.is_running():
            return

        self._cancelled = True
        kill_process_tree(self.process)
        # _on_finished မှ fetch_cancelled emit လုပ်မည်

    def get_error_output(self) -> str:
        """လက်ရှိ stderr buffer ကို ပြန်ပေး (View က error ပြရန်)"""
        return self._stderr_buffer

    # ------------------------------------------------------------------
    # QProcess handlers
    # ------------------------------------------------------------------
    def _on_stdout(self) -> None:
        data = (
            self.process
            .readAllStandardOutput()
            .data()
            .decode("utf-8", errors="replace")
        )
        if data:
            self._stdout_buffer += data

    def _on_stderr(self) -> None:
        error_data = (
            self.process
            .readAllStandardError()
            .data()
            .decode("utf-8", errors="replace")
        )

        if not error_data:
            return

        self._stderr_buffer += error_data
        error_lower = error_data.lower()

        # Cookies error keywords (main.py နဲ့ ကွက်တိတူ)
        error_keywords = [
            "confirm you're not a bot",
            "sign in to confirm you're not a bot",
            "sign in to confirm",
            "use --cookies-from-browser",
            "requires authentication",
            "video requires authentication",
            "login required",
        ]

        if any(keyword in error_lower for keyword in error_keywords):
            self._cookies_error_detected = True
            print(error_data)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        # Cancel flag
        if self._cancelled:
            self._cancelled = False
            self.fetch_cancelled.emit()
            return

        # Cookies error
        if self._cookies_error_detected:
            self._cookies_error_detected = False
            self.cookies_required.emit()
            return

        # Normal exit မဟုတ်
        if exit_status != QProcess.ExitStatus.NormalExit:
            self.fetch_failed.emit("Fetching process was interrupted.")
            return

        # Exit code error
        if exit_code != 0:
            err = self._stderr_buffer.strip()
            if not err:
                err = f"yt-dlp exited with code {exit_code}."
            self.fetch_failed.emit(err)
            return

        # JSON parse
        full_json = self._stdout_buffer.strip()

        if not full_json:
            self.fetch_failed.emit("No data received from yt-dlp.")
            return

        try:
            info = json.loads(full_json)
        except json.JSONDecodeError as e:
            self.fetch_failed.emit(
                "Error parsing video information: " + str(e)
            )
            return
        except Exception as e:
            self.fetch_failed.emit(
                "Unexpected error while processing video information: " + str(e)
            )
            return

        # Success
        self.fetch_completed.emit(info)