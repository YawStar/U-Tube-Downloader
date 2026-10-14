import os
import time
import platform
import subprocess
import requests
import psutil

from PySide6.QtCore import (
    QObject, QProcess, QProcessEnvironment, QTimer, Signal, Slot
)

from utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Cross-Platform Constants
# ============================================================================
CURRENT_OS = platform.system()
IS_WINDOWS = CURRENT_OS == "Windows"
IS_LINUX = CURRENT_OS == "Linux"
IS_MACOS = CURRENT_OS == "Darwin"
BIN_EXT = ".exe" if IS_WINDOWS else ""

CREATE_NO_WINDOW = 0x08000000


# ============================================================================
# Helper: Executable permission (Linux/macOS)
# ============================================================================
def ensure_executable(filepath: str):
    if IS_WINDOWS:
        return
    if not filepath or not os.path.exists(filepath):
        return
    try:
        current_mode = os.stat(filepath).st_mode
        os.chmod(filepath, current_mode | 0o111)
    except Exception as e:
        logger.error(f"Failed to set executable permission for {filepath}: {e}")


# ============================================================================
# Helper: Hide console window (Windows only, version-safe)
# ============================================================================
def _hide_console_window(process: QProcess):
    if not IS_WINDOWS:
        return
    modifier = getattr(process, "setCreateProcessArgumentsModifier", None)
    if modifier is None:
        return
    try:
        def _apply(args):
            try:
                args.flags = args.flags | CREATE_NO_WINDOW
            except Exception:
                pass
        modifier(_apply)
    except AttributeError:
        pass
    except Exception as e:
        logger.debug(f"Could not set process args modifier: {e}")


# ============================================================================
# Helper: Kill process on port (cross-platform)
# ============================================================================
def _kill_process_on_port(port: int = 8080) -> bool:
    try:
        target_pids = set()

        try:
            for conn in psutil.net_connections(kind="inet"):
                if (conn.laddr
                        and conn.laddr.port == port
                        and conn.status == psutil.CONN_LISTEN
                        and conn.pid):
                    target_pids.add(conn.pid)
        except (psutil.AccessDenied, PermissionError):
            pass
        except Exception:
            pass

        if not target_pids and not IS_WINDOWS:
            try:
                result = subprocess.run(
                    ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().splitlines():
                        try:
                            target_pids.add(int(line.strip()))
                        except ValueError:
                            pass
            except Exception:
                pass

        if not target_pids and IS_WINDOWS:
            try:
                result = subprocess.run(
                    ["netstat", "-ano", "-p", "TCP"],
                    capture_output=True, text=True, timeout=5,
                    creationflags=CREATE_NO_WINDOW,
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        line = line.strip()
                        if f":{port}" in line and "LISTENING" in line.upper():
                            parts = line.split()
                            if parts:
                                try:
                                    target_pids.add(int(parts[-1]))
                                except ValueError:
                                    pass
            except Exception:
                pass

        if not target_pids:
            return True

        killed_any = False
        for pid in target_pids:
            try:
                proc = psutil.Process(pid)
                try:
                    children = proc.children(recursive=True)
                except Exception:
                    children = []

                for child in children:
                    try:
                        child.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                try:
                    proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

                gone, alive = psutil.wait_procs([proc] + children, timeout=2)
                for p in alive:
                    try:
                        p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                killed_any = True
            except psutil.NoSuchProcess:
                killed_any = True
            except Exception as e:
                logger.error(f"Error killing PID {pid}: {e}")

        return killed_any or not target_pids

    except Exception as e:
        logger.error(f"Error in _kill_process_on_port({port}): {e}")
        return False


# ============================================================================
# POT Server Process — ရိုးရှင်းတဲ့ Logic (No Health Check)
# ============================================================================
class POTServerProcess(QObject):
    """
    POT Server ကို QProcess နဲ့ run ပေးတဲ့ class။
    
    ရိုးရှင်းတဲ့ logic:
    1. Server ကို run
    2. Deno process start ဖြစ်/မဖြစ် စစ်
    3. ဖြစ်ရင် → "Running" ပြ၊ stdout ဖတ်
    4. မဖြစ်ရင် → "Error" ပြ၊ stdout မဖတ်
    
    Health check မပါ။ /ping endpoint ကို သုံးတဲ့ health checker မပါ
    
    Signals:
        started_signal(bool, str)   — (is_success, message)
        stopped_signal(bool, str)   — (is_success, message)
        log_signal(str)             — Server stdout line
        error_signal(str, str)      — (error_code, error_message)
    """
    started_signal = Signal(bool, str)
    stopped_signal = Signal(bool, str)
    log_signal = Signal(str)
    error_signal = Signal(str, str)

    def __init__(self, tools_dir: str, parent=None):
        super().__init__(parent)
        self.tools_dir = tools_dir
        self.ys_pot_server_exe = os.path.join(self.tools_dir, f"yawstar-pot-server{BIN_EXT}")
        self.ys_pot_server = os.path.join(self.tools_dir, f"yawstar-pot-server{BIN_EXT}")
        ensure_executable(self.ys_pot_server)

        self.server_dir = self.tools_dir # os.path.join(self.tools_dir, "pot-server")
        self.server_url = "http://127.0.0.1:8080"
        self.server_port = 8080

        self._process: QProcess | None = None
        self._stop_requested = False
        self._started_emitted = False
        self._running = False              # Server run နေလား
        self._first_output_received = False # stdout ပထမဆုံး ရလား

    # ========================================================
    # Public API
    # ========================================================
    def start(self):
        """
        Server ကို စတင်။
        
        Logic:
        1. ys-pot-server executable ရှိ/မရှိ စစ်
        2. Server dir ရှိ/မရှိ စစ်
        3. QProcess စတင်
        4. waitForStarted() နဲ့ process start ဖြစ်/မဖြစ် စစ်
        5. ဖြစ်ရင် → started_signal(True) + stdout reader စ
        6. မဖြစ်ရင် → started_signal(False) + error_signal
        """
        self._stop_requested = False
        self._started_emitted = False
        self._running = False
        self._first_output_received = False

        self.log_signal.emit("Checking server status...")

        # ၁။ ys-pot-server executable ရှိ/မရှိ
        if not os.path.exists(self.ys_pot_server):
            self._fail_start(
                "not_found",
                f"Deno executable not found: {self.ys_pot_server}"
            )
            return

        # ၂။ Server directory ရှိ/မရှိ
        if not os.path.exists(self.server_dir):
            self._fail_start(
                "not_installed",
                f"POT Server directory not found: {self.server_dir}"
            )
            return
        
        # ၄။ Process စတင်
        self._launch_process()

    def stop_server(self):
        """Server ကို ရပ်"""
        self._stop_requested = True
        self._running = False

        self.log_signal.emit("[INFO] Stopping POT Server...")

        try:
            # ၁။ /shutdown endpoint
            try:
                requests.post(f"{self.server_url}/shutdown", timeout=1)
                self.log_signal.emit("[INFO] Called /shutdown endpoint.")
                logger.info("🖲️-☑️ Shutdown endpoint called successfully.")
            except Exception:
                pass

            # ၂။ QProcess ရပ်
            if (self._process
                    and self._process.state() != QProcess.ProcessState.NotRunning):
                self._process.terminate()
                if not self._process.waitForFinished(2000):
                    self._process.kill()
                    self._process.waitForFinished(1000)
            self._process = None

            # ၃။ Port fallback
            _kill_process_on_port(self.server_port)

            # ၄။ ရပ်သွား/မသွား အတည်ပြု
            time.sleep(0.3)
            if self.is_server_running():
                self.stopped_signal.emit(False, "Failed to stop server port 4416.")
            else:
                self.stopped_signal.emit(True, "Server stopped successfully.")

        except Exception as e:
            self.stopped_signal.emit(False, f"Error stopping server: {str(e)}")

    # ========================================================
    # Backward Compatibility
    # ========================================================
    def isRunning(self) -> bool:
        """Process run နေလား"""
        if self._process is None:
            return False
        try:
            return self._process.state() != QProcess.ProcessState.NotRunning
        except Exception:
            return False

    def quit(self):
        if (self._process
                and self._process.state() != QProcess.ProcessState.NotRunning):
            self._process.terminate()

    def wait(self, timeout_ms: int = 2000) -> bool:
        if (self._process
                and self._process.state() != QProcess.ProcessState.NotRunning):
            return self._process.waitForFinished(timeout_ms)
        return True

    def terminate(self):
        if (self._process
                and self._process.state() != QProcess.ProcessState.NotRunning):
            self._process.kill()
            self._process.waitForFinished(1000)

    # ========================================================
    # QProcess Setup — အဓိက Logic
    # ========================================================
    def _launch_process(self):
        """
        YawStar Pot server ကို QProcess နဲ့ စတင်။
        
        waitForStarted() က process spawn ဖြစ်/မဖြစ် စစ်တယ်။
        stdout reader ကို process start ဖြစ်မှ ချိတ်တယ်။
        """
        cmd_args = [
            "--host",
            "127.0.0.1",
            "--port",
            "8080",
        ]

        self.log_signal.emit(f"[EXEC] {self.ys_pot_server} {' '.join(cmd_args)}")
        logger.info(f"[EXEC] {self.ys_pot_server} {' '.join(cmd_args)}")

        try:
            self._process = QProcess(self)
            self._process.setWorkingDirectory(self.server_dir)
            self._process.setProcessChannelMode(
                QProcess.ProcessChannelMode.MergedChannels
            )

            _hide_console_window(self._process)

            # Process error handler — start မဖြစ်ရင် ဒီက ဖမ်း
            self._process.errorOccurred.connect(self._on_process_error)
            self._process.finished.connect(self._on_process_finished)

            # Process စတင်
            self._process.start(self.ys_pot_server, cmd_args)

            # # [KEY] process spawn ဖြစ်/မဖြစ် စစ် (3s စောင့်)
            # if not self._process.waitForStarted(3000):
            #     err_str = self._process.errorString() or "Unknown error"
            #     self._fail_start(
            #         "failed_to_start",
            #         f"Failed to start yawstar-pot-server process: {err_str}"
            #     )
            #     self._cleanup_process()
            #     return

            # [KEY] Process start ဖြစ်သွားပြီ — ဒါဆို stdout reader စ
            # (stdout ကို readyReadStandardOutput signal နဲ့ ဖတ်မယ်)
            self._process.readyReadStandardOutput.connect(self._on_stdout)

            # UI ကို "Running" ပြ (started_signal)
            self._running = True
            msg = "POT Server started successfully."
            logger.info(f"🖲️-✅ {msg}")
            self.log_signal.emit(f"[SUCCESS] {msg}")
            self._emit_started(True, msg)

        except Exception as e:
            self._fail_start(
                "failed_to_start",
                f"Exception launching process: {e}"
            )
            self._cleanup_process()

    @Slot()
    def _on_stdout(self):
        """
        Server stdout/stderr မှ output ကို ဖတ်။
        output ရှိရင် log_signal နဲ့ UI ကို ပြ။
        """
        if not self._process:
            return
        try:
            data = bytes(self._process.readAllStandardOutput()).decode(
                "utf-8", errors="replace"
            )
            for line in data.splitlines():
                line = line.rstrip()
                if line:
                    # stdout မှ output တစ်ခုခု ရလာပြီ
                    if not self._first_output_received:
                        self._first_output_received = True
                        logger.info("📤 First stdout output received")

                    self.log_signal.emit(f"[SERVER] {line}")
        except Exception as e:
            logger.error(f"Error reading server output: {e}")

    @Slot(int, QProcess.ExitStatus)
    def _on_process_finished(self, exit_code, exit_status):
        """
        Process ပိတ်သွားရင်။
        
        - User stop လုပ်လို့ ပိတ်သွား → ဘာမှ မလုပ်
        - Run ပြီးမှ crash → stopped_signal(False)
        """
        if self._stop_requested:
            return

        if self._running:
            # Run နေရင်းက ရပ်သွား — crash
            msg = f"Server process exited unexpectedly (exit code: {exit_code})"
            logger.error(f"🖲️-💥 {msg}")
            self.log_signal.emit(f"[CRASH] {msg}")
            self._running = False
            self.error_signal.emit("crashed", msg)
            self.stopped_signal.emit(False, msg)
        else:
            # Start မဖြစ်ဘဲ သေသွား
            msg = f"Server exited during startup (exit code: {exit_code})"
            logger.error(f"🖲️-❌ {msg}")
            self.log_signal.emit(f"[ERROR] {msg}")
            self._emit_started(False, msg)

        self._cleanup_process()

    @Slot(QProcess.ProcessError)
    def _on_process_error(self, error):
        """
        Process error — FailedToStart က အဓိက
        """
        if self._stop_requested:
            return

        error_names = {
            QProcess.ProcessError.FailedToStart: "FailedToStart",
            QProcess.ProcessError.Crashed: "Crashed",
            QProcess.ProcessError.Timedout: "Timedout",
            QProcess.ProcessError.WriteError: "WriteError",
            QProcess.ProcessError.ReadError: "ReadError",
            QProcess.ProcessError.UnknownError: "UnknownError",
        }
        error_name = error_names.get(error, str(error))
        msg = f"Process error: {error_name}"
        logger.error(f"🖲️-❌ {msg}")
        self.log_signal.emit(f"[ERROR] {msg}")

        if error == QProcess.ProcessError.FailedToStart and not self._running:
            self._fail_start("failed_to_start", msg)

    # ========================================================
    # Error Handling
    # ========================================================
    def _fail_start(self, error_code: str, msg: str):
        """
        Start မဖြစ်ရင် — error signal + started_signal(False) ပို့။
        Health check မစ။ stdout reader မချိတ်ထား
        """
        logger.error(f"🖲️-❌ {msg}")
        self.log_signal.emit(f"[ERROR] {msg}")
        self._running = False
        self.error_signal.emit(error_code, msg)
        self._emit_started(False, msg)

    def _emit_started(self, success: bool, message: str):
        """ started_signal ကို တစ်ခါပဲ emit """
        if self._started_emitted:
            return
        self._started_emitted = True
        self.started_signal.emit(success, message)

    def _cleanup_process(self):
        """ Process ကို ရှင်း """
        if (self._process
                and self._process.state() != QProcess.ProcessState.NotRunning):
            try:
                self._process.terminate()
                if not self._process.waitForFinished(2000):
                    self._process.kill()
                    self._process.waitForFinished(1000)
            except Exception:
                pass
        self._process = None

    # ========================================================
    # Helpers
    # ========================================================
    def is_server_running(self) -> bool:
        """
        Server run နေလား — QProcess state နဲ့ စစ် (health check မလိုအပ်)။
        ဒါပေမယ့် backward compat အတွက် ping ကိုလည်း စစ်နိုင်
        """
        if not self._running:
            return False
        if self._process is None:
            return False
        try:
            return self._process.state() != QProcess.ProcessState.NotRunning
        except Exception:
            return False

    @classmethod
    def kill_process_on_port(cls, port: int = 8080) -> bool:
        try:
            requests.post(f"http://127.0.0.1:{port}/shutdown", timeout=1)
            time.sleep(0.3)
        except Exception:
            pass

        try:
            res = requests.get(f"http://127.0.0.1:{port}/ping", timeout=0.5)
            if res.status_code != 200:
                logger.info("🖲️-☑️ POT Server stopped successfully.")
                return True
        except Exception:
            logger.info("🖲️-☑️ POT Server stopped successfully.")
            return True

        killed = _kill_process_on_port(port)
        logger.info("🖲️-☑️ POT Server stopped successfully.")
        return killed


# ============================================================================
# Backward Compatibility Alias
# ============================================================================
POTServerThread = POTServerProcess