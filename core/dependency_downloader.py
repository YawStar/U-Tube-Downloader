import sys
import os
import platform
import zipfile
import shutil
import time
import niquests as requests
from PySide6.QtCore import QSize, QThread, Signal, Slot, Qt, QStandardPaths, QCoreApplication, QTimer
from PySide6.QtGui import QFont, QIcon, QColor, QCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QTextEdit, QWidget, QLabel, QProgressBar, QHBoxLayout, QCheckBox,
                             QGraphicsDropShadowEffect, QFrame)

# CONSTANTS
import core.global_constants as CONST
QCoreApplication.setOrganizationName(CONST.COMPANY_NAME)
QCoreApplication.setApplicationName(CONST.APP_NAME)

# --- 🖥️ OS ကို စစ်ပြီး Binary Extension သတ်မှတ်ခြင်း ---
CURRENT_OS = platform.system()
BIN_EXT = ".exe" if CURRENT_OS == "Windows" else ""

# OS အလိုက် Downloads Path ကို ယူမယ်
downloads_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
download_path = os.path.normpath(os.path.join(downloads_dir, 'U-Tube Downloader'))
if not os.path.exists(download_path):
    os.makedirs(download_path)

# AppData Folder လမ်းကြောင်းများ
APP_DATA_DIR = os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
APP_CACHE_DIR = os.path.join(APP_DATA_DIR, "Cache")
TPT_DIR = os.path.join(APP_DATA_DIR, "Tools")

# Compiled UI ကို ဖတ်
from core.depD_ui import Ui_MainWindow


# ═══════════════════════════════════════════════════════════════════
# 🔄 DOWNLOAD WORKER THREAD
# ═══════════════════════════════════════════════════════════════════
class DownloadWorker(QThread):
    progress_signal = Signal(str, int)       # (target_name, percentage)
    status_signal = Signal(str, str)         # (target_name, status_text)
    finished_signal = Signal(str, bool)      # (target_name, is_successful)

    def __init__(self, target_dir, target_name, skip_existing=True):
        super().__init__()
        self.target_dir = target_dir
        self.target_name = target_name  
        self.skip_existing = skip_existing
        self.os_type = platform.system().lower()
        self._is_running = True
        self.is_successful = False
        self.current_file = None

        self.session = requests.Session()
        self.session.trust_env = True
        self._apply_system_proxy()

    def _apply_system_proxy(self):
        try:
            import urllib.request
            system_proxies = urllib.request.getproxies()
            if system_proxies:
                self.session.proxies.update(system_proxies)
        except Exception:
            pass

    def run(self):
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        self.is_successful = False 

        try:
            if self.target_name == "ytdlp":
                self.download_ytdlp()
            elif self.target_name == "ffmpeg":
                self.download_ffmpeg()
            elif self.target_name == "deno":
                self.download_deno()
            
            if self._is_running:
                self.is_successful = True
                
        except Exception as e:
            if not self._is_running:
                self.status_signal.emit(self.target_name, "Download is stopped.")
            else:
                self.status_signal.emit(self.target_name, f"Error: {str(e)}")
                self.progress_signal.emit(self.target_name, 0)
                self.is_successful = False
        
        if not self.is_successful:
            self.cleanup_partial_file()

        self.finished_signal.emit(self.target_name, self.is_successful)

    def stop(self):
        self._is_running = False
        self.cleanup_partial_file()

    def cleanup_partial_file(self):
        if self.current_file and not self.is_successful:
            path = os.path.join(self.target_dir, self.current_file)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def is_file_valid(self, filename):
        target_path = os.path.join(self.target_dir, filename)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return True
        return False

    def download_file(self, url, filename):
        if not self._is_running:
            return None

        self.current_file = filename  
        path = os.path.join(self.target_dir, filename)
        
        # အကယ်၍ skip_existing က False ဖြစ်နေပါက (Overwrite လုပ်ခိုင်းမယ်)
        if not self.skip_existing and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

        existing_file_size = 0
        if self.skip_existing and os.path.exists(path):
            existing_file_size = os.path.getsize(path)

        headers = {}
        if existing_file_size > 0 and self.skip_existing:
            headers['Range'] = f"bytes={existing_file_size}-"

        self.status_signal.emit(self.target_name, f"📥 Downloading: {filename}...")
        
        try:
            response = self.session.get(url, headers=headers, stream=True, timeout=10)
        except Exception as e:
            if not self._is_running:
                return None
            raise Exception(f"Network error: {str(e)}")
        
        status_code = getattr(response, 'status_code', 200)
        if status_code == 206:
            total_size = int(response.headers.get('content-length', 0)) + existing_file_size
            downloaded = existing_file_size
        else:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            existing_file_size = 0

        start_time = time.time()
        write_mode = 'ab' if (existing_file_size > 0 and self.skip_existing) else 'wb'
        
        try:
            with open(path, write_mode) as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if not self._is_running:
                        break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress_signal.emit(self.target_name, percent)
                            
                            elapsed_time = time.time() - start_time
                            actual_downloaded = downloaded - existing_file_size
                            speed = (actual_downloaded / elapsed_time / (1024 * 1024)) if elapsed_time > 0 else 0
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            
                            status_text = f"⚡ {speed:.2f} MB/s  |  📦 {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percent}%)"
                            self.status_signal.emit(self.target_name, status_text)
        except Exception as e:
            if not self._is_running:
                raise Exception("User stopped the download.")
            raise e
                        
        if not self._is_running:
            raise Exception("User stopped the download.")

        self.progress_signal.emit(self.target_name, 100)
        return path

    def get_latest_github_release(self, repo, asset_keyword, reject_keyword=None):
        if not self._is_running: return None
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = self.session.get(api_url, timeout=10)
        response.raise_for_status()
        assets = response.json().get('assets', [])
        for asset in assets:
            name = asset['name']
            if asset_keyword in name:
                if reject_keyword and reject_keyword in name:
                    continue
                return asset['browser_download_url'], name
        raise Exception(f"Not found binary: {asset_keyword}")

    def download_ytdlp(self):
        if not self._is_running: return
        if self.os_type == "windows":
            if self.skip_existing and self.is_file_valid("yt-dlp.exe"):
                return
            yt_url, yt_name = self.get_latest_github_release("yt-dlp/yt-dlp", "yt-dlp.exe")
            self.download_file(yt_url, "yt-dlp.exe")
        elif self.os_type == "linux":
            if self.skip_existing and self.is_file_valid("yt-dlp"):
                return
            yt_url, yt_name = self.get_latest_github_release("yt-dlp/yt-dlp", "yt-dlp", reject_keyword=".exe")
            yt_path = self.download_file(yt_url, "yt-dlp")
            if yt_path: os.chmod(yt_path, 0o755)
        elif self.os_type == "darwin":
            if self.skip_existing and self.is_file_valid("yt-dlp"):
                return
            yt_url, yt_name = self.get_latest_github_release("yt-dlp/yt-dlp", "yt-dlp_macos")
            yt_path = self.download_file(yt_url, "yt-dlp")
            if yt_path: os.chmod(yt_path, 0o755)

    def download_ffmpeg(self):
        if not self._is_running: return
        if self.os_type == "windows":
            has_ffmpeg = self.is_file_valid("ffmpeg.exe")
            has_ffprobe = self.is_file_valid("ffprobe.exe")
            if self.skip_existing and has_ffmpeg and has_ffprobe:
                return
            ff_api_url = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/tags/latest"
            ff_res = self.session.get(ff_api_url, timeout=10)
            ff_res.raise_for_status()
            assets = ff_res.json().get('assets', [])
            
            ff_url, ff_name = None, None
            for asset in assets:
                name = asset['name']
                if "ffmpeg-master-latest-win64-gpl-shared.zip" in name:
                    ff_url = asset['browser_download_url']
                    ff_name = name
                    break
            if not ff_url:
                raise Exception("FFmpeg zip file not found.")

            zip_path = self.download_file(ff_url, ff_name)
            if self._is_running and zip_path and os.path.exists(zip_path):
                self.current_file = None  
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        if "/bin/" in file_info.filename and not file_info.filename.endswith('/'):
                            if file_info.filename.endswith('ffplay.exe'):
                                continue
                            filename = os.path.basename(file_info.filename)
                            with zip_ref.open(file_info) as source, open(os.path.join(self.target_dir, filename), "wb") as target:
                                shutil.copyfileobj(source, target)
                os.remove(zip_path)
        else:
            has_ffmpeg = self.is_file_valid("ffmpeg")
            has_ffprobe = self.is_file_valid("ffprobe")
            if self.skip_existing and has_ffmpeg and has_ffprobe:
                return
            ff_url = "https://ffbinaries.com/api/v1/version/latest"
            ff_res = self.session.get(ff_url, timeout=10).json()
            mac_arch = "osx-64"
            arch_key = 'linux-64' if self.os_type == 'linux' else mac_arch
            
            ffmpeg_zip_url = ff_res['bin'][arch_key]['ffmpeg']
            ff_zip = self.download_file(ffmpeg_zip_url, "ffmpeg.zip")
            if ff_zip and os.path.exists(ff_zip):
                with zipfile.ZipFile(ff_zip, 'r') as zip_ref:
                    zip_ref.extractall(self.target_dir)
                os.remove(ff_zip)
            
            ffprobe_zip_url = ff_res['bin'][arch_key]['ffprobe']
            fp_zip = self.download_file(ffprobe_zip_url, "ffprobe.zip")
            if fp_zip and os.path.exists(fp_zip):
                with zipfile.ZipFile(fp_zip, 'r') as zip_ref:
                    zip_ref.extractall(self.target_dir)
                os.remove(fp_zip)
            
            if os.path.exists(os.path.join(self.target_dir, "ffmpeg")): os.chmod(os.path.join(self.target_dir, "ffmpeg"), 0o755)
            if os.path.exists(os.path.join(self.target_dir, "ffprobe")): os.chmod(os.path.join(self.target_dir, "ffprobe"), 0o755)

    def download_deno(self):
        if not self._is_running: return
        if self.os_type == "windows":
            if self.skip_existing and self.is_file_valid("deno.exe"):
                return
            deno_url, deno_name = self.get_latest_github_release("denoland/deno", "x86_64-pc-windows-msvc.zip")
            deno_zip = self.download_file(deno_url, deno_name)
            if self._is_running and deno_zip and os.path.exists(deno_zip):
                self.current_file = None
                with zipfile.ZipFile(deno_zip, 'r') as zip_ref:
                    zip_ref.extractall(self.target_dir)
                os.remove(deno_zip)
        else:
            if self.skip_existing and self.is_file_valid("deno"):
                return
            deno_target = "aarch64-apple-darwin.zip" if (self.os_type == "darwin" and platform.machine() == "arm64") else ("x86_64-apple-darwin.zip" if self.os_type == "darwin" else "x86_64-unknown-linux-gnu.zip")
            deno_url, deno_name = self.get_latest_github_release("denoland/deno", deno_target)
            deno_zip = self.download_file(deno_url, deno_name)
            if self._is_running and deno_zip and os.path.exists(deno_zip):
                self.current_file = None
                with zipfile.ZipFile(deno_zip, 'r') as zip_ref:
                    zip_ref.extractall(self.target_dir)
                os.remove(deno_zip)
                if os.path.exists(os.path.join(self.target_dir, "deno")): os.chmod(os.path.join(self.target_dir, "deno"), 0o755)


# ═══════════════════════════════════════════════════════════════════
# 🖥️ MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window Flags နှင့် Size သတ်မှတ်ခြင်း
        self.setWindowFlags(
            Qt.Window | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint | 
            Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("⬇️  Dependencies Downloader")
        self.setFixedSize(640, 560)
        
        self.setupUi(self)
        
        # သီးသန့် Worker Dictionary (Parallel Downloads အတွက်)
        self.workers = {
            "ytdlp": None,
            "ffmpeg": None,
            "deno": None
        }
        self.is_download_all_active = False
        self.queue_list = []

        # --- StyleSheet ထဲတွင် Disabled နှင့် Stop Download အတွက် Style များ ထည့်သွင်းခြင်း ---
        existing_style = self.styleSheet()
        extra_styles = """
            QPushButton:disabled {
                background-color: #151b28;
                border: 1px solid #1e293b;
                color: #475569;
            }
            QPushButton#btnFfmpegDownload:disabled, 
            QPushButton#btnDenoDownload:disabled, 
            QPushButton#btnYtDlpDownload:disabled, 
            QPushButton#downloadAllButton:disabled {
                background-color: #182030;
                border: 1px solid #222e45;
                color: #64748b;
            }
            QPushButton#downloadAllButton[is_stop="true"] {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c);
                border: 1px solid #ef4444;
            }
            QPushButton#downloadAllButton[is_stop="true"]:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #dc2626);
            }
        """
        self.setStyleSheet(existing_style + extra_styles)

        # --- Signals ချိတ်ဆက်ခြင်း ---
        self.btnYtDlpDownload.clicked.connect(lambda: self.start_single_download("ytdlp"))
        self.btnYtDlpCancel.clicked.connect(lambda: self.stop_single_download("ytdlp"))

        self.btnFfmpegDownload.clicked.connect(lambda: self.start_single_download("ffmpeg"))
        self.btnFfmpegCancel.clicked.connect(lambda: self.stop_single_download("ffmpeg"))

        self.btnDenoDownload.clicked.connect(lambda: self.start_single_download("deno"))
        self.btnDenoCancel.clicked.connect(lambda: self.stop_single_download("deno"))

        self.downloadAllButton.clicked.connect(self.toggle_download_all)

        # မိခင်ဝင်းဒိုး၏ အလယ်တည့်တည့်တွင် ပေါ်စေရန်
        if parent:
            self.center_on_parent(parent)

    def center_on_parent(self, parent):
        parent_geo = parent.geometry()
        x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
        self.move(x, y)

    def check_buttons_state(self):
        """Single သို့မဟုတ် All တစ်ခုခု အလုပ်လုပ်နေပါက ဆန့်ကျင်ဘက် ခလုတ်များကို Disable လုပ်ပေးခြင်း"""
        any_single_running = any(w and w.isRunning() for w in self.workers.values())
        
        if any_single_running:
            self.downloadAllButton.setEnabled(False)
        elif self.is_download_all_active:
            self.btnYtDlpDownload.setEnabled(False)
            self.btnFfmpegDownload.setEnabled(False)
            self.btnDenoDownload.setEnabled(False)
        else:
            self.downloadAllButton.setEnabled(True)
            self.btnYtDlpDownload.setEnabled(True)
            self.btnFfmpegDownload.setEnabled(True)
            self.btnDenoDownload.setEnabled(True)

    def start_single_download(self, target_name):
        if not os.path.exists(TPT_DIR):
            os.makedirs(TPT_DIR)

        if self.workers[target_name] and self.workers[target_name].isRunning():
            return

        if target_name == "ytdlp":
            self.stackedYtDlp.setCurrentIndex(1)
            self.labelYtDlpStatus.setText("Status: Downloading yt-dlp...")
        elif target_name == "ffmpeg":
            self.stackedFfmpeg.setCurrentIndex(1)
            self.labelFfmpegStatus.setText("Status: Downloading FFmpeg...")
        elif target_name == "deno":
            self.stackedDeno.setCurrentIndex(1)
            self.labelDenoStatus.setText("Status: Downloading Deno...")

        skip_existing = self.chk_skip_existing.isChecked()
        worker = DownloadWorker(TPT_DIR, target_name, skip_existing=skip_existing)
        worker.progress_signal.connect(self.update_progress)
        worker.status_signal.connect(self.update_status)
        worker.finished_signal.connect(self.download_finished)
        self.workers[target_name] = worker
        worker.start()

        self.check_buttons_state()

    def stop_single_download(self, target_name):
        worker = self.workers.get(target_name)
        if worker and worker.isRunning():
            worker.stop()
            worker.wait()

        if target_name == "ytdlp":
            self.stackedYtDlp.setCurrentIndex(0)
            self.labelYtDlpStatus.setText("Status: Ready to Download")
            self.progressBarYtDlp.setValue(0)
        elif target_name == "ffmpeg":
            self.stackedFfmpeg.setCurrentIndex(0)
            self.labelFfmpegStatus.setText("Status: Ready to Download")
            self.progressBarFfmpeg.setValue(0)
        elif target_name == "deno":
            self.stackedDeno.setCurrentIndex(0)
            self.labelDenoStatus.setText("Status: Ready to Download")
            self.progressBarDeno.setValue(0)

        self.check_buttons_state()

    def toggle_download_all(self):
        if self.is_download_all_active:
            self.stop_all_active_downloads()
        else:
            if not os.path.exists(TPT_DIR):
                os.makedirs(TPT_DIR)

            # Progressbar များကို ပြန်လျှော့
            self.progressBarYtDlp.setValue(0)
            self.progressBarFfmpeg.setValue(0)
            self.progressBarDeno.setValue(0)

            self.is_download_all_active = True
            self.queue_list = ["ytdlp", "ffmpeg", "deno"]
            self.check_buttons_state()
            
            self.downloadAllButton.setText("Stop Download")
            self.downloadAllButton.setProperty("is_stop", True)
            self.downloadAllButton.style().unpolish(self.downloadAllButton)
            self.downloadAllButton.style().polish(self.downloadAllButton)
            
            self.process_next_in_queue()

    def process_next_in_queue(self):
        if not self.queue_list or not self.is_download_all_active:
            self.stop_all_active_downloads()
            return

        next_target = self.queue_list.pop(0)

        if next_target == "ytdlp":
            self.stackedYtDlp.setCurrentIndex(1)
            self.labelYtDlpStatus.setText("Status: Downloading yt-dlp...")
        elif next_target == "ffmpeg":
            self.stackedFfmpeg.setCurrentIndex(1)
            self.labelFfmpegStatus.setText("Status: Downloading FFmpeg...")
        elif next_target == "deno":
            self.stackedDeno.setCurrentIndex(1)
            self.labelDenoStatus.setText("Status: Downloading Deno...")

        self.downloadAllButton.setText("Stop Download")
        self.downloadAllButton.setProperty("is_stop", True)
        self.downloadAllButton.style().unpolish(self.downloadAllButton)
        self.downloadAllButton.style().polish(self.downloadAllButton)
        
        skip_existing = self.chk_skip_existing.isChecked()
        worker = DownloadWorker(TPT_DIR, next_target, skip_existing=skip_existing)
        worker.progress_signal.connect(self.update_progress)
        worker.status_signal.connect(self.update_status)
        worker.finished_signal.connect(self.download_finished)
        self.workers[next_target] = worker
        worker.start()

    def stop_all_active_downloads(self):
        self.is_download_all_active = False
        self.queue_list = []

        for name, worker in self.workers.items():
            if worker and worker.isRunning():
                worker.stop()
                worker.wait()

        self.stackedYtDlp.setCurrentIndex(0)
        self.stackedFfmpeg.setCurrentIndex(0)
        self.stackedDeno.setCurrentIndex(0)

        self.labelYtDlpStatus.setText("Status: Ready to Download")
        self.labelFfmpegStatus.setText("Status: Ready to Download")
        self.labelDenoStatus.setText("Status: Ready to Download")

        # self.progressBarYtDlp.setValue(0)
        # self.progressBarFfmpeg.setValue(0)
        # self.progressBarDeno.setValue(0)

        self.downloadAllButton.setText("Download All")
        self.downloadAllButton.setProperty("is_stop", False)
        self.downloadAllButton.style().unpolish(self.downloadAllButton)
        self.downloadAllButton.style().polish(self.downloadAllButton)
        
        self.check_buttons_state()

    @Slot(str, int)
    def update_progress(self, target_name, value):
        if target_name == "ytdlp":
            self.progressBarYtDlp.setValue(value)
        elif target_name == "ffmpeg":
            self.progressBarFfmpeg.setValue(value)
        elif target_name == "deno":
            self.progressBarDeno.setValue(value)

    @Slot(str, str)
    def update_status(self, target_name, text):
        if target_name == "ytdlp":
            self.labelYtDlpStatus.setText(text)
        elif target_name == "ffmpeg":
            self.labelFfmpegStatus.setText(text)
        elif target_name == "deno":
            self.labelDenoStatus.setText(text)

    def start_close_countdown(self, seconds=5):
        self.remaining_seconds = seconds

        def update_countdown():
            if self.remaining_seconds > 0:
                # ✨ ခလုတ်ရဲ့ စာသားကို countdown ပုံစံ ပြောင်းလဲခြင်း
                self.downloadAllButton.setText(f"Will close in {self.remaining_seconds}...")
                self.remaining_seconds -= 1
            else:
                self.close_timer.stop()
                self.close()

        self.close_timer = QTimer(self)
        self.close_timer.timeout.connect(update_countdown)
        self.close_timer.start(1000)
        update_countdown()

    @Slot(str, bool)
    def download_finished_BAK(self, target_name, is_success):
        if target_name == "ytdlp":
            self.stackedYtDlp.setCurrentIndex(0)
            if is_success:
                self.labelYtDlpStatus.setText("Status: Downloaded")
                self.progressBarYtDlp.setValue(100)
            else:
                self.labelYtDlpStatus.setText("Status: Ready to Download")

        elif target_name == "ffmpeg":
            self.stackedFfmpeg.setCurrentIndex(0)
            if is_success:
                self.labelFfmpegStatus.setText("Status: Downloaded")
                self.progressBarFfmpeg.setValue(100)
            else:
                self.labelFfmpegStatus.setText("Status: Ready to Download")

        elif target_name == "deno":
            self.stackedDeno.setCurrentIndex(0)
            if is_success:
                self.labelDenoStatus.setText("Status: Downloaded")
                self.progressBarDeno.setValue(100)
            else:
                self.labelDenoStatus.setText("Status: Ready to Download")

        if self.is_download_all_active and is_success and self.queue_list:
            self.process_next_in_queue()
        else:
            if not self.is_download_all_active:
                self.check_buttons_state()
            else:
                self.stop_all_active_downloads()

    @Slot(str, bool)
    def download_finished(self, target_name, is_success):
        if target_name == "ytdlp":
            self.stackedYtDlp.setCurrentIndex(0)
            if is_success:
                self.labelYtDlpStatus.setText("Status: Downloaded")
                self.progressBarYtDlp.setValue(100)
            else:
                self.labelYtDlpStatus.setText("Status: Ready to Download")
                self.progressBarYtDlp.setValue(0)

        elif target_name == "ffmpeg":
            self.stackedFfmpeg.setCurrentIndex(0)
            if is_success:
                self.labelFfmpegStatus.setText("Status: Downloaded")
                self.progressBarFfmpeg.setValue(100)
            else:
                self.labelFfmpegStatus.setText("Status: Ready to Download")
                self.progressBarFfmpeg.setValue(0)

        elif target_name == "deno":
            self.stackedDeno.setCurrentIndex(0)
            if is_success:
                self.labelDenoStatus.setText("Status: Downloaded")
                self.progressBarDeno.setValue(100)
            else:
                self.labelDenoStatus.setText("Status: Ready to Download")
                self.progressBarDeno.setValue(0)

        # ✨ Download All (Queue) လုပ်နေစဉ် ဆက်လုပ်စရာ ကျန်သေးလား စစ်ဆေးခြင်း
        if self.is_download_all_active and is_success and self.queue_list:
            self.process_next_in_queue()
        else:
            if not self.is_download_all_active:
                self.check_buttons_state()
            else:
                # 🛑 Download All ပြီးဆုံးသွားပြီ (သို့မဟုတ် queue ပြီးသွားပြီ)
                self.is_download_all_active = False
                self.queue_list = []

                for name, worker in self.workers.items():
                    if worker and worker.isRunning():
                        worker.stop()
                        worker.wait()

                self.stackedYtDlp.setCurrentIndex(0)
                self.stackedFfmpeg.setCurrentIndex(0)
                self.stackedDeno.setCurrentIndex(0)

                # ✨ Download All အားလုံး ပြီးသွားပါက ခလုတ်ကို Disable လုပ်ပြီး Countdown စတင်မည်
                self.downloadAllButton.setEnabled(False)
                self.start_close_countdown(5)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())