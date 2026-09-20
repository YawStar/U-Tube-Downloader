import os
import platform
import zipfile
import shutil
import time
import niquests as requests
from PySide6.QtCore import QSize, QThread, Signal, Slot, Qt, QStandardPaths, QCoreApplication, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, 
                             QTextEdit, QWidget, QLabel, QProgressBar, QHBoxLayout)

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
# တကယ်လို့ အဲဒီ ဖိုဒါမရှိသေးရင် Create
if not os.path.exists(download_path):
    os.makedirs(download_path)

# OS အလိုက် စိတ်ချရတဲ့ AppData Folder လမ်းကြောင်းကို ယူမယ်
# ဥပမာ- Windows မှာ: AppData/Local/YourAppName
# ဥပမာ- Linux မှာ: .local/share/YourAppName
APP_DATA_DIR = os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
APP_CACHE_DIR = os.path.join(APP_DATA_DIR, "Cache")
TPT_DIR = os.path.join(APP_DATA_DIR, "Tools")

class DownloadWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)       # Percentage (0-100)
    status_signal = Signal(str)         # Speed & Size Text
    finished_signal = Signal()

    def __init__(self, target_dir):
        super().__init__()
        self.target_dir = target_dir
        self.os_type = platform.system().lower()
        self._is_running = True # Thread ရပ်/မရပ် ထိန်းချုပ်ရန် Flag
        self.is_successful = False  # ဒေါင်းလုဒ် အောင်မြင်မှု ရှိ/မရှိ စစ်မယ့် Flag

    def run(self):
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        self.log_signal.emit(f"🔄 Machine type: {platform.system()} ({platform.architecture()[0]}) \n")
        self.is_successful = False 

        try:
            if self.os_type == "windows":
                self.download_windows()
            elif self.os_type == "linux":
                self.download_linux()
            elif self.os_type == "darwin":
                self.download_mac()
            else:
                self.log_signal.emit(f"❌ Sorry... This program does ot support {platform.system()} OS.")
                
        except Exception as e:
            if not self._is_running:
                self.log_signal.emit("🛑 Download is cancalled by user!")
                self.status_signal.emit("Download is stopped.")
            else:
                self.log_signal.emit(f"❌ Error occured: {str(e)}")
                self.progress_signal.emit(0)
                self.status_signal.emit("An unexpected error occured!")
                self.is_successful = False # Error တက်ရင် လုံးဝ False စစ်စစ် ဖြစ်စေရမယ်
        
        self.finished_signal.emit()

    def stop(self):
        """ အပြင်ကနေ ဒေါင်းလုဒ်ကို လှမ်းရပ်နိုင်ရန် function """
        self._is_running = False

    def download_file(self, url, filename):
        """ Resume (လုပ်လက်စကဆက်ဒေါင်းခြင်း) စနစ်ပါဝင်သော ဒေါင်းလုဒ် helper function """
        if not self._is_running:
            return None

        path = os.path.join(self.target_dir, filename)
        
        # စက်ထဲမှာ ဒေါင်းလက်စ ဖိုင်ရှိမရှိ စစ်ဆေးခြင်း
        existing_file_size = 0
        if os.path.exists(path):
            existing_file_size = os.path.getsize(path)

        headers = {}
        # ရှိပြီးသားဖိုင်ဆိုဒ် ရှိနေရင် Range Header ထည့်မည်
        if existing_file_size > 0:
            headers['Range'] = f"bytes={existing_file_size}-"
            self.log_signal.emit(f"⚙️ ဒေါင်းလက်စဖိုင် တွေ့ရှိသဖြင့် {existing_file_size / (1024*1024):.2f} MB မှ ဆက်လက်ဒေါင်းလုဒ်လုပ်နေသည်...")

        self.log_signal.emit(f"📥 Downloading: {filename}...")
        self.status_signal.emit(f"📥 Downloading: {filename}...")
        
        # Stream ကို Header ပါဝင်ပြီး ခေါ်ယူခြင်း
        response = requests.get(url, headers=headers, stream=True)
        
        # 206 Partial Content ဆိုရင် အောင်မြင်စွာ ဆက်ဒေါင်းနိုင်ခြင်းဖြစ်ပြီး 200 ဆိုရင် ဆာဗာက resume မပေးလို့ အစကပြန်ဒေါင်းမယ်
        if response.status_color_code if hasattr(response, 'status_color_code') else response.status_code == 206:
            total_size = int(response.headers.get('content-length', 0)) + existing_file_size
            downloaded = existing_file_size
        else:
            # အစကနေ ပြန်ဒေါင်းရမည့် အခြေအနေ (Range ကို ဆာဗာက ငြင်းပယ်ရင်)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            existing_file_size = 0

        start_time = time.time()
        # 'ab' (Append Binary) မုဒ်ဖြင့် ဖွင့်ခြင်းကြောင့် ဖိုင်အဟောင်းနောက်ကနေ ဆက်ရေးသွားမယ်
        write_mode = 'ab' if existing_file_size > 0 else 'wb'
        
        with open(path, write_mode) as f:
            for chunk in response.iter_content(chunk_size=65536): # 64KB chunks
                # အသုံးပြုသူက Stop နှိပ်လိုက်ရင် Loop ထဲက ထွက်
                if not self._is_running:
                    break
                
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        self.progress_signal.emit(percent)
                        
                        elapsed_time = time.time() - start_time
                        # ဒေါင်းလုဒ်ဆွဲသည့် အမြန်နှုန်း အမှန်ရရန် လက်ရှိဆွဲမိသော ပမာဏဖြင့်သာ တွက်ချက်
                        actual_downloaded = downloaded - existing_file_size
                        if elapsed_time > 0:
                            speed = actual_downloaded / elapsed_time / (1024 * 1024)
                        else:
                            speed = 0
                            
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        
                        status_text = f"⚡ {speed:.2f} MB/s  |  📦 {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percent}%)"
                        self.status_signal.emit(status_text)
                        
        # အကယ်၍ Stop နှိပ်ခံရလို့ ထွက်လာတာဆိုရင် Exception တွန်းထုတ်ပြီး ရပ်ပစ်မယ်
        if not self._is_running:
            raise Exception("User stopped the download.")

        self.log_signal.emit(f"✅ Download finished: {filename}")
        self.progress_signal.emit(100)
        self.status_signal.emit(f"✅ Finished: {filename}")
        return path

    def get_latest_github_release(self, repo, asset_keyword, reject_keyword=None):
        if not self._is_running: return None
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = requests.get(api_url)
        response.raise_for_status()
        assets = response.json().get('assets', [])
        for asset in assets:
            name = asset['name']
            if asset_keyword in name:
                if reject_keyword and reject_keyword in name:
                    continue
                return asset['browser_download_url'], name
        raise Exception(f"Not found!: 'No binary found {asset_keyword}' in {repo}")

    def download_windows(self):
        os.path.defpath
        # 1. yt-dlp.exe
        if not self._is_running: return
        yt_url, yt_name = self.get_latest_github_release("yt-dlp/yt-dlp", "yt-dlp.exe")
        self.download_file(yt_url, "yt-dlp.exe")
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')

        # 2. ffmpeg & ffprobe 
        if not self._is_running: return
        ff_api_url = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/tags/latest"
        ff_res = requests.get(ff_api_url)
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
            raise Exception("BtbN Repository တွင် win64-gpl-shared zip ဖိုင် ရှာမတွေ့ပါ။")

        zip_path = self.download_file(ff_url, ff_name)
        
        # ဒေါင်းလုဒ် အောင်မြင်စွာ ပြီးဆုံးမှသာ Extraction လုပ်မယ်
        if self._is_running and zip_path and os.path.exists(zip_path):
            self.log_signal.emit("📦 Extracting necessory files...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if "/bin/" in file_info.filename and not file_info.filename.endswith('/'):
                        if file_info.filename.endswith('ffplay.exe'):
                            continue
                        filename = os.path.basename(file_info.filename)
                        with zip_ref.open(file_info) as source, open(os.path.join(self.target_dir, filename), "wb") as target:
                            shutil.copyfileobj(source, target)
            os.remove(zip_path)
            self.log_signal.emit("✅ BtbN FFmpeg Shared Binaries (.exe + .dll) Extraction finished...")
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')

        # 3. deno.exe
        if not self._is_running: return
        deno_url, deno_name = self.get_latest_github_release("denoland/deno", "x86_64-pc-windows-msvc.zip")
        deno_zip = self.download_file(deno_url, deno_name)
        if self._is_running and deno_zip and os.path.exists(deno_zip):
            self.log_signal.emit("📦 Extracting Deno Binary files...")
            with zipfile.ZipFile(deno_zip, 'r') as zip_ref:
                zip_ref.extractall(self.target_dir)
            os.remove(deno_zip)
            self.log_signal.emit("✅ Deno Windows binary Extraction finished...")
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')
        if self._is_running:
            self.is_successful = True

    def download_linux(self):
        # 1. yt-dlp 
        if not self._is_running: return
        yt_url, yt_name = self.get_latest_github_release("yt-dlp/yt-dlp", "yt-dlp", reject_keyword=".exe")
        yt_path = self.download_file(yt_url, "yt-dlp")
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')
        if self._is_running and yt_path:
            os.chmod(yt_path, 0o755)

        # 2. ffmpeg & ffprobe
        if not self._is_running: return
        ff_url = "https://ffbinaries.com/api/v1/version/latest"
        ff_res = requests.get(ff_url).json()
        
        # ffmpeg
        ffmpeg_zip_url = ff_res['bin']['linux-64']['ffmpeg']
        ff_zip = self.download_file(ffmpeg_zip_url, "ffmpeg-linux.zip")
        if self._is_running and ff_zip and os.path.exists(ff_zip):
            with zipfile.ZipFile(ff_zip, 'r') as zip_ref:
                zip_ref.extractall(self.target_dir)
            os.remove(ff_zip)

        # ffprobe
        if not self._is_running: return
        ffprobe_zip_url = ff_res['bin']['linux-64']['ffprobe']
        fp_zip = self.download_file(ffprobe_zip_url, "ffprobe-linux.zip")
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')
        if self._is_running and fp_zip and os.path.exists(fp_zip):
            with zipfile.ZipFile(fp_zip, 'r') as zip_ref:
                zip_ref.extractall(self.target_dir)
            os.remove(fp_zip)

        if self._is_running:
            if os.path.exists(os.path.join(self.target_dir, "ffmpeg")): os.chmod(os.path.join(self.target_dir, "ffmpeg"), 0o755)
            if os.path.exists(os.path.join(self.target_dir, "ffprobe")): os.chmod(os.path.join(self.target_dir, "ffprobe"), 0o755)

        # 3. deno
        if not self._is_running: return
        deno_url, deno_name = self.get_latest_github_release("denoland/deno", "x86_64-unknown-linux-gnu.zip")
        deno_zip = self.download_file(deno_url, deno_name)
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')
        if self._is_running and deno_zip and os.path.exists(deno_zip):
            with zipfile.ZipFile(deno_zip, 'r') as zip_ref:
                zip_ref.extractall(self.target_dir)
            os.remove(deno_zip)
            if os.path.exists(os.path.join(self.target_dir, "deno")): os.chmod(os.path.join(self.target_dir, "deno"), 0o755)
            self.log_signal.emit("✅ Deno Linux binary extraction ပြီးဆုံးပါပြီ။\n")
            self.is_successful = True

    def download_mac(self):
        # 1. yt-dlp (macOS)
        if not self._is_running: return
        yt_url, yt_name = self.get_latest_github_release("yt-dlp/yt-dlp", "yt-dlp_macos")
        yt_path = self.download_file(yt_url, "yt-dlp")
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')
        if self._is_running and yt_path:
            os.chmod(yt_path, 0o755)

        # 2. ffmpeg & ffprobe (macOS)
        if not self._is_running: return
        ff_url = "https://ffbinaries.com/api/v1/version/latest"
        ff_res = requests.get(ff_url).json()
        
        # macOS Architecture စစ်ဆေးခြင်း (Intel သို့မဟုတ် Apple Silicon/arm64)
        mac_arch = "osx-64"
        if platform.machine() == "arm64":
            mac_arch = "osx-64" # ffbinaries အနေဖြင့် universal/osx-64 ဖြင့် Support ပေး

        # ffmpeg
        ffmpeg_zip_url = ff_res['bin'][mac_arch]['ffmpeg']
        ff_zip = self.download_file(ffmpeg_zip_url, "ffmpeg-mac.zip")
        if self._is_running and ff_zip and os.path.exists(ff_zip):
            with zipfile.ZipFile(ff_zip, 'r') as zip_ref:
                zip_ref.extractall(self.target_dir)
            os.remove(ff_zip)

        # ffprobe
        if not self._is_running: return
        ffprobe_zip_url = ff_res['bin'][mac_arch]['ffprobe']
        fp_zip = self.download_file(ffprobe_zip_url, "ffprobe-mac.zip")
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')
        if self._is_running and fp_zip and os.path.exists(fp_zip):
            with zipfile.ZipFile(fp_zip, 'r') as zip_ref:
                zip_ref.extractall(self.target_dir)
            os.remove(fp_zip)

        if self._is_running:
            if os.path.exists(os.path.join(self.target_dir, "ffmpeg")): os.chmod(os.path.join(self.target_dir, "ffmpeg"), 0o755)
            if os.path.exists(os.path.join(self.target_dir, "ffprobe")): os.chmod(os.path.join(self.target_dir, "ffprobe"), 0o755)

        # 3. deno (macOS)
        if not self._is_running: return
        deno_target = "aarch64-apple-darwin.zip" if platform.machine() == "arm64" else "x86_64-apple-darwin.zip"
        deno_url, deno_name = self.get_latest_github_release("denoland/deno", deno_target)
        deno_zip = self.download_file(deno_url, deno_name)
        self.log_signal.emit('------------------------------------------------------------------------------------------\n')
        if self._is_running and deno_zip and os.path.exists(deno_zip):
            with zipfile.ZipFile(deno_zip, 'r') as zip_ref:
                zip_ref.extractall(self.target_dir)
            os.remove(deno_zip)
            if os.path.exists(os.path.join(self.target_dir, "deno")): os.chmod(os.path.join(self.target_dir, "deno"), 0o755)
            self.log_signal.emit("✅ Deno macOS binary extraction ပြီးဆုံးပါပြီ။\n")
            self.is_successful = True
            
class MainWindow(QMainWindow):
    # main25 ဆီ ရလဒ် (True/False) လှမ်းပို့ပေးမယ့် Signal အသစ်တစ်ခု Declare လုပ်
    download_status_signal = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Close Button (X) တစ်ခုတည်း ပါဝင်အောင် ပြုလုပ်
        self.setWindowFlags(
            Qt.Window | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint | 
            Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("Dependencies Downloader")
        self.setFixedSize(600, 480)

        # Global Fonts Settings
        self.main_font = QFont("Pyidaungsu", 11)
        self.log_font = QFont("Pyidaungsu", 10)
        self.status_font = QFont("Pyidaungsu", 10, QFont.Bold)

        # UI Elements
        # self.label = QLabel("yt-dlp, FFmpeg နှင့် Deno တို့ကို တစ်ဆင့်ချင်းစီ Download လုပ်သွားပါမည်။")
        self.label = QLabel("Click Start Download button to download dependencies..")
        self.label.setFont(self.main_font)
        
        # ခလုတ်နှစ်ခုကို အလျားလိုက်ထားရန် Layout ဆောက်
        self.btn_layout = QHBoxLayout()
        
        self.btn_download = QPushButton("Start Download")
        self.btn_download.setFont(QFont("Pyidaungsu", 10))
        self.btn_download.setFixedHeight(40)
        
        self.btn_stop = QPushButton("Stop Download")
        self.btn_stop.setFont(QFont("Pyidaungsu", 10))
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.setEnabled(False) # Download မစခင် Disable ထား
        
        self.btn_layout.addWidget(self.btn_download)
        self.btn_layout.addWidget(self.btn_stop)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(self.log_font)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        self.lbl_status = QLabel("Ready to download Dependencies...")
        self.lbl_status.setFont(self.status_font)
        self.lbl_status.setStyleSheet("color: #2980b9;")

        # Main Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(self.btn_layout) # Button Layout ထည့်ခြင်း
        layout.addWidget(self.log_view)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.lbl_status)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.btn_download.clicked.connect(self.start_download)
        self.btn_stop.clicked.connect(self.stop_download)
        
        self.worker = None

    # Window ကို X နှိပ်ပြီး ပိတ်လိုက်သည့်အခါ စစ်ဆေးမယ့် Event
    def closeEvent(self, event):
        # btn_download က Disable ဖြစ်နေလျှင် (Download ဆွဲနေဆဲ ဖြစ်လျှင်) Window မပိတ်အောင် တားဆီး
        if not self.btn_download.isEnabled():
            self.log_view.append("\n⚠️ Downloading in progress. Please stop the download before closing.")
            event.ignore()  # 🛑 Window ပိတ်မည့် Event ကို ငြင်းပယ်လိုက်သည်
            return

        # Download မဆွဲနေပါက Thread ရှိနေလျှင် ပုံမှန်အတိုင်း ရပ်ပြီးမှ ပိတ်မယ်
        if self.worker and self.worker.isRunning():
            self.log_view.append("\n⚠️ Aborting download...")
            
            try:
                self.worker.log_signal.disconnect(self.update_log)
            except RuntimeError:
                pass
                
            self.worker.stop()
            self.worker.wait() 
            
        event.accept()  # ✅ Window ကိုပိတ်ခွင့်ပြု

    def delete_folder(folder_path, keep_folder=False):
        """
        folder ကိုဖျက်တယ်
        
        Args:
            folder_path: ဖျက်ချင်တဲ့ folder path
            keep_folder: True ဆိုရင် folder ကိုထားပြီး အတွင်းက file တွေပဲဖျက်မယ်
        """
        try:
            if not os.path.exists(folder_path):
                print(f"⚠️ Folder မရှိပါ: {folder_path}")
                return
                
            if keep_folder:
                # folder ထဲက file တွေပဲဖျက်မယ်
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
            else:
                # folder နဲ့ အတွင်းပါအကုန်ဖျက်မယ်
                shutil.rmtree(folder_path)
                
        except PermissionError:
            print(f"❌ Permission denied: {folder_path} (Maybe some file was using.)")
        except FileNotFoundError:
            print(f"❌ Folder not found!: {folder_path}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def start_download(self):
        self.btn_download.setEnabled(False)
        self.btn_stop.setEnabled(True)
        # shutil.rmtree(TPT_DIR)
        if not os.path.exists(TPT_DIR): os.mkdir(TPT_DIR)
        for item in os.listdir(TPT_DIR):
            item_path = os.path.join(TPT_DIR, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        # --- ဒေါင်းလုဒ်အသစ်စတိုင်း UI အဟောင်းများကို အကုန်အစင် ရှင်းလင်း ---
        self.log_view.clear()            # Log ပြကွက်ထဲက စာဟောင်းများအားလုံးကို ဖျက်
        self.log_view.append("▶️ Starting download process...")
        self.update_status("▶️ Starting download process...")
        self.progress_bar.setValue(0)    # Progress Bar ကို 0% ပြန်လုပ်
        # ------------------------------------------------------------------
        
        target_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), TPT_DIR)
        
        self.worker = DownloadWorker(target_directory)
        
        self.worker.log_signal.connect(self.update_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.download_finished)
        
        self.worker.start()

    def stop_download(self):
        if self.worker and self.worker.isRunning():
            self.log_view.append("\n🛑 Trying to stop download... Please wait...")
            self.update_status("🛑 Trying to stop download... Please wait...")

            # log_signal ချိတ်ဆက်မှုကို လုံးဝ ဖြုတ်
            try:
                self.worker.log_signal.disconnect(self.update_log)
            except RuntimeError:
                print("Error: Stopping Download") #pass # ချိတ်ဆက်မှု မရှိထားရင် error မတက်အောင်

            self.worker.stop()
            # self.log_view.append("🛑 Download was stopped...")
            # self.update_status("🛑 Trying to stop download...")
            self.btn_stop.setEnabled(False)

    @Slot(str)
    def update_log(self, text):
        self.log_view.append(text)

    @Slot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @Slot(str)
    def update_status(self, text):
        self.lbl_status.setText(text)

    def start_close_countdown(self, seconds=5):
        """ စက္ကန့်အလိုက် Countdown ပြပြီးမှ Window ပိတ်ပေးမည့် helper function """
        self.remaining_seconds = seconds

        def update_countdown():
            if self.remaining_seconds > 0:
                self.lbl_status.setText(
                    f"🎉 Completed: All necessory dependencies were downloaded successfully.\n"
                    f"(Windows will closed in {self.remaining_seconds} sec.)"
                )
                self.remaining_seconds -= 1
            else:
                self.close_timer.stop()
                self.close()

        self.close_timer = QTimer(self)
        self.close_timer.timeout.connect(update_countdown)
        self.close_timer.start(1000)
        update_countdown()

    @Slot()
    def download_finished(self):
        self.btn_download.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        # ပုံမှန်ပြီးဆုံးခြင်း ဟုတ်မဟုတ် စစ်ဆေးသည်
        if self.worker and self.worker.is_successful:
            self.log_view.append("🎉 All necessory dependencies were downloaded successfully.")
            self.progress_bar.setValue(100)
            
            # တကယ် အောင်မြင်ခဲ့ရင် True လှမ်းပို့မယ်
            self.download_status_signal.emit(True)
            
            # ၅, ၄, ၃, ၂, ၁ စက္ကန့် Countdown ပြပြီးမှ Window ကို အလိုအလျောက် ပိတ်
            self.start_close_countdown(5)
        else:
            if self.worker and not self.worker._is_running:
                self.lbl_status.setText("🛑 Download stopped.")
                self.log_view.append("🛑 Download was stopped...")
            else:
                self.lbl_status.setText("❌ Download unsuccessful. Try again...")
            
            # မအောင်မြင်ရင် သို့မဟုတ် အသုံးပြုသူက ရပ်လိုက်ရင် False လှမ်းပို့မယ်
            self.download_status_signal.emit(False)