# -*- coding: utf-8 -*-
import os
import zipfile
import platform
import psutil
import time
import requests
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QButtonGroup, QApplication, QProgressBar
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QCoreApplication, QFile, QStandardPaths, QThread, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QDesktopServices
import urllib.request
import json

# CONSTANTS
import core.global_constants as CONST

# ============================================================================
# Setup: QCoreApplication metadata
# ============================================================================
QCoreApplication.setOrganizationName(CONST.COMPANY_NAME)
QCoreApplication.setApplicationName(CONST.APP_NAME)

# OS
CURRENT_OS = platform.system()
IS_WINDOWS = CURRENT_OS == "Windows"
IS_LINUX = CURRENT_OS == "Linux"
IS_MACOS = CURRENT_OS == "Darwin"
BIN_EXT = ".exe" if IS_WINDOWS else ""
SVR_EXE_NAME = f"yawstar-pot-server{BIN_EXT}" if IS_WINDOWS else "yawstar-pot-server"

# ============================================================================
# AppData Paths
# ============================================================================
APP_DATA_DIR = os.path.normpath(
    QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
)
if not os.path.exists(APP_DATA_DIR):
    os.makedirs(APP_DATA_DIR)

APP_CACHE_DIR = os.path.join(APP_DATA_DIR, "Cache")
if not os.path.exists(APP_CACHE_DIR):
    os.makedirs(APP_CACHE_DIR)

TPT_DIR = os.path.join(APP_DATA_DIR, "Tools")
if not os.path.exists(TPT_DIR):
    os.makedirs(TPT_DIR)

# Modern Update Dialog
from ui.update_dialog import ModernUpdateDialog

# Logger
from utils.logger import setup_logging, get_logger

# Module logger
logger = get_logger(__name__)

# POT Server Services
from utils.pot_server import POTServerThread

# ============================================================================
# GitHub Release Fetcher Thread (POT Server & Plugin အတွက် နောက်ဆုံး Version ရှာရန်)
# ============================================================================
class GitHubReleaseFetcherThread(QThread):
  release_fetched = Signal(str, str, str)  # latest_version, server_download_url, plugin_download_url
  fetch_failed = Signal(str)

  def __init__(self, owner: str, repo: str, parent=None):
    super().__init__(parent)
    self.api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

  def run(self):
    try:
      req = urllib.request.Request(
          self.api_url,
          headers={
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
              'Accept': 'application/vnd.github.v3+json',
          },
      )
      with urllib.request.urlopen(req, timeout=10) as response:
        if response.status == 200:
          data = json.loads(response.read().decode('utf-8'))
          latest_version = data.get("tag_name", "v0.1.0")

          server_url = ""
          plugin_url = ""

          assets = data.get("assets", [])
          for asset in assets:
            asset_name = asset.get("name", "").lower()
            download_url = asset.get("browser_download_url", "")

            # OS အလိုက် POT Server binary ကို ရှာခြင်း
            if IS_WINDOWS and "windows-amd64.exe" in asset_name:
              server_url = download_url
            elif IS_LINUX and "linux-amd64" in asset_name:
              server_url = download_url
            elif IS_MACOS and "darwin-amd64" in asset_name:
              server_url = download_url

            # Plugin zip ဖိုင်ကို ရှာခြင်း
            if "yawstar-ytdlp-pot-provider.zip" in asset_name:
              plugin_url = download_url

          # Assets ထဲမှာ မတွေ့ရင် fallback URL သုံးရန်
          if not server_url:
            if IS_WINDOWS:
              server_url = f"https://github.com/YawStar/ytdlp-pot-provider/releases/download/{latest_version}/yawstar-pot-server-windows-amd64.exe"
            elif IS_LINUX:
              server_url = f"https://github.com/YawStar/ytdlp-pot-provider/releases/download/{latest_version}/yawstar-pot-server-linux-amd64"
            elif IS_MACOS:
              server_url = f"https://github.com/YawStar/ytdlp-pot-provider/releases/download/{latest_version}/yawstar-pot-server-darwin-amd64"

          if not plugin_url:
            plugin_url = f"https://github.com/YawStar/ytdlp-pot-provider/releases/download/{latest_version}/yawstar-ytdlp-pot-provider.zip"

          self.release_fetched.emit(latest_version, server_url, plugin_url)
        else:
          self.fetch_failed.emit(f"GitHub API Error: HTTP {response.status}")
    except Exception as e:
      self.fetch_failed.emit(str(e))

# ============================================================================
# Stop Server Worker
# ============================================================================
class StopServerWorker(QThread):
    """
    POT Server ကို background မှာ ရပ်တန့်ပေးသည့် Worker Thread။
    
    ⚠️ အရေးကြီး — `_stop_requested` flag ကို အရင် သတ်ပြီးမှ process ကို kill
    လုပ်ရမယ်။ မဟုတ်ရင် `_on_process_finished()` က "Server Crashed" လို့
    မှားယွင်း သတ်မှတ်နိုင်တယ်။
    """
    finished = Signal(bool, str)

    def __init__(self, pot_mgr, parent=None):
        super().__init__(parent)
        self.pot_mgr = pot_mgr

    def run(self):
        try:
            # ⬇️ [KEY] Stop flag ကို အရင် သတ် — crash လို့ မမှားစေရန်
            self.pot_mgr._stop_requested = True
            self.pot_mgr._running = False

            # ၁။ /shutdown endpoint (graceful)
            try:
                requests.post(f"{self.pot_mgr.server_url}/shutdown", timeout=1)
                logger.info("🖲️-☑️ Shutdown endpoint called (background).")
            except Exception:
                pass

            # ၂။ Process kill / port clear
            POTServerThread.kill_process_on_port(4416)

            # ၃။ ရပ်သွား/မသွား အတည်ပြု
            time.sleep(0.3)
            if not self.pot_mgr.is_server_running():
                self.finished.emit(True, "Server stopped successfully.")
            else:
                self.finished.emit(False, "Failed to stop server port 4416.")

        except Exception as e:
            logger.error(f"StopServerWorker error: {e}")
            self.finished.emit(False, f"Error stopping server: {e}")


# ============================================================================
# Direct Update Checker Thread
# ============================================================================
class DirectUpdateCheckerThread(QThread):
    update_checked = Signal(bool, str, str, str)
    check_failed = Signal(str)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version.lstrip('v')
        self.api_url = "https://api.github.com/repos/YawStar/U-Tube-Downloader/releases/latest"

    def run(self):
        try:
            req = urllib.request.Request(
                self.api_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_version = data.get("tag_name", "0.0.0").lstrip('v')
                    release_notes = data.get("body", "No release notes available.")
                    html_url = data.get("html_url", "https://github.com/YawStar/U-Tube-Downloader/releases")

                    download_url = html_url
                    assets = data.get("assets", [])
                    for asset in assets:
                        asset_name = asset.get("name", "").lower()
                        if asset_name.endswith(".exe"):
                            download_url = asset.get("browser_download_url", html_url)
                            break

                    is_available = self._is_newer(self.current_version, latest_version)
                    self.update_checked.emit(is_available, latest_version, release_notes, download_url)
                else:
                    self.check_failed.emit(f"GitHub API Error: HTTP {response.status}")
        except Exception as e:
            self.check_failed.emit(str(e))

    def _is_newer(self, current: str, latest: str) -> bool:
        try:
            c = [int(x) for x in current.split('.')]
            l = [int(x) for x in latest.split('.')]
            return l > c
        except ValueError:
            return latest > current


# ============================================================================
# File Downloader Thread
# ============================================================================
class FileDownloaderThread(QThread):
    progress_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, url: str, save_path: str, extract_to: str = None, is_zip: bool = False, parent=None):
        super().__init__(parent)
        self.url = url
        self.save_path = save_path
        self.extract_to = extract_to
        self.is_zip = is_zip

    def run(self):
        try:
            self.progress_signal.emit("Downloading file...")
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)

            req = urllib.request.Request(
                self.url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )

            with urllib.request.urlopen(req, timeout=30) as response, open(self.save_path, 'wb') as out_file:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                block_size = 1024 * 64

                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    out_file.write(buffer)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        self.progress_signal.emit(f"Downloading... {percent}%")

            # if self.is_zip and self.extract_to:
            #     self.progress_signal.emit("Extracting server files...")
            #     os.makedirs(self.extract_to, exist_ok=True)

            #     with zipfile.ZipFile(self.save_path, 'r') as zip_ref:
            #         all_members = zip_ref.namelist()

            #         server_prefix = None
            #         for member in all_members:
            #             if member.endswith('/server/') or member.endswith('/server'):
            #                 server_prefix = member if member.endswith('/') else member + '/'
            #                 break

            #         if server_prefix:
            #             for member in zip_ref.infolist():
            #                 if member.filename.startswith(server_prefix) and member.filename != server_prefix:
            #                     rel_path = member.filename[len(server_prefix):]
            #                     if not rel_path:
            #                         continue

            #                     target_path = os.path.join(self.extract_to, rel_path)

            #                     if member.is_dir():
            #                         os.makedirs(target_path, exist_ok=True)
            #                     else:
            #                         if not os.path.exists(target_path):
            #                             os.makedirs(os.path.dirname(target_path), exist_ok=True)
            #                             with zip_ref.open(member) as source, open(target_path, "wb") as target:
            #                                 target.write(source.read())
            #                         else:
            #                             logger.info(f"Skipped existing file: {target_path}")
            #         else:
            #             raise Exception("Could not find 'server' directory in the downloaded zip package.")

            #     if os.path.exists(self.save_path):
            #         os.remove(self.save_path)

            self.finished_signal.emit(True, "Download completed successfully.")

        except Exception as e:
            self.finished_signal.emit(False, f"Download failed: {str(e)}")


# ============================================================================
# Settings Dialog
# ============================================================================
class SettingsDialog(QDialog):
    """ ConfigManager ကို အသုံးပြု၍ App ဆက်တင်များအားလုံးကို RAM ပေါ်မှတစ်ဆင့် 
    မြန်ဆန်ချောမွေ့စွာ ဖတ်ခြင်း၊ ရေးခြင်း၊ Default ချခြင်းများ ပြုလုပ်ပေးမည့် Dialog Class """

    def __init__(self, config_mgr, parent=None, initial_tab=None, pot_mgr=None):
        super().__init__(parent)
        self.config_mgr = config_mgr

        # Server လုပ်ဆောင်ချက်များ လုပ်နေချိန် Window မပိတ်နိုင်စေရန် Flag
        self.is_busy = False
        self._force_close_allowed = False
        self._stop_worker: StopServerWorker | None = None

        # App Data Dir ကို သတ်မှတ်
        APP_DATA_DIR = os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        APP_CACHE_DIR = os.path.join(APP_DATA_DIR, "Cache")
        self.manual_cookies_path = os.path.join(APP_CACHE_DIR, "manual_cookies.txt")

        # POT Manager — MainWindow က ပေးရင် သုံး၊ မပေးရင် အသစ်ဆောက်
        if pot_mgr is not None:
            self.pot_mgr = pot_mgr
            # logger.info("SettingsDialog: Using provided POT manager")
        else:
            self.pot_mgr = POTServerThread(tools_dir=TPT_DIR)
            # logger.info("SettingsDialog: Created new POT manager")

        # Dynamic UI Loading
        loader = QUiLoader()
        ui_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings_dialog.ui")
        ui_file = QFile(ui_file_path)

        if not ui_file.open(QFile.ReadOnly):
            self.show_custom_message("critical", "Error", f"Cannot open {ui_file_path}")
            return

        self.ui = loader.load(ui_file, self)
        ui_file.close()

        # Tab Index
        if initial_tab is None:
            initial_tab = self.config_mgr.get("last_settings_tab", 0)

        tab_widget = getattr(self, 'tabWidget', None) or getattr(self.ui, 'tabWidget', None)
        if tab_widget:
            if isinstance(initial_tab, int):
                tab_widget.setCurrentIndex(initial_tab)
            elif isinstance(initial_tab, str):
                for i in range(tab_widget.count()):
                    if tab_widget.tabText(i).lower() == initial_tab.lower():
                        tab_widget.setCurrentIndex(i)
                        break

        self.setWindowTitle("Settings")
        self.setFixedSize(680, 590)

        if self.ui.layout():
            self.setLayout(self.ui.layout())

        # Object Name သတ်မှတ်ခြင်း
        if hasattr(self.ui, 'btn_save'):
            self.ui.btn_save.setObjectName("btn_pref_action")
        if hasattr(self.ui, 'btn_cancel'):
            self.ui.btn_cancel.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_restore'):
            self.ui.btn_restore.setObjectName("btn_pref_def_restore")

        if hasattr(self.ui, 'btn_check_update'):
            self.ui.btn_check_update.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_get_cookie_ext'):
            self.ui.btn_get_cookie_ext.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_clear_cookies'):
            self.ui.btn_clear_cookies.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_reset_output_template'):
            self.ui.btn_reset_output_template.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_reset_playlist_indexing'):
            self.ui.btn_reset_playlist_indexing.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_BrowsePath'):
            self.ui.btn_BrowsePath.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_browse_cookies'):
            self.ui.btn_browse_cookies.setObjectName("btn_pref_browse")
        if hasattr(self.ui, 'btn_paste_clipboard'):
            self.ui.btn_paste_clipboard.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_save_manual'):
            self.ui.btn_save_manual.setObjectName("btn_pref_secondary")

        self.ui.btn_toggle_pot_server.setObjectName("btn_pref_secondary")
        self.ui.btn_download_pot_server.setObjectName("btn_pref_secondary")
        self.ui.btn_download_plugin.setObjectName("btn_pref_secondary")

        # Dynamic Style Sheet Override
        self.setStyleSheet("""
            QDialog {
                background-color: #161616;
                color: #ffffff;
            }

            QLineEdit, QComboBox, QSpinBox {
                min-height: 20px;
                max-height: 20px;
                padding-left: 5px;
                padding-right: 5px;
            }

            QGroupBox {
                margin-top: 14px;
                padding-top: 12px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                top: 3px;
                padding: 0 5px;
                background-color: #2D2D2D;
            }

            QPushButton#btn_pref_action {
                background-color: #2563eb !important;
                color: #ffffff !important;
                border: 1px solid #3b82f6 !important;
                border-radius: 6px !important;
                padding: 5px 15px !important;
                font-weight: bold !important;
            }
            QPushButton#btn_pref_action:hover {
                background-color: #1d4ed8 !important;
            }
            QPushButton#btn_pref_action:pressed {
                background-color: #1e40af !important;
            }
            QPushButton#btn_pref_action:disabled {
                background-color: #334155 !important;
                color: #64748b !important;
                border: 1px solid #475569 !important;
            }

            QPushButton#btn_pref_secondary {
                background-color: #1e293b !important;
                color: #f8fafc !important;
                border: 1px solid #475569 !important;
                border-radius: 6px !important;
                padding: 4px 12px !important;
                font-weight: normal !important;
            }
            QPushButton#btn_pref_secondary:disabled{
                background-color: #555555 !important;
                color: #888888 !important;
                border-color: #64748b !important;
            }
            QPushButton#btn_pref_secondary:hover {
                background-color: #334155 !important;
                border-color: #64748b !important;
            }
            QPushButton#btn_pref_secondary:pressed {
                background-color: #0f172a !important;
            }

            QPushButton#btn_pref_browse {
                background-color: #1e293b !important;
                color: #ffffff !important;
                border: 1px solid #475569 !important;
                border-radius: 6px !important;
                padding: 4px 12px !important;
                font-size: 9pt !important;
            }
            QPushButton#btn_pref_browse:hover {
                background-color: #334155 !important;
                border-color: #64748b !important;
            }
            QPushButton#btn_pref_browse:pressed {
                background-color: #0f172a !important;
            }

            QPushButton#btn_pref_def_restore {
                background-color: #2c1517 !important;
                color: #f87171 !important;
                border: 1px solid #7f1d1d !important;
                border-radius: 6px !important;
                padding: 4px 12px !important;
                font-size: normal !important;
            }
            QPushButton#btn_pref_def_restore:hover {
                background-color: #450a0a !important;
                color: #fca5a5 !important;
                border-color: #991b1b !important;
            }
            QPushButton#btn_pref_def_restore:pressed {
                background-color: #0f172a !important;
            }

            QPushButton#btn_pref_accent {
                background-color: #16a34a !important;
                color: #ffffff !important;
                border: 1px solid #22c55e !important;
                border-radius: 6px !important;
                padding: 4px 12px !important;
                font-weight: bold !important;
            }
            QPushButton#btn_pref_accent:hover {
                background-color: #15803d !important;
            }
            QPushButton#btn_pref_accent:pressed {
                background-color: #166534 !important;
            }

            QPushButton#btnNone, QPushButton#btnManual, QPushButton#btnCookieFile, QPushButton#btnFromBrowser {
                background-color: #1e1e24 !important;
                color: #ffffff !important;
                border: 1px solid #333333 !important;
                padding: 6px 12px !important;
                font-size: 9.5pt !important;
            }
            QPushButton#btnNone {
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                border-right: none !important;
            }
            QPushButton#btnFromBrowser {
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QPushButton#btnNone:checked, QPushButton#btnManual:checked, QPushButton#btnCookieFile:checked, QPushButton#btnFromBrowser:checked {
                background-color: #4ade80 !important;
                color: #111111 !important;
                border: 1px solid #4ade80 !important;
                font-weight: bold;
            }
            QPushButton#btnNone:hover:not(:checked), QPushButton#btnManual:hover:not(:checked), QPushButton#btnCookieFile:hover:not(:checked), QPushButton#btnFromBrowser:hover:not(:checked) {
                background-color: #2d2d35 !important;
            }

            QWidget:disabled {
                color: #71717a !important;
            }

            QPushButton#btn_pref_secondary:disabled,
            QPushButton#btn_pref_action:disabled,
            QPushButton#btn_pref_browse:disabled {
                background-color: #27272a !important;
                color: #71717a !important;
                border: 1px solid #3f3f46 !important;
            }

            QTabBar::tab:disabled {
                color: #52525b !important;
            }
        """)

        # POT Busy Progress Bar
        self.pot_busy_bar = QProgressBar()
        self.pot_busy_bar.setRange(0, 0)
        self.pot_busy_bar.setTextVisible(False)
        self.pot_busy_bar.setFixedHeight(4)
        self.pot_busy_bar.setVisible(False)
        self.pot_busy_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #1e293b;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: #2563eb;
                border-radius: 2px;
            }
        """)
        if hasattr(self.ui, 'potProviderVLayout'):
            self.ui.potProviderVLayout.insertWidget(0, self.pot_busy_bar)

        # Cookie Button Group Setup & Signals Connection
        self.cookie_button_group = QButtonGroup(self)
        self.cookie_button_group.addButton(self.ui.btnNone, 0)
        self.cookie_button_group.addButton(self.ui.btnManual, 1)
        self.cookie_button_group.addButton(self.ui.btnCookieFile, 2)
        self.cookie_button_group.addButton(self.ui.btnFromBrowser, 3)
        self.cookie_button_group.setExclusive(True)
        self.cookie_button_group.idClicked.connect(self.on_cookie_mode_changed)

        # Combo Box Browser
        if hasattr(self.ui, 'combo_browser'):
            self.ui.combo_browser.clear()
            self.ui.combo_browser.addItems([
                "Chrome", "Edge", "Firefox", "Brave", "Opera", "Vivaldi", "Chromium", "Whale"
            ])

        # Signals & Slots connections
        self.ui.btn_BrowsePath.clicked.connect(self.on_browse_clicked)
        self.ui.btn_reset_output_template.clicked.connect(self.on_reset_output_template_clicked)
        self.ui.btn_reset_playlist_indexing.clicked.connect(self.on_reset_playlist_indexing_clicked)
        self.ui.btn_save.clicked.connect(self.on_save_clicked)
        self.ui.btn_cancel.clicked.connect(self.reject)
        self.ui.btn_restore.clicked.connect(self.on_restore_defaults_clicked)
        self.ui.chk_use_proxy.clicked.connect(self.on_use_proxy_update)
        self.ui.btn_get_cookie_ext.clicked.connect(self.on_get_yawstar_smart_cookie_ext)
        self.ui.btn_clear_cookies.clicked.connect(self.on_clear_restored_cookies)

        if hasattr(self.ui, 'btn_check_update'):
            self.ui.btn_check_update.clicked.connect(self.on_check_update_clicked)

        if hasattr(self.ui, 'btn_browse_cookies'):
            self.ui.btn_browse_cookies.clicked.connect(self.on_browse_cookies_clicked)
        if hasattr(self.ui, 'btn_paste_clipboard'):
            self.ui.btn_paste_clipboard.clicked.connect(self.on_paste_clipboard_clicked)
        if hasattr(self.ui, 'btn_save_manual'):
            self.ui.btn_save_manual.clicked.connect(self.on_save_cookies_data_clicked)

        # [CHANGED] POT Signals Connection — တစ်ခါပဲ ချိတ်
        self.pot_mgr.started_signal.connect(self.on_pot_server_started)
        self.pot_mgr.stopped_signal.connect(self.on_pot_server_stopped)
        self.pot_mgr.log_signal.connect(self.append_output_log)
        self.pot_mgr.error_signal.connect(self.on_pot_server_error)
        self._pot_signals_connected = True

        # Checkbox state change → refresh buttons
        self.ui.chk_enable_pot_server.stateChanged.connect(self.on_enable_pot_server_update)

        if hasattr(self.ui, 'btn_toggle_pot_server'):
            self.ui.btn_toggle_pot_server.clicked.connect(self.on_toggle_start_stop_clicked)

        if hasattr(self.ui, 'btn_download_pot_server'):
            self.ui.btn_download_pot_server.clicked.connect(self.on_download_pot_server_clicked)

        if hasattr(self.ui, 'btn_download_plugin'):
            self.ui.btn_download_plugin.clicked.connect(self.on_download_plugin_clicked)

        # Load Settings Into UI
        self.load_settings_into_ui()
        self.on_use_proxy_update()

    # =========================================================================
    # POT Server signal handlers
    # =========================================================================
    def on_pot_server_started(self, success: bool, message: str):
        """Server start ဖြစ်/မဖြစ်"""
        self.set_ui_busy(False)

        if success:
            # ✅ Success — "Running" ပြ
            logger.info(f"🖲️-✅ {message}")
            if hasattr(self.ui, 'lbl_pot_server_status_val'):
                self.ui.lbl_pot_server_status_val.setText("🟢 Running")
                self.ui.lbl_pot_server_status_val.setStyleSheet("color: #2ECC71;")
            if hasattr(self.ui, 'btn_toggle_pot_server'):
                self.ui.btn_toggle_pot_server.setText("Stop Server")
                self.ui.btn_toggle_pot_server.setEnabled(True)
        else:
            # ❌ Error — "Error" ပြ
            logger.error(f"🖲️-❌ {message}")
            if hasattr(self.ui, 'lbl_pot_server_status_val'):
                self.ui.lbl_pot_server_status_val.setText("🔴 Error")
                self.ui.lbl_pot_server_status_val.setStyleSheet("color: #e74c3c;")
            if hasattr(self.ui, 'btn_toggle_pot_server'):
                self.ui.btn_toggle_pot_server.setText("Start Server")
                self.ui.btn_toggle_pot_server.setEnabled(True)

    def on_pot_server_stopped(self, success: bool, message: str):
        """ Server ရပ်သွားချိန် """
        self.set_ui_busy(False)

        if success:
            if hasattr(self.ui, 'lbl_pot_server_status_val'):
                self.ui.lbl_pot_server_status_val.setText("⚫ Stopped")
                self.ui.lbl_pot_server_status_val.setStyleSheet("color: #8B949E;")
            if hasattr(self.ui, 'btn_toggle_pot_server'):
                self.ui.btn_toggle_pot_server.setText("Start Server")
                self.ui.btn_toggle_pot_server.setEnabled(True)
        else:
            if hasattr(self.ui, 'lbl_pot_server_status_val'):
                self.ui.lbl_pot_server_status_val.setText("🔴 Error")
                self.ui.lbl_pot_server_status_val.setStyleSheet("color: #e74c3c;")
            if hasattr(self.ui, 'btn_toggle_pot_server'):
                self.ui.btn_toggle_pot_server.setText("Start Server")
                self.ui.btn_toggle_pot_server.setEnabled(True)

    @Slot(str, str)
    def on_pot_server_error(self, error_code: str, error_message: str):
        """Server error တက်ရင် UI မှာ ပြ"""
        # [KEY] Stop လုပ်နေချိန်ဆိုရင် error မပြ
        if getattr(self.pot_mgr, '_stop_requested', False):
            logger.debug(f"Ignoring error during stop: {error_code} — {error_message}")
            return

        self.set_ui_busy(False)

        error_titles = {
            "not_found": "Deno Not Found",
            "not_installed": "POT Server Not Installed",
            "failed_to_start": "Server Failed to Start",
            "crashed": "Server Crashed",
        }
        title = error_titles.get(error_code, "POT Server Error")

        # Log မှာ ပြ
        self.append_output_log(f"\n[❌ {title}] {error_message}\n")

        if hasattr(self.ui, 'lbl_pot_server_status_val'):
            self.ui.lbl_pot_server_status_val.setText("🔴 Error")
            self.ui.lbl_pot_server_status_val.setStyleSheet("color: #e74c3c;")
        if hasattr(self.ui, 'btn_toggle_pot_server'):
            self.ui.btn_toggle_pot_server.setText("Start Server")
            self.ui.btn_toggle_pot_server.setEnabled(True)

        # Dialog ပြ (crash မဟုတ်ရင်)
        if error_code != "crashed":
            self.show_custom_message("critical", title, error_message)

    def append_output_log(self, text: str):
        """txtOutputLog ထဲသို့ log text ထည့် (stdout output ကို ဒီမှာ ပြ)"""
        if hasattr(self.ui, 'txtOutputLog'):
            self.ui.txtOutputLog.append(text)
            scrollbar = self.ui.txtOutputLog.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    # =========================================================================
    # set_ui_busy — POT Provider tab ကိုပဲ disable
    # =========================================================================
    def set_ui_busy(self, busy: bool, message: str = "", allow_close: bool = False):
        self.is_busy = busy
        self._force_close_allowed = allow_close

        if hasattr(self, 'pot_busy_bar'):
            self.pot_busy_bar.setVisible(busy)

        if hasattr(self.ui, 'tab_pot_provider'):
            self.ui.tab_pot_provider.setEnabled(not busy)

        for name in ('btn_save', 'btn_restore'):
            if hasattr(self.ui, name):
                getattr(self.ui, name).setEnabled(not busy)

        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    # =========================================================================
    # closeEvent — Busy ဖြစ်နေရင် Confirm dialog မေး
    # =========================================================================
    def closeEvent(self, event):
        if getattr(self, 'is_busy', False):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Operation in Progress")
            msg_box.setText(
                "POT Server operation is still running.\n\n"
                "Do you want to wait for it to finish, or force close?\n\n"
                "⚠️ Force closing may leave the server in an inconsistent state."
            )
            msg_box.setIcon(QMessageBox.Icon.Warning)

            btn_wait = msg_box.addButton("Wait", QMessageBox.ButtonRole.RejectRole)
            btn_force = msg_box.addButton("Force Close", QMessageBox.ButtonRole.DestructiveRole)
            msg_box.setDefaultButton(btn_wait)

            self.apply_msgbox_style(msg_box)
            msg_box.exec()

            if msg_box.clickedButton() == btn_wait:
                event.ignore()
                return
            else:
                self._force_abort_busy_operation()

        self.save_current_tab_index()
        super().closeEvent(event)

    def _force_abort_busy_operation(self):
        """ Busy ဖြစ်နေတဲ့ operation တွေကို force abort လုပ် """
        try:
            if self._stop_worker and self._stop_worker.isRunning():
                self._stop_worker.terminate()
                self._stop_worker.wait(1000)

            for attr in ('pot_dl_thread', 'plugin_dl_thread', 'module_downloader'):
                thread = getattr(self, attr, None)
                if thread and thread.isRunning():
                    thread.terminate()
                    thread.wait(1000)

            self.is_busy = False
            QApplication.restoreOverrideCursor()
            logger.info("Force aborted busy operations.")
        except Exception as e:
            logger.error(f"Force abort failed: {e}")

    def save_current_tab_index(self):
        if hasattr(self.ui, 'tabWidget'):
            current_tab = self.ui.tabWidget.currentIndex()
            self.config_mgr.set("last_settings_tab", current_tab)

    def apply_msgbox_style(self, msg_box):
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #161616;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 9.5pt;
            }
            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 18px;
                min-width: 70px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #64748b;
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
        """)

    def show_custom_message(self, msg_type, title, text):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)

        if msg_type == "info":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif msg_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif msg_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)

        self.apply_msgbox_style(msg_box)
        msg_box.exec()

    def on_cookie_mode_changed(self, button_id):
        if hasattr(self.ui, 'container_manual'):
            self.ui.container_manual.setVisible(button_id == 1)
        if hasattr(self.ui, 'container_cookie_file'):
            self.ui.container_cookie_file.setVisible(button_id == 2)
        if hasattr(self.ui, 'container_browser'):
            self.ui.container_browser.setVisible(button_id == 3)

        if hasattr(self.ui, 'groupCookieStatus'):
            self.ui.groupCookieStatus.setVisible(button_id != 3)

    def on_paste_clipboard_clicked(self):
        clipboard = QApplication.clipboard()
        if hasattr(self.ui, 'txt_manual_cookie'):
            self.ui.txt_manual_cookie.setText(clipboard.text())

    def on_save_cookies_data_clicked(self):
        try:
            cache_dir = os.path.dirname(self.manual_cookies_path)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            cookie_data = self.ui.txt_manual_cookie.toPlainText()

            if not cookie_data.strip():
                cookie_data = self.config_mgr.get("cookies_manual_text", "")
                self.ui.txt_manual_cookie.setText(cookie_data)

            with open(self.manual_cookies_path, "w", encoding="utf-8") as f:
                f.write(cookie_data)

        except Exception as e:
            logger.error(f"❌ An error is occured while saving Cookies: {e}")
            self.show_custom_message("critical", "Error", f"Failed to save cookies data:\n{str(e)}")

    def load_settings_into_ui(self):
        mgr = self.config_mgr

        # General Settings
        self.ui.combo_Language.clear()
        self.ui.combo_Language.addItems(["English (American English)", "Burma (မြန်မာဘာသာ)"])
        self.ui.combo_Language.setCurrentText(mgr.get("language", "English (American English)"))

        self.ui.chkAlwaysOnTop.setChecked(mgr.get("always_on_top", False))
        self.ui.chkRememberSizePos.setChecked(mgr.get("remember_win_pos_size", False))

        self.ui.chk_add_clipboard_auto.setChecked(mgr.get("add_links_clipboard", False))
        self.ui.chk_start_download_auto.setChecked(mgr.get("auto_start_download", False))
        self.ui.chk_remove_completed_auto.setChecked(mgr.get("auto_remove_completed", False))
        self.ui.chk_play_after_downloaded_auto.setChecked(mgr.get("play_after_downloaded", False))
        self.ui.chk_minimize_to_tray.setChecked(mgr.get("minimize_to_tray", False))
        self.ui.chk_notify_fetched.setChecked(mgr.get("notify_fetched", True))
        self.ui.chk_notify_download_started.setChecked(mgr.get("notify_download_started", True))
        self.ui.chk_notify_download_completed.setChecked(mgr.get("notify_download_completed", True))
        self.ui.chk_auto_update.setChecked(mgr.get("check_auto_update", True))

        # Download Settings
        res_val = str(mgr.get("resolution", 1080))
        res_index = self.ui.combo_pref_res.findText(res_val)

        if res_index != -1:
            self.ui.combo_pref_res.setCurrentIndex(res_index)
        else:
            self.ui.combo_pref_res.setCurrentIndex(0)

        self.ui.chk_pref_fps.setChecked(mgr.get("prefer_higher_framerate", True))

        vcon_val = str(mgr.get("video_ext", "mp4"))
        vcon_index = self.ui.combo_pref_vcontainer.findText(vcon_val)

        if vcon_index != -1:
            self.ui.combo_pref_vcontainer.setCurrentIndex(vcon_index)
        else:
            self.ui.combo_pref_vcontainer.setCurrentIndex(0)

        vcodec_val = str(mgr.get("video_codec", "h264"))
        vcodec_index = self.ui.combo_pref_vcodec.findText(vcodec_val)

        if vcodec_index != -1:
            self.ui.combo_pref_vcodec.setCurrentIndex(vcodec_index)
        else:
            self.ui.combo_pref_vcodec.setCurrentIndex(0)

        acon_val = str(mgr.get("audio_ext", "m4a"))
        acon_index = self.ui.combo_pref_acontainer.findText(acon_val)

        if acon_index != -1:
            self.ui.combo_pref_acontainer.setCurrentIndex(acon_index)
        else:
            self.ui.combo_pref_acontainer.setCurrentIndex(0)

        acodec_val = str(mgr.get("audio_codec", "m4a"))
        acodec_index = self.ui.combo_pref_acodec.findText(acodec_val)

        if acodec_index != -1:
            self.ui.combo_pref_acodec.setCurrentIndex(acodec_index)
        else:
            self.ui.combo_pref_acodec.setCurrentIndex(0)

        self.ui.spin_Simultaneous.setValue(mgr.get("simultaneous_limit", 1))
        self.ui.chk_speed_limit.setChecked(mgr.get("use_speed_limit", False))
        self.ui.spin_speed_limit.setValue(mgr.get("speed_limit_val", 500))
        self.ui.inp_dowload_path.setText(mgr.get("download_path", ""))
        self.ui.inp_output_template.setText(mgr.get("output_template", "%(title)s.%(ext)s"))
        self.ui.inp_playlist_indexing.setText(mgr.get("playlist_indexing", "%(playlist_index)s - "))
        self.ui.chk_pad_playlist_index.setChecked(mgr.get("index_filename_with_zero", False))
        self.ui.chk_playlist_own_folders.setChecked(mgr.get("playlist_in_own_folder", False))
        self.ui.chk_forceOverwrite.setChecked(mgr.get("force_overwrite", False))
        self.ui.chk_awakeMode.setChecked(mgr.get("awake_mode", False))

        # Network Settings
        ptype_val = str(mgr.get("proxy_type", "SOCKS5"))
        ptype_index = self.ui.combo_proxy_type.findText(ptype_val)

        if ptype_index != -1:
            self.ui.combo_proxy_type.setCurrentIndex(ptype_index)
        else:
            self.ui.combo_proxy_type.setCurrentIndex(2)

        self.ui.chk_use_proxy.setChecked(mgr.get("use_proxy", False))
        self.ui.inp_proxy_host.setText(mgr.get("proxy_host", ""))
        self.ui.spin_proxy_port.setValue(mgr.get("proxy_port", 8080))
        self.ui.inp_proxy_user.setText(mgr.get("proxy_auth_name", ""))
        self.ui.inp_proxy_pass.setText(mgr.get("proxy_auth_password", ""))

        ipver_val = str(mgr.get("ip_version", "Default"))
        ipver_index = self.ui.combo_ip_version.findText(ipver_val)

        if ipver_index != -1:
            self.ui.combo_ip_version.setCurrentIndex(ipver_index)
        else:
            self.ui.combo_ip_version.setCurrentIndex(0)

        # Cookie Settings
        cookies_type = str(mgr.get("cookies_type", "none")).lower()
        if cookies_type == "manual":
            self.ui.btnManual.setChecked(True)
            self.on_cookie_mode_changed(1)
        elif cookies_type == "file":
            self.ui.btnCookieFile.setChecked(True)
            self.on_cookie_mode_changed(2)
        elif cookies_type == "browser":
            self.ui.btnFromBrowser.setChecked(True)
            self.on_cookie_mode_changed(3)
        else:
            self.ui.btnNone.setChecked(True)
            self.on_cookie_mode_changed(0)

        if hasattr(self.ui, 'inp_cookies_path'):
            self.ui.inp_cookies_path.setText(mgr.get("cookies_path", ""))
        if hasattr(self.ui, 'txt_manual_cookie'):
            self.ui.txt_manual_cookie.setText(mgr.get("cookies_manual_text", ""))
        if hasattr(self.ui, 'combo_browser'):
            self.ui.combo_browser.setCurrentText(mgr.get("cookies_browser_name", "Chrome"))

        if cookies_type != "none":
            self.ui.lbl_cookie_status.setText(f"Status: Active cookie loaded from {cookies_type}")
        else:
            self.ui.lbl_cookie_status.setText("Status: No active cookie loaded.")

        # POT Server settings
        self.ui.spin_pot_port.setEnabled(False)
        enable_pot_server = mgr.get("enable_pot_server", False)
        self.ui.chk_enable_pot_server.setChecked(bool(enable_pot_server))

        self.refresh_POT_Server_Page()

    def on_browse_clicked(self):
        current_path = self.ui.inp_dowload_path.text()
        os_downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        if current_path == "":
            current_path = os_downloads_path
        dir_path = QFileDialog.getExistingDirectory(self, "Select Download Directory", current_path)
        if dir_path:
            self.ui.inp_dowload_path.setText(os.path.normpath(dir_path))

    def on_reset_output_template_clicked(self):
        self.ui.inp_output_template.setText("%(title).200s.%(ext)s")

    def on_reset_playlist_indexing_clicked(self):
        self.ui.inp_playlist_indexing.setText("%(playlist_index)s - ")

    def on_use_proxy_update(self):
        is_checked = self.ui.chk_use_proxy.isChecked()

        controls = [
            'inp_proxy_host', 'inp_proxy_user', 'combo_proxy_type',
            'spin_proxy_port', 'inp_proxy_pass', 'spin_socket_timeout',
            'spin_max_retries', 'inp_geo_bypass_country'
        ]

        for widget_name in controls:
            if hasattr(self.ui, widget_name):
                getattr(self.ui, widget_name).setEnabled(is_checked)

    def on_enable_pot_server_update(self):
        # is_checked = self.ui.chk_enable_pot_server.isChecked()
        self.refresh_POT_Server_Page()

    def on_browse_cookies_clicked(self):
        current_path = self.ui.inp_cookies_path.text() if hasattr(self.ui, 'inp_cookies_path') else ""
        os_downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        if current_path == "":
            current_path = os_downloads_path
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Cookies File", current_path, "Text Files (*.txt);;All Files (*)")
        if file_path and hasattr(self.ui, 'inp_cookies_path'):
            self.ui.inp_cookies_path.setText(os.path.normpath(file_path))

    def get_selected_cookies_type(self):
        if self.ui.btnManual.isChecked():
            return "manual"
        elif self.ui.btnCookieFile.isChecked():
            return "file"
        elif self.ui.btnFromBrowser.isChecked():
            return "browser"
        return "none"

    def on_save_clicked(self):
        use_Cookies = False
        if self.get_selected_cookies_type() != "none":
            use_Cookies = True
        else:
            use_Cookies = False

        current_tab_index = self.ui.tabWidget.currentIndex() if hasattr(self.ui, 'tabWidget') else 0

        updated_data = {
            "last_settings_tab": current_tab_index,
            "language": self.ui.combo_Language.currentText(),
            "always_on_top": self.ui.chkAlwaysOnTop.isChecked(),
            "remember_win_pos_size": self.ui.chkRememberSizePos.isChecked(),
            "add_links_clipboard": self.ui.chk_add_clipboard_auto.isChecked(),
            "auto_start_download": self.ui.chk_start_download_auto.isChecked(),
            "auto_remove_completed": self.ui.chk_remove_completed_auto.isChecked(),
            "play_after_downloaded": self.ui.chk_play_after_downloaded_auto.isChecked(),
            "minimize_to_tray": self.ui.chk_minimize_to_tray.isChecked(),
            "notify_fetched": self.ui.chk_notify_fetched.isChecked(),
            "notify_download_started": self.ui.chk_notify_download_started.isChecked(),
            "notify_download_completed": self.ui.chk_notify_download_completed.isChecked(),
            "check_auto_update": self.ui.chk_auto_update.isChecked(),
            "video_ext": self.ui.combo_pref_vcontainer.currentText(),
            "resolution": self.ui.combo_pref_res.currentText(),
            "prefer_higher_framerate": self.ui.chk_pref_fps.isChecked(),
            "video_codec": self.ui.combo_pref_vcodec.currentText(),
            "audio_ext": self.ui.combo_pref_acontainer.currentText(),
            "audio_codec": self.ui.combo_pref_acodec.currentText(),
            "use_speed_limit": self.ui.chk_speed_limit.isChecked(),
            "simultaneous_limit": self.ui.spin_Simultaneous.value(),
            "speed_limit_val": self.ui.spin_speed_limit.value(),
            "download_path": self.ui.inp_dowload_path.text(),
            "output_template": self.ui.inp_output_template.text(),
            "index_filename_with_zero": self.ui.chk_pad_playlist_index.isChecked(),
            "playlist_in_own_folder": self.ui.chk_playlist_own_folders.isChecked(),
            "playlist_indexing": self.ui.inp_playlist_indexing.text(),
            "force_overwrite": self.ui.chk_forceOverwrite.isChecked(),
            "awake_mode": self.ui.chk_awakeMode.isChecked(),
            "use_proxy": self.ui.chk_use_proxy.isChecked(),
            "proxy_host": self.ui.inp_proxy_host.text(),
            "proxy_port": self.ui.spin_proxy_port.value(),
            "proxy_auth_name": self.ui.inp_proxy_user.text(),
            "proxy_auth_password": self.ui.inp_proxy_pass.text(),
            "ip_version": self.ui.combo_ip_version.currentText(),
            "use_cookies": use_Cookies,
            "proxy_type": self.ui.combo_proxy_type.currentText(),
            "cookies_type": self.get_selected_cookies_type(),
            "cookies_path": self.ui.inp_cookies_path.text() if hasattr(self.ui, 'inp_cookies_path') else "",
            "cookies_manual_text": self.ui.txt_manual_cookie.toPlainText() if hasattr(self.ui, 'txt_manual_cookie') else "",
            "cookies_browser_name": self.ui.combo_browser.currentText() if hasattr(self.ui, 'combo_browser') else "Chrome",
            "enable_pot_server": self.ui.chk_enable_pot_server.isChecked()
        }

        try:
            if self.config_mgr.update_multiple(updated_data):
                self.accept()
            else:
                self.show_custom_message("warning", "Save Error", "Failed to save configuration settings.")
        except Exception as e:
            self.show_custom_message("critical", "Error", f"An unexpected error occurred while saving: {e}")

    def reject(self):
        self.save_current_tab_index()
        super().reject()

    def on_restore_defaults_clicked(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Confirm Reset')
        msg_box.setText('Are you sure you want to restore all settings to default?')
        msg_box.setIcon(QMessageBox.Icon.Question)

        btn_yes = msg_box.addButton(QMessageBox.StandardButton.Yes)
        btn_no = msg_box.addButton(QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(btn_no)

        self.apply_msgbox_style(msg_box)

        msg_box.exec()

        if msg_box.clickedButton() == btn_yes:
            if os.path.exists(self.manual_cookies_path):
                try:
                    os.remove(self.manual_cookies_path)
                except Exception as e:
                    logger.error(f"❌ Failed to delete manual cookies file: {e}")
            else:
                logger.error("ℹ️ Manual cookies file does not exist.")

            if self.config_mgr.restore_defaults():
                self.load_settings_into_ui()
                self.show_custom_message("info", "Success", "All settings have been restored to default.")
                self.accept()
            else:
                self.show_custom_message("warning", "Error", "Failed to restore default settings.")

    def on_get_yawstar_smart_cookie_ext(self):
        self.open_link("https://github.com/YawStar/Smart-Cookies")

    def on_clear_restored_cookies(self):
        self.ui.inp_cookies_path.setText("")
        self.ui.txt_manual_cookie.setText("")

    def on_check_update_clicked(self):
        if hasattr(self.ui, 'btn_check_update'):
            self.ui.btn_check_update.setEnabled(False)
            self.ui.btn_check_update.setText("Checking...")
            logger.info("Checking for application updates...")

        current_ver = self.config_mgr.get("app_version", CONST.APP_VERSION)

        self.update_thread = DirectUpdateCheckerThread(current_version=current_ver, parent=self)
        self.update_thread.update_checked.connect(self.on_update_check_finished)
        self.update_thread.check_failed.connect(self.on_update_check_failed)
        self.update_thread.start()

    def on_update_check_finished(self, is_available: bool, latest_ver: str, notes: str, download_url: str):
        if hasattr(self.ui, 'btn_check_update'):
            self.ui.btn_check_update.setEnabled(True)
            self.ui.btn_check_update.setText("Check Now")

        current_ver = self.config_mgr.get("app_version", CONST.APP_VERSION)

        if is_available:
            dialog = ModernUpdateDialog(
                current_ver=current_ver,
                latest_ver=latest_ver,
                release_notes=notes,
                download_url="https://github.com/YawStar/U-Tube-Downloader/releases",
                parent=self
            )
            logger.info(f"Current: {current_ver} | Latest: {latest_ver} | Update Available: {is_available}")
            dialog.exec()
        else:
            logger.info("No Updates: You are using the latest version.")
            self.show_custom_message("info", "No Updates", "You are using the latest version.")

    def on_update_check_failed(self, error_msg: str):
        if hasattr(self.ui, 'btn_check_update'):
            self.ui.btn_check_update.setEnabled(True)
            self.ui.btn_check_update.setText("Check Now")

        logger.error(f"Failed to check for updates: Could not check for updates:\n{error_msg}")
        self.show_custom_message("warning", "Update Check Failed", f"Could not check for updates:\n{error_msg}\n\nမအေလိုး မင်းအောင်လှိုင်ကောင်းမှုကြောင့် GitHub Api ကိုဖတ်မရပါသဖြင့် VPN သုံးပြီး ပြန်စစ်ပါ..")

    def refresh_POT_Server_Page(self):
        """ POT Server status, install state, checkbox state အားလုံးကို refresh """
        is_checked = self.ui.chk_enable_pot_server.isChecked()

        # Server install state
        ys_pot_server_bin = os.path.join(TPT_DIR, SVR_EXE_NAME)
        server_installed = os.path.exists(ys_pot_server_bin)
        if server_installed:
            self.ui.lbl_pot_server_info_val.setText("✅ Installed")
            self.ui.lbl_pot_server_info_val.setStyleSheet("color: #2ECC71;")
            self.ui.btn_download_pot_server.setText("Uninstall POT Server")
        else:
            self.ui.lbl_pot_server_info_val.setText("❌ Not Installed")
            self.ui.lbl_pot_server_info_val.setStyleSheet("color: #F39C12;")
            self.ui.btn_download_pot_server.setText("Download POT Server")

        # Plugin install state
        plugin_zip = os.path.join(TPT_DIR, "yt-dlp-plugins", "yawstar-ytdlp-pot-provider.zip")
        plugin_installed = os.path.exists(plugin_zip)
        if plugin_installed:
            self.ui.lbl_bgutil_plugin_val.setText("✅ Installed")
            self.ui.lbl_bgutil_plugin_val.setStyleSheet("color: #2ECC71;")
            self.ui.btn_download_plugin.setText("Uninstall Plugin")
        else:
            self.ui.lbl_bgutil_plugin_val.setText("❌ Not Installed")
            self.ui.lbl_bgutil_plugin_val.setStyleSheet("color: #F39C12;")
            self.ui.btn_download_plugin.setText("Download Plugin")


        is_pot_server_running = self.pot_mgr.is_server_running()
        if is_pot_server_running:
            if hasattr(self.ui, 'lbl_pot_server_status_val'):
                self.ui.lbl_pot_server_status_val.setText("🟢 Running")
                self.ui.lbl_pot_server_status_val.setStyleSheet("color: #2ECC71;")
            if hasattr(self.ui, 'btn_toggle_pot_server'):
                self.ui.btn_toggle_pot_server.setText("Stop Server")
                self.ui.btn_toggle_pot_server.setEnabled(True)
        else:
            if hasattr(self.ui, 'lbl_pot_server_status_val'):
                self.ui.lbl_pot_server_status_val.setText("⚫ Stopped")
                self.ui.lbl_pot_server_status_val.setStyleSheet("color: #8B949E;")
            if hasattr(self.ui, 'btn_toggle_pot_server'):
                self.ui.btn_toggle_pot_server.setText("Start Server")
                self.ui.btn_toggle_pot_server.setEnabled(True)

        # Buttons
        if server_installed:
            self.ui.btn_toggle_pot_server.setEnabled(True)
        else:
            self.ui.btn_toggle_pot_server.setEnabled(False)

        # self.ui.btn_download_pot_server.setEnabled(is_checked and not server_installed)
        # self.ui.btn_download_plugin.setEnabled(is_checked and not plugin_installed)
        # self.ui.spin_pot_port.setEnabled(False)

    def on_toggle_start_stop_clicked(self):
        """ YawStar ytdlp POT Server ကို စတင်/ရပ်တန့် """
        is_pot_server_running = self.pot_mgr.is_server_running()

        self.ui.txtOutputLog.clear()

        if is_pot_server_running:
            # ============ STOP ============
            # [KEY] Stop flag ကို ချက်ချင်း သတ် — crash signal မရောက်စေရန်
            self.pot_mgr._stop_requested = True
            self.pot_mgr._running = False

            self.ui.btn_toggle_pot_server.setText("Stopping...")
            self.ui.btn_toggle_pot_server.setEnabled(False)
            self.ui.lbl_pot_server_status_val.setText("Stopping...")
            self.ui.lbl_pot_server_status_val.setStyleSheet("color: #f39c12;")
            QApplication.processEvents()

            self.set_ui_busy(True, "Stopping...", allow_close=True)

            self._stop_worker = StopServerWorker(self.pot_mgr, parent=self)
            self._stop_worker.finished.connect(self.on_pot_server_stopped)
            self._stop_worker.start()
        else:
            # ============ START ============
            self.ui.btn_toggle_pot_server.setText("Starting...")
            self.ui.btn_toggle_pot_server.setEnabled(False)
            self.ui.lbl_pot_server_status_val.setText("Starting...")
            self.ui.lbl_pot_server_status_val.setStyleSheet("color: #f39c12;")
            QApplication.processEvents()

            self.set_ui_busy(True, "Starting...", allow_close=True)

            self.pot_mgr.start()

    def _on_pot_server_download_finished(self, success: bool, message: str):
        self.set_ui_busy(False)

        if hasattr(self.ui, 'btn_download_pot_server'):
            self.ui.btn_download_pot_server.setEnabled(True)
            self.ui.btn_download_pot_server.setText("Download Server")

        if IS_LINUX or IS_MACOS:
            if os.path.exists(os.path.join(self.target_dir, "yawstar-pot-server")): 
                os.chmod(os.path.join(self.target_dir, "yawstar-pot-server"), 0o755)

        self.refresh_POT_Server_Page()

        if success:
            self.append_output_log("[INFO]: POT Server dowload successful.")
        else:
            self.append_output_log("[INFO]: POT Server dowload error.")

    def on_plugin_download_progress(self):
        pass

    def _on_plugin_download_finished(self, success: bool, message: str):
        self.set_ui_busy(False)

        if hasattr(self.ui, 'btn_download_plugin'):
            self.ui.btn_download_plugin.setEnabled(True)
            self.ui.btn_download_plugin.setText("Download Plugin")

        self.refresh_POT_Server_Page()
        if success:
            self.append_output_log("[INFO]: Plugin dowload successful.")
        else:
            self.append_output_log("[INFO]: Plugin download error.")

    def on_download_pot_server_clicked(self):
      filePath = os.path.join(TPT_DIR, SVR_EXE_NAME)
      if os.path.exists(filePath):
        self.ui.txtOutputLog.clear()
        self.set_ui_busy(True, "Uninstalling POT Server...", allow_close=True)
        self.append_output_log("Uninstalling POT Server...")
        try:
          os.remove(filePath)
          self.append_output_log("Uninstalling POT Server successful...")
        except OSError as e:
          self.append_output_log(f"Uninstalling POT Server failed: {e}")
        self.set_ui_busy(False)
        self.refresh_POT_Server_Page()
        return

      # ဒေါင်းလုပ်မဆွဲခင် နောက်ဆုံး Version ကို GitHub ကနေ အရင် စစ်ယူပါမည်
      self.ui.txtOutputLog.clear()
      self.set_ui_busy(True, "Fetching latest version...", allow_close=True)
      self.append_output_log("Checking latest release for POT Server...")
      QApplication.processEvents()

      self.release_checker = GitHubReleaseFetcherThread(
          "YawStar", "ytdlp-pot-provider", parent=self
      )
      self.release_checker.release_fetched.connect(
          self._start_pot_server_download
      )
      self.release_checker.fetch_failed.connect(self._on_release_fetch_failed)
      self.release_checker.start()

    def _start_pot_server_download(
        self, latest_version: str, server_url: str, plugin_url: str
    ):
      filePath = os.path.join(TPT_DIR, SVR_EXE_NAME)
      self.append_output_log(
          f"Latest version found: {latest_version}. Downloading from:"
          f" {server_url}"
      )

      if hasattr(self.ui, 'btn_download_pot_server'):
        self.ui.btn_download_pot_server.setEnabled(False)
        self.ui.btn_download_pot_server.setText("Downloading...")
        self.ui.lbl_pot_server_info_val.setText("Downloading...")
        self.ui.lbl_pot_server_info_val.setStyleSheet("color: #f39c12;")

      self.pot_dl_thread = FileDownloaderThread(
          url=server_url,
          save_path=filePath,
          extract_to=TPT_DIR,
          is_zip=True,
          parent=self,
      )

      def _handle_pot_dl_progress(msg: str):
        logger.info(f"[POT Server DL]: {msg}")
        self.append_output_log(f"[POT Server DL]: {msg}")

      self.pot_dl_thread.progress_signal.connect(_handle_pot_dl_progress)
      self.pot_dl_thread.finished_signal.connect(
          self._on_pot_server_download_finished
      )
      self.pot_dl_thread.start()

    def on_download_plugin_clicked(self):
      plugin_dir = os.path.join(TPT_DIR, "yt-dlp-plugins")
      plugin_zip_path = os.path.join(
          plugin_dir, "yawstar-ytdlp-pot-provider.zip"
      )

      if os.path.exists(plugin_zip_path):
        self.ui.txtOutputLog.clear()
        self.set_ui_busy(True, "Uninstalling Plugin...", allow_close=True)
        self.append_output_log("Uninstalling Plugin...")
        try:
          os.remove(plugin_zip_path)
          self.append_output_log("Uninstalling Plugin successful...")
        except OSError as e:
          self.append_output_log(f"Uninstalling Plugin failed: {e}")
        self.set_ui_busy(False)
        self.refresh_POT_Server_Page()
        return

      # ဒေါင်းလုပ်မဆွဲခင် နောက်ဆုံး Version ကို GitHub ကနေ အရင် စစ်ယူပါမည်
      self.ui.txtOutputLog.clear()
      self.set_ui_busy(True, "Fetching latest version...", allow_close=True)
      self.append_output_log("Checking latest release for Plugin...")
      QApplication.processEvents()

      self.release_checker = GitHubReleaseFetcherThread(
          "YawStar", "ytdlp-pot-provider", parent=self
      )
      self.release_checker.release_fetched.connect(
          self._start_plugin_download
      )
      self.release_checker.fetch_failed.connect(self._on_release_fetch_failed)
      self.release_checker.start()

    def _start_plugin_download(
        self, latest_version: str, server_url: str, plugin_url: str
    ):
      plugin_dir = os.path.join(TPT_DIR, "yt-dlp-plugins")
      plugin_zip_path = os.path.join(
          plugin_dir, "yawstar-ytdlp-pot-provider.zip"
      )
      self.append_output_log(
          f"Latest version found: {latest_version}. Downloading Plugin from:"
          f" {plugin_url}"
      )

      if hasattr(self.ui, 'btn_download_plugin'):
        self.ui.btn_download_plugin.setEnabled(False)
        self.ui.btn_download_plugin.setText("Downloading...")
        self.ui.lbl_bgutil_plugin_val.setText("Downloading...")
        self.ui.lbl_bgutil_plugin_val.setStyleSheet("color: #f39c12;")

      self.plugin_dl_thread = FileDownloaderThread(
          url=plugin_url, save_path=plugin_zip_path, is_zip=False, parent=self
      )

      def _handle_plugin_dl_progress(msg: str):
        logger.info(f"[Plugin DL]: {msg}")
        self.append_output_log(f"[Plugin DL]: {msg}")

      self.plugin_dl_thread.progress_signal.connect(_handle_plugin_dl_progress)
      self.plugin_dl_thread.finished_signal.connect(
          self._on_plugin_download_finished
      )
      self.plugin_dl_thread.start()

    def _on_release_fetch_failed(self, error_msg: str):
      self.set_ui_busy(False)
      self.refresh_POT_Server_Page()
      self.append_output_log(f"[Error]: Failed to fetch latest release: {error_msg}")
      self.show_custom_message(
          "warning",
          "Update Check Failed",
          f"Could not fetch latest release from GitHub:\n{error_msg}",
      )

    def open_link(self, url: str):
        if url:
            QDesktopServices.openUrl(QUrl(url))
