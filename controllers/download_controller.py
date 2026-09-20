# -*- coding: utf-8 -*-
"""
Download Controller

yt-dlp download ကို QProcess ဖြင့် run ပြီး progress ကို
parse လုပ်သည်။

main.py ထဲက ဒီ logic တွေကို စုစည်းထားသည်:
    • on_download_clicked() — process start + args
    • read_download_output() — progress parse + destination detect
    • read_download_error() — error handling
    • on_download_finished() — completed/failed

View ကို signals ဖြင့် notify လုပ်သည်:

    download_started                    — UI state ပြောင်းရန်
    download_log(str)                   — log အတွက်
    download_destination_changed(str)   — final path update
    download_progress(int, str)         — percent + status
    download_indeterminate()            — marquee mode
    download_completed(str)             — final path
    download_failed(str)                — error message
    download_cancelled                  — user ဖျက်လိုက်
"""
import re
from PySide6.QtCore import QObject, QProcess, Signal

from core.services.yt_dlp_service import YtDlpService
from utils.process_utils import kill_process_tree


class DownloadController(QObject):
    """yt-dlp download process ကို စီမံသည်။"""

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    download_started = Signal()
    download_log = Signal(str)                       # stdout log
    download_destination_changed = Signal(str)       # final path update
    download_progress = Signal(int, str)             # percent + status text
    download_indeterminate = Signal()                # marquee mode trigger
    download_completed = Signal(str)                 # final file path
    download_failed = Signal(str)                    # error message
    download_cancelled = Signal()
    download_progress_resumed = Signal()

    def __init__(self, yt_dlp_service: YtDlpService, parent=None):
        super().__init__(parent)
        self.yt_dlp_service = yt_dlp_service

        # QProcess
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)

        # State
        self._cancelled = False
        self.final_path = ""
        self._stderr_buffer = ""
        self._is_marquee = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_running(self) -> bool:
        return self.process.state() == QProcess.ProcessState.Running

    def start(
        self,
        url: str,
        settings: dict,
        selected_format_id: str | None = None,
        gui_overrides: dict | None = None,
        is_windows: bool = False,
    ) -> None:
        """
        Download စတင်သည်။

        Args:
            url: video URL
            settings: config settings dict
            selected_format_id: FormatDialog မှ ရွေးထားသော ID
            gui_overrides: GUI checkbox တန်ဖိုးများ
            is_windows: --windows-filenames ထည့်ရန်
        """
        if self.is_running():
            return

        # State reset
        self._cancelled = False
        self.final_path = ""
        self._stderr_buffer = ""
        self._is_marquee = False

        # Args ဆောက်
        args = self.yt_dlp_service.build_download_args(
            url=url,
            settings=settings,
            selected_format_id=selected_format_id,
            gui_overrides=gui_overrides,
            is_windows=is_windows,
        )
        yt_dlp_path = self.yt_dlp_service.yt_dlp_path

        self.download_started.emit()
        self.process.start(yt_dlp_path, args)

    def cancel(self) -> None:
        """User က Stop Download နှိပ်လိုက်"""
        if not self.is_running():
            return

        self._cancelled = True
        kill_process_tree(self.process)
        # _on_finished မှ download_cancelled emit လုပ်မည်

    def get_error_output(self) -> str:
        return self._stderr_buffer

    # ------------------------------------------------------------------
    # QProcess handlers
    # ------------------------------------------------------------------
    def _on_stdout(self) -> None:
        data = (
            self.process
            .readAllStandardOutput()
            .data()
            .decode("utf-8", errors="ignore")
        )

        if not data:
            return

        if "[download]" not in data:
            self.download_log.emit(data)

        for line in data.splitlines():
            # Destination path
            if "[download] Destination:" in line:
                self.final_path = line.replace(
                    "[download] Destination:", ""
                ).strip()
                self.download_log.emit(data)
                self.download_destination_changed.emit(self.final_path)
                continue

            # Merger path
            if "[Merger] Merging formats into" in line:
                self.final_path = (
                    line.replace("[Merger] Merging formats into", "")
                    .replace('"', "")
                    .strip()
                )
                self.download_destination_changed.emit(self.final_path)
                # ⭐ Postprocess → marquee
                self._is_marquee = True
                self.download_indeterminate.emit()
                continue

            # Postprocess markers
            if (
                "[ExtractAudio]" in line
                or "[EmbedFilename]" in line
            ):
                # ⭐ Postprocess → marquee
                self._is_marquee = True
                self.download_indeterminate.emit()
                continue

            # Progress line
            if "[download]" in line and "|" in line:
                data_part = line.replace("[download]", "").strip()
                parts = data_part.split("|")

                if len(parts) >= 6:
                    raw_percent = parts[0]
                    raw_fileSize = parts[1]
                    raw_speed = parts[2]
                    raw_eta = parts[3]

                    try:
                        pct_match = re.search(r"([\d.]+)", raw_percent)
                        if pct_match:
                            percent_int = int(float(pct_match.group(1)))
                            status = (
                                f"Downloading... {raw_percent} | "
                                f"Size: {raw_fileSize} | "
                                f"Speed: {raw_speed} | "
                                f"ETA: {raw_eta}"
                            )
                            self.download_progress.emit(percent_int, status)
                    except Exception:
                        pass

    def _on_stderr(self) -> None:
        error_data = (
            self.process
            .readAllStandardError()
            .data()
            .decode("utf-8", errors="ignore")
        )
        if error_data:
            self._stderr_buffer += error_data

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if self._cancelled:
            self._cancelled = False
            self.download_cancelled.emit()
            return

        if exit_code == 0:
            self.download_completed.emit(self.final_path)
        else:
            err = self._stderr_buffer.strip()
            if not err:
                err = f"Download failed with exit code {exit_code}."
            self.download_failed.emit(err)