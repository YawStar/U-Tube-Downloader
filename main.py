# AppName = YawStar U-Tube Downloader
# Author = YawHackka (YawStar)

import sys
import os
import re
import platform
import subprocess
import json

from PySide6.QtWidgets import (
    QApplication, QListWidgetItem, QMainWindow, QSystemTrayIcon,
    QMessageBox, QDialog, QMenu, QLabel, QToolButton, QVBoxLayout,
    QWidget, QHBoxLayout, QPushButton,
)
from PySide6.QtCore import (
    QEventLoop, Qt, QSize, QStandardPaths,
    QCoreApplication, QUrl, QTimer,
)
from PySide6.QtGui import (
    QDesktopServices, QPixmap, QMovie, QIcon, QFont,
    QBitmap, QPainter, QCursor,
)

from PySide6.QtNetwork import QNetworkAccessManager

from wakepy import keep

# Random
import time
import random
import string

# CONSTANTS
import core.global_constants as CONST

# Resources
import assets.resources_rc  # noqa: F401

# Single Instance
from app_platform.application import SingletonApplication

APP_ID = f'{CONST.COMPANY_NAME}.{CONST.APP_NAME}.subproduct.{CONST.APP_VERSION}'

# UI
from ui.ui_main import Ui_MainWindow

# History UI
from ui.ui_history import Ui_HistoryDialog

# Config
from core.config_manager import ConfigManager

# Database
from core.db_manager import DatabaseManager

# Clipboard
from core.clipboard_monitor import ClipboardMonitor

# Dialogs
from ui.format_dialog import FormatDialog
from ui.settings_dialog import SettingsDialog

# Dependency Downloader
import core.dependency_downloader

# About
import ui.about

# ============================================================================
# ✨ Phase 1 — Refactored services
# ============================================================================
from core.services.yt_dlp_service import YtDlpService
from utils.text_utils import description_to_html

# ============================================================================
# ✨ Phase 2 — Refactored services
# ============================================================================
from core.services.thumbnail_service import ThumbnailService
from core.services.notification_service import NotificationService
from core.services.taskbar_service import TaskbarService

# ============================================================================
# ✨ Phase 3 — Controllers
# ============================================================================
from controllers.fetch_controller import FetchController
from controllers.download_controller import DownloadController

# ============================================================================
# ✨ Phase 4 — File Opener Service
# ============================================================================
from core.services.file_opener import FileOpenerService

# ============================================================================
# ✨ Phase 5A — Logging + Constants
# ============================================================================
from utils.logger import setup_logging, get_logger
from core.constants import (
    ConfigKey, StatusMsg, UiState, ResourcePath, Timing,
)

# main.py — imports
from core.services.font_service import FontService

# ============================================================================
# Setup: QCoreApplication metadata
# ============================================================================
QCoreApplication.setOrganizationName(CONST.COMPANY_NAME)
QCoreApplication.setApplicationName(CONST.APP_NAME)

# OS
CURRENT_OS = platform.system()
BIN_EXT = ".exe" if CURRENT_OS == "Windows" else ""

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

CONFIG_PATH = os.path.normpath(os.path.join(APP_DATA_DIR, "config.json"))

DB_PATH = os.path.normpath(os.path.join(APP_DATA_DIR, "history.db"))


# ============================================================================
# ✨ Phase 5A — Logging setup
# ============================================================================
LOG_FILE = os.path.normpath(os.path.join(APP_DATA_DIR, "app.log"))
setup_logging(log_file=LOG_FILE, level=10)  # DEBUG level

# Module logger
logger = get_logger(__name__)
logger.info(f"=== {CONST.APP_NAME} {CONST.APP_VERSION} starting ===")

# ============================================================================
# Launch state
# ============================================================================
is_first_launch = not os.path.exists(CONFIG_PATH)

downloads_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
download_path = os.path.normpath(os.path.join(downloads_dir, 'U-Tube Downloader'))
manual_cookies_path = os.path.join(APP_CACHE_DIR, "manual_cookies.txt")

if not os.path.exists(download_path):
    os.makedirs(download_path)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # ⭐ Font apply — Designer ရဲ့ font ကို override
        myanmar_family = FontService.get_family(
            ":/fonts/fonts/pyidaungsu.ttf", fallback="sans-serif"
        )
        window_font = QFont()
        window_font.setFamilies([myanmar_family, "Pyidaungsu", "sans-serif"])
        window_font.setPointSize(10)
        self.setFont(window_font)

        self.setWindowTitle(f"{CONST.APP_NAME} - {CONST.APP_VERSION}")
        app_icon = QIcon(ResourcePath.APP_ICON)
        self.setWindowIcon(app_icon)

        # =====================================================================
        # Tips Rotation
        # =====================================================================
        self.tips_list = [
            "👉 Supports thousands of websites including YouTube, Facebook, Instagram, X, TikTok, Bilibili etc.",
            "🚩 Make sure to set a download directory before downloading.",
            "ℹ️ Having download issues? Go to Settings to configure cookies or update yt-dlp.",
            "😊 Choose video-only or audio-only mode to download as needed.",
            "🖼️ Right-click on the thumbnail to save it.",
            "🧊 Click uploader name to visit the channel.",
            "♦️You can stop fetching or downloading anytime.",
            "❤️ Support the developer to help improve this program.",
        ]
        self.current_tip_index = 0
        self.show_tips = True

        self.tip_timer = QTimer(self)
        self.tip_timer.setInterval(Timing.TIPS_INTERVAL_MS)
        self.tip_timer.timeout.connect(self.rotate_tips)
        self.start_tips_rotation()

        # =====================================================================
        # txtInfoLog link interaction
        # =====================================================================
        self.txtInfoLog.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        # =====================================================================
        # Sleep mode context
        # =====================================================================
        self.awake_mode = None

        # =====================================================================
        # Network Manager (ThumbnailService အတွက်)
        # =====================================================================
        self.network_manager = QNetworkAccessManager(self)

        # =====================================================================
        # Config Manager
        # =====================================================================
        self.config_mgr = ConfigManager(CONFIG_PATH)

        # =====================================================================
        # Database Init လုပ်
        # =====================================================================
        self.db_mgr = DatabaseManager(DB_PATH)

        # =====================================================================
        # ✨ Phase 1 — YtDlpService
        # =====================================================================
        self.yt_dlp_service = YtDlpService(
            tools_dir=TPT_DIR,
            bin_ext=BIN_EXT,
            manual_cookies_path=manual_cookies_path,
        )

        # =====================================================================
        # ✨ Phase 2 — ThumbnailService
        # =====================================================================
        self.thumbnail_service = ThumbnailService(self.network_manager, self)
        self.thumbnail_service.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.thumbnail_service.thumbnail_failed.connect(self.on_thumbnail_failed)

        # =====================================================================
        # ✨ Phase 2 — TaskbarService
        # =====================================================================
        if CURRENT_OS == "Windows":
            hwnd = int(self.winId())
        else:
            hwnd = 0
        self.taskbar_service = TaskbarService(
            hwnd, is_windows=(CURRENT_OS == "Windows")
        )

        # =====================================================================
        # ✨ Phase 3 — FetchController
        # =====================================================================
        self.fetch_controller = FetchController(self.yt_dlp_service, self)
        self.fetch_controller.fetch_started.connect(self.on_fetch_started)
        self.fetch_controller.fetch_completed.connect(self.on_fetch_completed)
        self.fetch_controller.fetch_failed.connect(self.on_fetch_failed)
        self.fetch_controller.fetch_cancelled.connect(self.on_fetch_cancelled)
        self.fetch_controller.cookies_required.connect(
            self.on_fetch_cookies_required
        )

        # =====================================================================
        # ✨ Phase 3 — DownloadController
        # =====================================================================
        self.download_controller = DownloadController(self.yt_dlp_service, self)
        self.download_controller.download_started.connect(self.on_download_started)
        self.download_controller.download_log.connect(self.on_download_log)
        self.download_controller.download_destination_changed.connect(
            self.on_download_destination_changed
        )
        self.download_controller.download_progress.connect(
            self.on_download_progress
        )
        self.download_controller.download_indeterminate.connect(
            self.on_download_indeterminate
        )
        self.download_controller.download_completed.connect(
            self.on_download_completed
        )
        self.download_controller.download_failed.connect(self.on_download_failed)
        self.download_controller.download_cancelled.connect(
            self.on_download_cancelled
        )
        self.download_controller.download_progress_resumed.connect(
            self.on_download_progress_resumed
        )

        # =====================================================================
        # Loaded settings (global)
        # =====================================================================
        global loaded_settings
        loaded_settings = self.config_mgr.get_all()

        # =====================================================================
        # UI initial states
        # =====================================================================
        self.lblUploaderVal.mousePressEvent = self.open_uploader_url

        self.urlInput.setText(
            str(loaded_settings.get(
                ConfigKey.LAST_ADDED_URL,
                'https://www.youtube.com/watch?v=gEy-6IWaVh4'
            ))
        )

        self.embThumbnailButton.setChecked(
            bool(loaded_settings.get(ConfigKey.EMBED_THUMBNAIL))
        )
        self.embChaptersButton.setChecked(
            bool(loaded_settings.get(ConfigKey.EMBED_CHAPTERS))
        )
        self.embSubtitlesButton.setChecked(
            bool(loaded_settings.get(ConfigKey.EMBED_SUBTITLES))
        )
        self.embMetadataButton.setChecked(
            bool(loaded_settings.get(ConfigKey.EMBED_METADATA))
        )
        self.useMTimeButton.setChecked(
            bool(loaded_settings.get(ConfigKey.USE_MTIME))
        )

        self.progressBar.setVisible(False)
        self.show_option_controls_status(False)
        self.is_marquee = False
        self.selectFormatsButton.setEnabled(False)
        self.downloadButton.setEnabled(False)
        self.display_default_thumbnail()

        # =====================================================================
        # Tray + Notification + Menus
        # =====================================================================
        self.tray_icon = None
        self.setup_tray_icon()

        self.notification_service = NotificationService(self.tray_icon, self)

        if self.tray_icon:
            tray_menu = QMenu(self)
            tray_menu.setStyleSheet("""
                QMenu {
                    font-size: 13px;
                    font-family: "Segoe UI", sans-serif;
                }
                QMenu::item {
                    padding: 4px 20px 4px 10px;
                }
            """)

            paste_link_action = tray_menu.addAction("Paste link")
            self.auto_add_from_clipboard_action = tray_menu.addAction("Auto add from clipboard")
            self.auto_add_from_clipboard_action.setCheckable(True)
            self.auto_add_from_clipboard_action.setChecked(
                bool(loaded_settings.get(ConfigKey.ADD_LINKS_CLIPBOARD))
            )
            

            # (Separator) ခြား
            tray_menu.addSeparator()

            show_action = tray_menu.addAction("Show Window")
            exit_action = tray_menu.addAction("Quit")

            paste_link_action.triggered.connect(self.paste_link)
            self.auto_add_from_clipboard_action.triggered.connect(self.on_toggle_clipboard_action)
            show_action.triggered.connect(self.showNormal)
            exit_action.triggered.connect(self.fully_exit_app)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # =====================================================================
        # Assets/BINS → PATH
        # =====================================================================
        base_dir = os.path.dirname(os.path.abspath(__file__))
        bin_folder = os.path.join(base_dir, "Assets", "BINS")
        if bin_folder not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + bin_folder

        # =====================================================================
        # View state
        # =====================================================================
        self.info_buffer = ""
        self.original_description = ""
        self.final_downloaded_path = ""
        self.cookie_grabber_window = None
        self.info = None
        self.selected_format_id = None

        # =====================================================================
        # Clipboard
        # =====================================================================
        self.clipboard_thread = None
        self.check_and_toggle_clipboard_monitor()

        # =====================================================================
        # Signals & Slots
        # =====================================================================
        self.getInfoButton.clicked.connect(self.on_get_info_clicked)
        self.downloadButton.clicked.connect(self.on_download_clicked)
        self.historyButton.clicked.connect(self.on_history_clicked)
        self.pasteButton.clicked.connect(self.on_paste_clicked)
        self.openFolderButton.clicked.connect(self.on_open_folder_clicked)
        self.selectFormatsButton.clicked.connect(self.on_select_formats_clicked)
        self.settingsButton.clicked.connect(self.on_settings_clicked)
        self.aboutButton.clicked.connect(self.on_about_button_clicked)

        # Thumbnail right-click
        self.lblThumbnail.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.lblThumbnail.customContextMenuRequested.connect(
            self.on_thumbnail_context_menu
        )

        self.statusbar.showMessage(StatusMsg.READY)
        logger.info("MainWindow initialized")

    # =========================================================================
    # Tips Rotation
    # =========================================================================
    def start_tips_rotation(self):
        if self.show_tips:
            self.statusbar.showMessage(self.tips_list[self.current_tip_index])
            self.tip_timer.start()

    def rotate_tips(self):
        if not self.show_tips:
            self.tip_timer.stop()
            return
        self.current_tip_index = (self.current_tip_index + 1) % len(self.tips_list)
        self.statusbar.showMessage(self.tips_list[self.current_tip_index])

    def stop_tips_rotation(self):
        self.show_tips = False
        if self.tip_timer.isActive():
            self.tip_timer.stop()

    # =========================================================================
    # Dependencies
    # =========================================================================
    def check_necessary_files(self):
        return self.yt_dlp_service.check_necessary_files()

    def open_dep_downloader(self):
        self.dep_window = core.dependency_downloader.MainWindow(parent=self)
        self.dep_window.setAttribute(Qt.WA_DeleteOnClose)
        self.dep_window.setWindowModality(Qt.WindowModal)
        self.dep_window.show()

    # =========================================================================
    # Close / Exit
    # =========================================================================
    def closeEvent(self, event):
        is_info_running = self.fetch_controller.is_running()
        is_download_running = self.download_controller.is_running()

        global loaded_settings
        if loaded_settings.get(ConfigKey.MINIMIZE_TO_TRAY, True):
            event.ignore()
            self.hide()
            if self.tray_icon:
                if is_info_running or is_download_running:
                    self.notification_service.notify_background_work()
        else:
            if is_info_running or is_download_running:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Confirm Exit")
                msg_box.setText(
                    "1 videos are currently in progress.\n\n"
                    "Do you want to stop them and quit?"
                )
                msg_box.setIcon(QMessageBox.Icon.Question)

                yes_button = msg_box.addButton(
                    "Yes", QMessageBox.ButtonRole.YesRole
                )
                no_button = msg_box.addButton(
                    "No", QMessageBox.ButtonRole.NoRole
                )

                msg_box.setStyleSheet("""
                    QPushButton {
                        font-size: 13px;
                        padding: 5px 15px;
                        min-width: 60px;
                        max-width: 80px;
                        min-height: 20px;
                        max-height: 30px;
                    }
                    QMessageBox {
                        min-width: 300px;
                    }
                """)

                msg_box.exec()

                if msg_box.clickedButton() == yes_button:
                    if is_info_running:
                        self.fetch_controller.cancel()
                    if is_download_running:
                        self.download_controller.cancel()

                    if is_info_running:
                        self.fetch_controller.process.waitForFinished(1000)
                    if is_download_running:
                        self.download_controller.process.waitForFinished(1000)

                    if self.tray_icon:
                        self.tray_icon.hide()
                    logger.info("Application exit — processes stopped")
                    event.accept()
                else:
                    event.ignore()

    def fully_exit_app(self):
        is_info_running = self.fetch_controller.is_running()
        is_download_running = self.download_controller.is_running()

        if is_info_running or is_download_running:
            self.showNormal()
            self.activateWindow()
            self.close()
        else:
            global loaded_settings
            loaded_settings[ConfigKey.MINIMIZE_TO_TRAY] = False
            if self.tray_icon:
                self.tray_icon.hide()
            self.close()
            logger.info("Application fully exited")
            QApplication.quit()

    def on_tray_icon_activated(self, reason):
        if (reason == QSystemTrayIcon.Trigger
                or reason == QSystemTrayIcon.DoubleClick):
            self.showNormal()
            self.activateWindow()

    # =========================================================================
    # Tray
    # =========================================================================
    def setup_tray_icon(self):
        try:
            icon = QIcon(ResourcePath.APP_ICON)
            self.tray_icon = QSystemTrayIcon(icon, self)
            self.tray_icon.setToolTip(CONST.APP_NAME)
            self.tray_icon.show()
        except Exception as e:
            logger.error(f"Error setting up tray icon: {e}")
            self.tray_icon = None

    # =========================================================================
    # Default Thumbnail
    # =========================================================================
    def display_default_thumbnail(self):
        try:
            pixmap = QPixmap(ResourcePath.DEFAULT_THUMBNAIL)
            if not pixmap.isNull():
                mask = QBitmap(pixmap.size())
                mask.fill(Qt.color0)

                painter = QPainter(mask)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(Qt.color1)
                painter.drawRoundedRect(
                    mask.rect(), 30, 30
                )  # 12 က ထောင့်ဝိုင်းချင်တဲ့ Radius ပမာဏပါ
                painter.end()

                scaled_pixmap = pixmap.scaled(
                    340, 190,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.lblThumbnail.setPixmap(scaled_pixmap)
            else:
                self.lblThumbnail.setText("[ Thumbnail Image Not Found ]")
        except Exception as e:
            logger.error(f"Error loading default thumbnail: {e}")
            self.lblThumbnail.setText("[ Load Error ]")

    # =========================================================================
    # Marquee Progressbar
    # =========================================================================
    def marquee_progressbar(self, enable: bool):
        if enable:
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(0)
            self.progressBar.setTextVisible(False)
        else:
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(100)
            self.progressBar.setValue(0)
            self.progressBar.setTextVisible(True)

    # =========================================================================
    # Paste
    # =========================================================================
    def on_paste_clicked(self):
        clipboard = QApplication.clipboard()
        url_regex = re.compile(
            r'^https?://([^/\s]+)(?:/\S*)?$', re.IGNORECASE
        )
        match = re.match(url_regex, clipboard.text())

        if not match:
            return
        self.urlInput.setText(clipboard.text().strip())
        self.on_get_info_clicked()

    def paste_link(self):
        clipboard = QApplication.clipboard()
        url_regex = re.compile(
            r'^https?://([^/\s]+)(?:/\S*)?$', re.IGNORECASE
        )
        match = re.match(url_regex, clipboard.text())

        if not match:
            return
        self.urlInput.setText(clipboard.text().strip())

        if self.fetch_controller.is_running():
            self.statusbar.showMessage(StatusMsg.CANCELLING_FETCH)
            self.getInfoButton.setEnabled(False)
            self.fetch_controller.cancel()
            return
        else:
            self.on_get_info_clicked()

    def on_history_clicked(self):
        history_records = self.db_mgr.get_all_history()

        # db_mgr parameter ပါ ထည့်ပေးလိုက်ပါ
        dialog = HistoryDialog(self, history_records=history_records, db_mgr=self.db_mgr)
        
        if dialog.exec() == QDialog.Accepted:
            selected_url = dialog.get_selected_url()
            if selected_url:
                self.urlInput.setText(selected_url)

    # =========================================================================
    # Settings / About
    # =========================================================================
    def on_Goto_Settings_Clicked(self):
        dialog = SettingsDialog(self.config_mgr, self, initial_tab=3)
        dialog.exec()

    def on_settings_clicked(self):
        if self.clipboard_thread:
            self.clipboard_thread.stop()

        global loaded_settings
        dialog = SettingsDialog(self.config_mgr, self, initial_tab=0)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            loaded_settings = self.config_mgr.get_all()
            self.check_and_toggle_clipboard_monitor()

            # Config ထဲမှ နောက်ဆုံး စာရင်းသွင်းထားသော တန်ဖိုးကို ယူခြင်း
            is_auto_add = self.config_mgr.get("add_links_clipboard", False)
            print(f"Clipboard Monitor is: {is_auto_add}")

            # Tray Menu Action ၏ Checked state ကို Sync လုပ်ခြင်း
            if hasattr(self, 'auto_add_from_clipboard_action'):
                self.auto_add_from_clipboard_action.setChecked(is_auto_add)
                print("hasattr statement is executed.")

            self.statusbar.showMessage(StatusMsg.SETTINGS_SAVED)
            self.statusbar.showMessage(StatusMsg.READY)
            logger.info("Settings updated")

        if hasattr(self, 'check_and_toggle_clipboard_monitor'):
            self.check_and_toggle_clipboard_monitor()
        else:
            if self.clipboard_thread:
                self.clipboard_thread.start()

    def on_about_button_clicked(self):
        about_dialog = ui.about.AboutDialog(self)
        about_dialog.exec()

    # =========================================================================
    # ✨ Phase 4 — ConfigManager သုံး (ရိုးရှင်းအောင်)
    # =========================================================================
    def on_use_mtime_clicked(self):
        """Modify Time toggle — ConfigManager သုံး"""
        self.config_mgr.set(
            ConfigKey.USE_MTIME, self.useMTimeButton.isChecked()
        )

    def update_cookies_config(self, new_path):
        """Cookies path update — ConfigManager သုံး"""
        try:
            windows_path = os.path.normpath(new_path)
            self.config_mgr.set(ConfigKey.COOKIES_PATH, windows_path)
            logger.info("Config updated with new cookies path")
        except Exception as e:
            logger.error(f"Error updating config cookies_path: {e}")

    @staticmethod
    def generate_random_filename(prefix="dl", suffix="filepath",
                                  extension=".txt", random_length=6):
        timestamp = int(time.time() * 1000)
        random_str = ''.join(
            random.choices(
                string.ascii_lowercase + string.digits, k=random_length
            )
        )
        return f"{prefix}_{timestamp}_{random_str}_{suffix}{extension}"

    # =========================================================================
    # ✨ Phase 2 — ThumbnailService signal handlers
    # =========================================================================
    def on_thumbnail_ready(self, pixmap):
        self.thumbnail_success = True
        self.thumbnail_failed = False

        if hasattr(self, "movie") and self.movie:
            self.movie.stop()

        self.lblThumbnail.setMovie(None)
        self.lblThumbnail.clear()
        self.lblThumbnail.repaint()

        scaled_pixmap = ThumbnailService.scale_for_label(pixmap)
        self.lblThumbnail.setPixmap(scaled_pixmap)

        self.statusbar.showMessage("Fetch Info successful. Thumbnail ready.")
        logger.info("Thumbnail ready")

    def on_thumbnail_failed(self, reason):
        self.thumbnail_success = False
        self.thumbnail_failed = True

        if hasattr(self, "movie") and self.movie:
            self.movie.stop()

        self.lblThumbnail.setMovie(None)
        self.display_default_thumbnail()

        self.statusbar.showMessage(
            "Fetch Info successful. Thumbnail download failed."
        )
        logger.warning(f"Thumbnail download failed: {reason}")

    # =========================================================================
    # Save Thumbnail
    # =========================================================================
    def save_thumbnail(self):
        if not hasattr(self, 'info') or not self.info:
            return

        save_dir = loaded_settings.get(ConfigKey.DOWNLOAD_PATH, downloads_dir)

        ThumbnailService.save_thumbnail_dialog(
            parent_widget=self,
            info=self.info,
            default_dir=save_dir,
            status_callback=self.statusbar.showMessage,
        )

    def on_thumbnail_context_menu(self, pos):
        pixmap = self.lblThumbnail.pixmap()
        if not pixmap or pixmap.isNull():
            return

        if not hasattr(self, 'info') or self.info is None:
            return

        context_menu = QMenu(self)
        save_action = context_menu.addAction("Save Thumbnail As...")
        save_action.triggered.connect(self.save_thumbnail)

        context_menu.exec(self.lblThumbnail.mapToGlobal(pos))

    def open_uploader_url(self, event):
        uploader_url = getattr(self, "uploader_url", None)
        if uploader_url:
            QDesktopServices.openUrl(QUrl(uploader_url))

    # =========================================================================
    # ✨ Phase 3 — FetchController signal handlers
    # =========================================================================
    def on_fetch_started(self):
        """FetchController.fetch_started"""
        pass

    def on_fetch_completed(self, info):
        """FetchController.fetch_completed — JSON parse အောင်မြင်ပြီ"""
        self.getInfoButton.setText("Fetch Info")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", False)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()

        if hasattr(self, "movie") and self.movie:
            self.movie.stop()

        self.info = info

        # ⭐ [SQLite] Fetch ရရှိထားသော Video Info နှင့် URL အား Database ထဲသို့ သိမ်းဆည်းခြင်း
        current_url = self.urlInput.text().strip()
        if current_url and isinstance(info, dict):
            self.db_mgr.save_or_update_fetch(current_url, info)

        self.statusbar.showMessage("Video information fetched successfully.")
        logger.info("Fetch completed")

        if self.download_controller.is_running():
            self.set_controls_status(UiState.DOWNLOADING)
        else:
            self.set_controls_status(UiState.FETCHING_FINISHED)

        self.display_video_info()

    def on_fetch_failed(self, error_message):
        """FetchController.fetch_failed"""
        self.getInfoButton.setText("Fetch Info")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", False)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()

        if hasattr(self, "movie") and self.movie:
            self.movie.stop()

        self.statusbar.showMessage(StatusMsg.FETCH_FAILED)
        self.lblThumbnail.setMovie(None)
        self.display_default_thumbnail()

        if error_message:
            self.txtInfoLog.setPlainText(error_message)

        logger.error(f"Fetch failed: {error_message}")

        if not self.download_controller.is_running():
            self.set_controls_status(UiState.FETCHING_ERROR)
        else:
            self.set_controls_status(UiState.DOWNLOADING)

        self.taskbar_service.reset()
        self.taskbar_service.set_error(0, 100, "error")

    def on_fetch_cancelled(self):
        """FetchController.fetch_cancelled"""
        self.getInfoButton.setText("Fetch Info")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", False)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()

        self.lblThumbnail.setMovie(None)
        self.display_default_thumbnail()
        self.statusbar.showMessage(StatusMsg.FETCH_CANCELLED)
        logger.info("Fetch cancelled by user")

        if not self.download_controller.is_running():
            self.set_controls_status(UiState.FETCHING_ERROR)
        else:
            self.set_controls_status(UiState.DOWNLOADING)

        self.taskbar_service.reset()

    def on_fetch_cookies_required(self):
        """FetchController.cookies_required"""
        self.getInfoButton.setText("Fetch Info")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", False)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()

        self.lblThumbnail.setMovie(None)
        self.display_default_thumbnail()

        logger.warning("Cookies required — showing dialog")

        if not self.download_controller.is_running():
            self.set_controls_status(UiState.FETCHING_ERROR)
        else:
            self.set_controls_status(UiState.DOWNLOADING)

        self.taskbar_service.reset()
        self.show_cookies_required_dialog()

    # =========================================================================
    # ✨ Phase 3 — DownloadController signal handlers
    # =========================================================================
    def on_download_started(self):
        """DownloadController.download_started"""
        pass

    def on_download_log(self, log_text):
        """DownloadController.download_log"""
        self.txtInfoLog.insertPlainText(log_text)
        self.txtInfoLog.ensureCursorVisible()

    def on_download_destination_changed(self, path):
        """DownloadController.download_destination_changed"""
        self.final_downloaded_path = path
        self.taskbar_service.reset()
        self.taskbar_service.set_downloading(0, 100, "downloading")
        logger.debug(f"Download destination: {path}")

    def on_download_progress(self, percent, status_text):
        """DownloadController.download_progress"""
        if self.is_marquee:
            self.marquee_progressbar(False)
            self.is_marquee = False
            
        self.progressBar.setValue(percent)
        self.statusbar.showMessage(status_text)
        self.taskbar_service.set_downloading(percent, 100, "downloading")

    def on_download_indeterminate(self):
        """DownloadController.download_indeterminate"""
        if not self.is_marquee:
            self.marquee_progressbar(True)
            self.is_marquee = True
        self.taskbar_service.reset()
        self.taskbar_service.set_indeterminate()

    def on_download_progress_resumed(self):
        """DownloadController.download_progress_resumed — marquee ရပ်"""
        if self.is_marquee:
            self.marquee_progressbar(False)
            self.is_marquee = False

    def on_download_completed(self, final_path):
        """DownloadController.download_completed"""
        self.final_downloaded_path = final_path

        # ⭐ [SQLite] Download Success ဖြစ်ကြောင်း DB ထဲမှာ Status Update လုပ်ခြင်း
        current_url = self.urlInput.text().strip()
        if current_url:
            self.db_mgr.update_download_status(
                url=current_url, 
                status="Completed", 
                file_path=final_path
            )

        self.progressBar.setValue(100)
        self.set_controls_status(UiState.NORMAL)
        self.downloadButton.setText("Download")
        self.progressBar.setVisible(False)

        if self.is_marquee:
            self.marquee_progressbar(False)
            self.is_marquee = False

        self.taskbar_service.reset()
        self.taskbar_service.set_completed("completed")

        self.downloadButton.setProperty("working", False)
        self.downloadButton.style().unpolish(self.downloadButton)
        self.downloadButton.style().polish(self.downloadButton)
        self.downloadButton.update()

        if self.awake_mode:
            self.awake_mode.__exit__(None, None, None)
            self.awake_mode = None

        self.txtInfoLog.clear()
        self.txtInfoLog.setHtml(description_to_html(self.original_description))

        self.statusbar.showMessage(StatusMsg.DOWNLOAD_COMPLETED)
        logger.info(f"Download completed: {final_path}")

        video_title = self.lblTitle.text() or "Video"

        if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_COMPLETED):
            self.notification_service.notify_download_completed(video_title)

        if loaded_settings.get(ConfigKey.PLAY_AFTER_DOWNLOADED):
            if self.final_downloaded_path:
                url = QUrl.fromLocalFile(self.final_downloaded_path)
                success = QDesktopServices.openUrl(url)
                if not success:
                    logger.warning(
                        f"Play failed: {self.final_downloaded_path} not found"
                    )

    def on_download_failed(self, error_message):
        """DownloadController.download_failed"""
        # ⭐ [SQLite] Download Error ဖြစ်ကြောင်း DB ထဲမှာ Status Update လုပ်ခြင်း
        current_url = self.urlInput.text().strip()
        if current_url:
            self.db_mgr.update_download_status(
                url=current_url, 
                status="Error", 
                error_msg=error_message
            )

        self.progressBar.setValue(100)
        self.set_controls_status(UiState.NORMAL)
        self.downloadButton.setText("Download")
        self.progressBar.setVisible(False)

        if self.is_marquee:
            self.marquee_progressbar(False)
            self.is_marquee = False

        self.taskbar_service.reset()
        self.taskbar_service.set_error(0, 100, "error")

        self.downloadButton.setProperty("working", False)
        self.downloadButton.style().unpolish(self.downloadButton)
        self.downloadButton.style().polish(self.downloadButton)
        self.downloadButton.update()

        if self.awake_mode:
            self.awake_mode.__exit__(None, None, None)
            self.awake_mode = None

        if self.statusbar.currentMessage() != StatusMsg.DOWNLOAD_CANCELLED:
            self.statusbar.showMessage(StatusMsg.DOWNLOAD_FAILED)
            self.txtInfoLog.clear()
            self.txtInfoLog.insertPlainText(error_message)
            logger.error(f"Download failed: {error_message}")

    def on_download_cancelled(self):
        """DownloadController.download_cancelled"""
        # ⭐ [SQLite] User ဘက်မှ Download ကို မပြီးမီ Cancel လုပ်လိုက်ကြောင်း Update လုပ်ခြင်း
        current_url = self.urlInput.text().strip()
        if current_url:
            self.db_mgr.update_download_status(
                url=current_url, 
                status="Cancelled"
            )

        self.set_controls_status(UiState.NORMAL)
        self.downloadButton.setText("Download")
        self.progressBar.setVisible(False)

        if self.is_marquee:
            self.marquee_progressbar(False)
            self.is_marquee = False

        self.taskbar_service.reset()

        self.downloadButton.setProperty("working", False)
        self.downloadButton.style().unpolish(self.downloadButton)
        self.downloadButton.style().polish(self.downloadButton)
        self.downloadButton.update()

        if self.awake_mode:
            self.awake_mode.__exit__(None, None, None)
            self.awake_mode = None

        self.txtInfoLog.clear()
        self.txtInfoLog.setHtml(description_to_html(self.original_description))
        self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
        logger.info("Download cancelled by user")

    # =========================================================================
    # FETCH INFO
    # =========================================================================
    def show_cookies_required_dialog(self):
        self.statusbar.showMessage("Cookies Verification Required")

        if getattr(self, 'clipboard_thread', None):
            self.clipboard_thread.stop()

        if not self.download_controller.is_running():
            self.set_controls_status(UiState.FETCHING_ERROR)

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Cookies Verification Required")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText("<b>Requires Authentication / Cookies Verification</b>")
        msg_box.setInformativeText(
            "This video cannot be accessed because its requesting browser cookies "
            "to verify you are not a bot, or the video has age restrictions.\n\n"
            "💡 How to fix:\n"
            "Go to Settings -> Click Cookies Tab and configure your browser cookies "
            "or cookies file path to fix this error.\n \n"
            "If you need cookies exporter, use "
            "<a href=\"https://github.com/yawstar/cookie-exporter\">"
            "YawStar Cookies Exporter</a>."
        )

        # Corrected: TextInteractionFlags တွင် Interaction Flag ကိုသာ ထည့်သွင်းပေးရပါမည်
        msg_box.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )

        for label in msg_box.findChildren(QLabel):
            label.setOpenExternalLinks(True)

        settings_button = msg_box.addButton(
            "Go to Settings", QMessageBox.ButtonRole.ActionRole
        )
        msg_box.addButton(QMessageBox.StandardButton.Close)

        msg_box.exec()

        if hasattr(self, 'check_and_toggle_clipboard_monitor'):
            self.check_and_toggle_clipboard_monitor()
        elif getattr(self, 'clipboard_thread', None):
            self.clipboard_thread.start()

        if msg_box.clickedButton() == settings_button:
            self.on_Goto_Settings_Clicked()
            
    def on_get_info_clicked(self):
        """Fetch Info — FetchController ကို delegate"""
        self.stop_tips_rotation()

        # Stop fetching
        if self.fetch_controller.is_running():
            self.statusbar.showMessage(StatusMsg.CANCELLING_FETCH)
            self.getInfoButton.setEnabled(False)
            self.fetch_controller.cancel()
            return

        # Dependencies check
        dpc_check = self.check_necessary_files()
        if dpc_check[0] != 0:
            logger.warning(f"Missing dependencies: {dpc_check[0]}")
            self.statusbar.showMessage("Need dependencies files...")
            self.open_dep_downloader()

            loop = QEventLoop()
            self.dep_window.destroyed.connect(loop.quit)
            loop.exec()

            dpc_check_after = self.check_necessary_files()
            if dpc_check_after[0] == 0:
                self.statusbar.showMessage(StatusMsg.READY)
            else:
                self.statusbar.showMessage(
                    "Dependencies download incomplete or failed!"
                )
                self.display_default_thumbnail()
                self.set_controls_status(UiState.FETCHING_ERROR)
                return
        else:
            self.statusbar.showMessage(StatusMsg.READY)

        url = self.urlInput.text().strip()
        if not url:
            self.statusbar.showMessage("Please enter a valid URL.")
            return

        # State Reset
        self.fetch_cancelled = False
        self.cookies_error_detected = False
        self.info_buffer = ""
        self.info_output = ""
        self.info_error_output = ""
        self.info = None
        self.original_description = ""
        self.loaded_settings = {}

        # Thumbnail Reset
        self.thumbnail_request_id = (
            getattr(self, "thumbnail_request_id", 0) + 1
        )
        self.thumbnail_reply = None
        self.thumbnail_success = False
        self.thumbnail_failed = False
        self.thumbnail_timeout_timer = None

        # UI Reset
        self.lblTitle.setText("")
        self.lblDurationVal.setText("")
        self.lblChaptersVal.setText("")
        self.lblUploaderVal.setText("")
        self.lblUploadDateVal.setText("")

        if not self.download_controller.is_running():
            self.txtInfoLog.clear()
            # Taskbar
            self.taskbar_service.reset()
            self.taskbar_service.set_indeterminate("waiting")

        # Select Formats Reset
        self.selectFormatsButton.setText("Formats")
        self.selectFormatsButton.setProperty("selected", False)
        self.selectFormatsButton.style().unpolish(self.selectFormatsButton)
        self.selectFormatsButton.style().polish(self.selectFormatsButton)
        self.selectFormatsButton.update()
        self.selected_format_id = None

        # Controls
        if not self.download_controller.is_running():
            self.set_controls_status(UiState.FETCHING)

        self.getInfoButton.setText("Stop Fetching")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", True)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()

        # self.paste_link_action.setEnabled(False)

        # Loading GIF
        gif_path = ResourcePath.LOADING_GIF

        if hasattr(self, "movie") and self.movie:
            self.movie.stop()

        self.movie = QMovie(gif_path)

        if self.movie.isValid():
            self.lblThumbnail.setPixmap(QPixmap())
            self.lblThumbnail.setScaledContents(False)
            self.movie.jumpToFrame(0)

            original_size = self.movie.frameRect().size()
            if original_size.height() > 0:
                scale_factor = 0.7
                target_h = int(self.lblThumbnail.height() * scale_factor)
                aspect_ratio = original_size.width() / original_size.height()
                target_w = int(target_h * aspect_ratio)
                self.movie.setScaledSize(QSize(target_w, target_h))
            else:
                self.movie.setScaledSize(QSize(64, 64))

            self.lblThumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lblThumbnail.setMovie(self.movie)
            self.movie.start()
        else:
            self.lblThumbnail.setMovie(None)
            self.lblThumbnail.setText("Fetching data...")

        # Config
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as file:
                loaded_settings = json.load(file)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            loaded_settings = {}

        loaded_settings[ConfigKey.LAST_ADDED_URL] = url

        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as file:
                json.dump(loaded_settings, file, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

        self.loaded_settings = loaded_settings

        # yt-dlp path check
        yt_dlp_path = self.yt_dlp_service.yt_dlp_path
        if not os.path.exists(yt_dlp_path):
            self.statusbar.showMessage("yt-dlp executable not found.")
            logger.error("yt-dlp not found")
            if hasattr(self, "movie") and self.movie:
                self.movie.stop()
            self.lblThumbnail.setMovie(None)
            self.display_default_thumbnail()
            self.set_controls_status(UiState.FETCHING_ERROR)
            self.getInfoButton.setText("Fetch Info")
            self.getInfoButton.setProperty("working", False)
            self.getInfoButton.style().unpolish(self.getInfoButton)
            self.getInfoButton.style().polish(self.getInfoButton)
            self.getInfoButton.update()
            self.taskbar_service.reset()
            return

        self.statusbar.showMessage(StatusMsg.FETCHING)
        logger.info(f"Fetching: {url}")

        # ✨ Controller start
        self.fetch_controller.start(url, loaded_settings)

    # =========================================================================
    # Display Video Info
    # =========================================================================
    def display_video_info(self):
        try:
            info = self.info
            

            if not isinstance(info, dict):
                raise ValueError("Video information is not valid.")

            # =========================================================
            # 📁 JSON File အဖြစ် Save လုပ်ရန် ထည့်သွင်းရမည့် Code Portion
            # =========================================================
            # try:
            #     # File name ကို Title သို့မဟုတ် Fixed Name အဖြစ် သတ်မှတ်နိုင်ပါတယ်
            #     file_name = "video_info.json"
                
            #     with open(file_name, "w", encoding="utf-8") as f:
            #         # ensure_ascii=False က မြန်မာစာ သို့မဟုတ် အခြား Language စာလုံးများ မပျက်စီးအောင် ထိန်းပေးပါတယ်
            #         # indent=4 က JSON format ကို ဖတ်ရလွယ်အောင် လှပစွာ စီပေးပါတယ်
            #         json.dump(info, f, ensure_ascii=False, indent=4)
            # except Exception as save_err:
            #     logger.warning(f"Failed to save info as JSON: {save_err}")
            # =========================================================

            # Title
            fullTitleStr = info.get(
                "fulltitle", info.get("title", "Unknown Title")
            )
            if not isinstance(fullTitleStr, str):
                fullTitleStr = str(fullTitleStr)

            if len(fullTitleStr) >= 80:
                self.lblTitle.setText(fullTitleStr[:80])
            else:
                self.lblTitle.setText(fullTitleStr)

            # Duration
            duration_secs = info.get("duration") or 0
            try:
                seconds = int(duration_secs)
            except (TypeError, ValueError):
                seconds = 0

            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            if hours > 0:
                self.lblDurationVal.setText(
                    f"{hours}:{minutes:02d}:{seconds:02d}"
                )
            else:
                self.lblDurationVal.setText(f"{minutes}:{seconds:02d}")

            # Live
            is_Live = info.get("is_live", False)
            if is_Live:
                self.lblDurationVal.setText("🔴 LIVE")
                self.downloadButton.setEnabled(False)
            else:
                self.downloadButton.setEnabled(True)

            # Chapters
            chapters = info.get("chapters") or []
            if len(chapters) < 1:
                self.lblChaptersVal.setText("None")
            else:
                self.lblChaptersVal.setText(str(len(chapters)))

            # Uploader
            uploader = (
                info.get("uploader") or info.get("channel") or "Unknown"
            )
            self.uploader_url = (
                info.get("uploader_url") or info.get("channel_url")
            )

            self.lblUploaderVal.setText(str(uploader))

            if self.uploader_url:
                self.lblUploaderVal.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )
                self.lblUploaderVal.setToolTip(
                    f"Open link: {self.uploader_url}"
                )
                self.lblUploaderVal.setStyleSheet("""
                    QLabel:hover {
                        color: #3498db;
                        text-decoration: underline;
                    }
                """)
            else:
                self.lblUploaderVal.setCursor(Qt.CursorShape.ArrowCursor)
                self.lblUploaderVal.setToolTip("")
                self.lblUploaderVal.setStyleSheet("")

            # Upload Date
            upload_date = info.get("upload_date", "Unknown")
            if (isinstance(upload_date, str)
                    and len(upload_date) == 8
                    and upload_date.isdigit()):
                upload_date = (
                    f"{upload_date[:4]}-{upload_date[4:6]}-"
                    f"{upload_date[6:]}"
                )

            self.lblUploadDateVal.setText(str(upload_date))

            # Description
            desc_text = (
                info.get("description", "No description available.")
                or "No description available."
            )
            html_text = description_to_html(desc_text)
            self.txtInfoLog.setHtml(html_text)
            self.original_description = str(desc_text)

            # Thumbnail
            self.thumbnail_success = False
            self.thumbnail_failed = False
            thumbnail_url = info.get("thumbnail")

            if thumbnail_url:
                thumbnail_url = str(thumbnail_url)
                current_request_id = getattr(
                    self, "thumbnail_request_id", 0
                )
                self.thumbnail_service.request(
                    thumbnail_url, current_request_id
                )
            else:
                self.thumbnail_success = False
                self.thumbnail_failed = True

                if hasattr(self, "movie") and self.movie:
                    self.movie.stop()

                self.lblThumbnail.setMovie(None)
                self.display_default_thumbnail()
                self.statusbar.showMessage(
                    "Fetch Info successful. Thumbnail is not available."
                )

            # Taskbar Reset
            self.taskbar_service.reset()

            # self.paste_link_action.setEnabled(True)

            loaded_settings = getattr(self, "loaded_settings", {})

            # Notification
            if (loaded_settings.get(ConfigKey.NOTIFY_FETCHED)
                    and not loaded_settings.get(ConfigKey.AUTO_START_DOWNLOAD)):
                video_title = self.lblTitle.text()
                self.notification_service.notify_fetch_completed(video_title)

            # Auto Download
            if loaded_settings.get(ConfigKey.AUTO_START_DOWNLOAD):
                if not self.download_controller.is_running():
                    self.on_download_clicked()


        except Exception as e:
            error_message = "Error displaying video information: " + str(e)
            logger.exception(error_message)
            self.txtInfoLog.setPlainText(error_message)
            self.statusbar.showMessage(
                "Failed to display video information."
            )

            if hasattr(self, "movie") and self.movie:
                self.movie.stop()

            self.lblThumbnail.setMovie(None)
            self.display_default_thumbnail()

            if not self.download_controller.is_running():
                self.set_controls_status(UiState.FETCHING_ERROR)

            self.taskbar_service.reset()
            # self.paste_link_action.setEnabled(True)

    # =========================================================================
    # FORMAT SELECTION
    # =========================================================================
    def on_select_formats_clicked(self):
        if self.info is None:
            self.statusbar.showMessage(
                "No video information available. Please fetch info first."
            )
            return

        current_id = getattr(self, 'selected_format_id', None)
        dialog = FormatDialog(
            self.info, current_format_id=current_id, parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            chosen_id = dialog.get_selected_format_id()

            if chosen_id:
                self.selected_format_id = chosen_id
                self.selectFormatsButton.setText("Formats")
                self.selectFormatsButton.setProperty("selected", True)
                self.selectFormatsButton.style().unpolish(
                    self.selectFormatsButton
                )
                self.selectFormatsButton.style().polish(
                    self.selectFormatsButton
                )
                self.selectFormatsButton.update()
                self.statusbar.showMessage(
                    f"Selected Format ID: {chosen_id}"
                )
                logger.info(f"Format selected: {chosen_id}")
            else:
                self.selectFormatsButton.setText("Formats")
                self.selectFormatsButton.setProperty("selected", False)
                self.selectFormatsButton.style().unpolish(
                    self.selectFormatsButton
                )
                self.selectFormatsButton.style().polish(
                    self.selectFormatsButton
                )
                self.selectFormatsButton.update()
                self.selected_format_id = chosen_id = None
                self.statusbar.showMessage(
                    "Default prefered Format selection."
                )
        else:
            self.statusbar.showMessage("Format selection cancelled.")

    # =========================================================================
    # DOWNLOAD
    # =========================================================================
    def on_download_clicked(self):
        """Download — DownloadController ကို delegate"""
        self.stop_tips_rotation()

        # Stop download
        if self.download_controller.is_running():
            self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
            self.download_controller.cancel()
            return

        url = self.urlInput.text().strip()
        if not url:
            self.statusbar.showMessage("Please enter a valid URL.")
            return

        # Dependencies
        dpc_check = window.check_necessary_files()
        if dpc_check[0] != 0:
            logger.warning(f"Missing dependencies: {dpc_check[0]}")
            window.statusbar.showMessage("Need dependencies files...")
            window.open_dep_downloader()

            loop = QEventLoop()
            window.dep_window.destroyed.connect(loop.quit)
            loop.exec()

            dpc_check_after = window.check_necessary_files()
            if dpc_check_after[0] == 0:
                window.statusbar.showMessage(StatusMsg.READY)
            else:
                window.statusbar.showMessage(
                    "Dependencies download incomplete or failed!"
                )
        else:
            window.statusbar.showMessage(StatusMsg.READY)

        # Config
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            loaded_settings = json.load(file)

        prevent_sleep_while_dloading = loaded_settings.get(
            ConfigKey.AWAKE_MODE, False
        )
        download_path_cfg = loaded_settings.get(
            ConfigKey.DOWNLOAD_PATH,
            os.path.join(downloads_dir, 'YS U-Tube Downloader')
        )

        # GUI override
        embedded_thumbnail = self.embThumbnailButton.isChecked()
        embedded_chapters = self.embChaptersButton.isChecked()
        embedded_subtitle = self.embSubtitlesButton.isChecked()
        embedded_metadata = self.embMetadataButton.isChecked()
        use_mtime = self.useMTimeButton.isChecked()

        # Awake mode
        if prevent_sleep_while_dloading:
            self.awake_mode = keep.running()
            self.awake_mode.__enter__()

        updated_data = {
            ConfigKey.USE_MTIME: use_mtime,
            ConfigKey.EMBED_THUMBNAIL: embedded_thumbnail,
            ConfigKey.EMBED_SUBTITLES: embedded_subtitle,
            ConfigKey.EMBED_CHAPTERS: embedded_chapters,
            ConfigKey.EMBED_METADATA: embedded_metadata,
        }
        self.config_mgr.update_multiple(updated_data)

        if not os.path.exists(download_path_cfg):
            os.makedirs(download_path_cfg)

        gui_overrides = {
            "embed_thumbnail": embedded_thumbnail,
            "embed_chapters": embedded_chapters,
            "embed_subtitles": embedded_subtitle,
            "embed_metadata": embedded_metadata,
            "use_mtime": use_mtime,
        }

        # UI state
        self.set_controls_status(UiState.DOWNLOADING)
        self.downloadButton.setText("Stop Download")
        self.progressBar.setValue(0)
        self.statusbar.showMessage(StatusMsg.DOWNLOAD_PREPARING)

        self.progressBar.setVisible(True)
        if not self.is_marquee:
            self.marquee_progressbar(True)
            self.is_marquee = True

        self.txtInfoLog.clear()

        self.downloadButton.setProperty("working", True)
        self.downloadButton.style().unpolish(self.downloadButton)
        self.downloadButton.style().polish(self.downloadButton)
        self.downloadButton.update()

        # Notification
        if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_STARTED):
            self.notification_service.notify_download_started()

        # Taskbar
        self.taskbar_service.reset()
        self.taskbar_service.set_indeterminate()

        self.txtInfoLog.insertPlainText(
            "✦-------------------- Download Process Started "
            "--------------------✦\n"
        )
        self.txtInfoLog.ensureCursorVisible()

        logger.info(f"Download started: {url}")

        # ✨ Controller start
        self.download_controller.start(
            url=url,
            settings=loaded_settings,
            selected_format_id=self.selected_format_id,
            gui_overrides=gui_overrides,
            is_windows=(CURRENT_OS == "Windows"),
        )

    # =========================================================================
    # ✨ Phase 4 — OPEN FOLDER (FileOpenerService ကို delegate)
    # =========================================================================
    def open_downloaded_folder(self):
        """
        Open Download Folder — FileOpenerService ကို delegate။

        File ရှိရင် → folder ဖွင့်ပြီး file highlight
        File မရှိရင် → download folder ဖွင့်
        """
        # File ရှိရင် select လုပ်
        if (hasattr(self, 'final_downloaded_path')
                and self.final_downloaded_path
                and os.path.exists(self.final_downloaded_path)):
            FileOpenerService.open_folder_and_select_file(
                self.final_downloaded_path
            )
            return

        # File မရှိရင် folder ဖွင့်
        folder_path = loaded_settings.get(ConfigKey.DOWNLOAD_PATH, '')
        FileOpenerService.open_folder(folder_path)

    def on_notification_clicked(self):
        self.open_downloaded_folder()

    # =========================================================================
    # CONTROL STATES
    # =========================================================================
    def set_controls_status(self, method: str):
        if method == UiState.DOWNLOADING:
            self.show_option_controls_status(False)
            self.urlInput.setEnabled(True)
            self.pasteButton.setEnabled(True)
            self.historyButton.setEnabled(True)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(False)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(True)
        elif method == UiState.FETCHING:
            self.show_option_controls_status(False)
            self.urlInput.setEnabled(False)
            self.pasteButton.setEnabled(False)
            self.historyButton.setEnabled(False)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(False)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(False)
        elif method == UiState.FETCHING_ERROR:
            self.show_option_controls_status(False)
            self.urlInput.setEnabled(True)
            self.pasteButton.setEnabled(True)
            self.historyButton.setEnabled(True)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(False)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(False)
        elif method == UiState.FETCHING_FINISHED:
            self.show_option_controls_status(True)
            self.urlInput.setEnabled(True)
            self.pasteButton.setEnabled(True)
            self.historyButton.setEnabled(True)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(True)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(True)
        else:
            self.show_option_controls_status(True)
            self.urlInput.setEnabled(True)
            self.pasteButton.setEnabled(True)
            self.historyButton.setEnabled(True)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(True)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(True)

        self.selectFormatsButton.update()

    def on_open_folder_clicked(self):
        self.open_downloaded_folder()

    def show_option_controls_status(self, status: bool):
        if status:
            self.embThumbnailButton.setVisible(True)
            self.embSubtitlesButton.setVisible(True)
            self.embChaptersButton.setVisible(True)
            self.embMetadataButton.setVisible(True)
            self.useMTimeButton.setVisible(True)
        else:
            self.embThumbnailButton.setVisible(False)
            self.embSubtitlesButton.setVisible(False)
            self.embChaptersButton.setVisible(False)
            self.embMetadataButton.setVisible(False)
            self.useMTimeButton.setVisible(False)

    # =========================================================================
    # CLIPBOARD MONITOR
    # =========================================================================
    def check_and_toggle_clipboard_monitor(self):
        global loaded_settings
        is_auto_clipboard = loaded_settings.get(
            ConfigKey.ADD_LINKS_CLIPBOARD, False
        )

        if hasattr(self, 'auto_add_from_clipboard_action'):
            self.auto_add_from_clipboard_action.blockSignals(True)
            self.auto_add_from_clipboard_action.setChecked(is_auto_clipboard)
            self.auto_add_from_clipboard_action.blockSignals(False)

        if is_auto_clipboard:
            if self.clipboard_thread is None:
                self.clipboard_thread = ClipboardMonitor(self)
                self.clipboard_thread.url_captured.connect(
                    self.on_clipboard_url_captured
                )
                self.clipboard_thread.start()
                self.statusbar.showMessage("Clipboard Monitor: [ON]")
                logger.info("Clipboard monitor ON")
            else:
                self.clipboard_thread.start()
        else:
            if self.clipboard_thread:
                self.clipboard_thread.stop()
                self.clipboard_thread = None
                self.statusbar.showMessage("Clipboard Monitor: [OFF]")
                logger.info("Clipboard monitor OFF")

    def on_clipboard_url_captured(self, captured_url):
        if self.urlInput.text().strip() != captured_url:
            if not self.fetch_controller.is_running():
                self.urlInput.setText(captured_url)
                self.statusbar.showMessage(
                    f"Captured link from clipboard: {captured_url}"
                )
                logger.info(f"Clipboard captured: {captured_url}")
                self.on_get_info_clicked()
            else:
                logger.warning(
                    "Fetching already running — clipboard URL ignored"
                )
                if self.clipboard_thread:
                    self.clipboard_thread.last_clipboard_content = ""

    def on_toggle_clipboard_action(self):
        # Tray Menu action ရဲ့ checked state (True/False) ကို ယူခြင်း
        sender = self.sender()
        is_checked = sender.isChecked() if sender else False

        # Config မှာ တန်ဖိုး Update လုပ်ပြီး သိမ်းဆည်းခြင်း
        self.config_mgr.set(ConfigKey.ADD_LINKS_CLIPBOARD, is_checked)
        
        # global loaded_settings ကိုလည်း Update လုပ်ခြင်း
        global loaded_settings
        loaded_settings[ConfigKey.ADD_LINKS_CLIPBOARD] = is_checked

        # Clipboard Monitor thread ကို ချက်ချင်း Toggle (ON/OFF) လုပ်ပေးခြင်း
        self.check_and_toggle_clipboard_monitor()
        logger.info(f"Auto add clipboard toggled: {is_checked}")


class HistoryItemWidget(QWidget):
    def __init__(self, title, url, status, on_delete_callback, parent=None):
        super().__init__(parent)
        self.url = url
        self.on_delete_callback = on_delete_callback

        # Main Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # Left Side Layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 10pt; font-weight: bold; color: #ffffff;")
        
        status_str = f" <span style='color: #00A2FF;'>[{status}]</span>" if status else ""
        self.lbl_url = QLabel(f"{url}{status_str}")
        self.lbl_url.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_url.setStyleSheet("font-size: 8.5pt; color: #888888;")

        info_layout.addWidget(self.lbl_title)
        info_layout.addWidget(self.lbl_url)

        layout.addLayout(info_layout, stretch=1)

        # ⭐ QPushButton အစား QToolButton သုံးခြင်း
        self.btn_delete = QToolButton(self)
        self.btn_delete.setText("✕")
        self.btn_delete.setFixedSize(24, 24)
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.setToolTip("Delete item")
        
        # Style ပြင်ဆင်ခြင်း
        self.btn_delete.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: #A0A0A0;
                border: none;
                font-size: 12pt;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #D34507;
                color: #FFFFFF;
                border-radius: 12px;
            }
        """)
        
        self.btn_delete.hide()
        self.btn_delete.clicked.connect(self.on_delete_clicked)

        layout.addWidget(self.btn_delete, alignment=Qt.AlignmentFlag.AlignVCenter)

    def enterEvent(self, event):
        self.btn_delete.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_delete.hide()
        super().leaveEvent(event)

    def on_delete_clicked(self):
        if self.on_delete_callback:
            self.on_delete_callback(self.url)


class HistoryDialog(QDialog):
    def __init__(self, parent=None, history_records=None, db_mgr=None):
        super().__init__(parent)
        self.ui = Ui_HistoryDialog()
        self.ui.setupUi(self)

        self.db_mgr = db_mgr
        self.selected_url = ""

        if history_records:
            self.load_history(history_records)

        # Signals
        self.ui.txtSearch.textChanged.connect(self.filter_history)
        self.ui.btnSelect.clicked.connect(self.accept_selection)
        self.ui.btnCancel.clicked.connect(self.reject)
        self.ui.btnClearHistory.clicked.connect(self.clear_all_history)
        self.ui.listHistory.itemDoubleClicked.connect(self.accept_selection)

    def load_history(self, records):
        self.ui.listHistory.clear()
        
        for record in records:
            url = record[0] if len(record) > 0 else ""
            title = record[1] if len(record) > 1 and record[1] else "No Title"
            status = record[2] if len(record) > 2 and record[2] else ""
            
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 50))
            
            # UserRole ထဲတွင် Search အတွက် Data သိမ်းဆည်းခြင်း
            item.setData(Qt.ItemDataRole.UserRole, url)
            item.setData(Qt.ItemDataRole.UserRole + 1, f"{title} {url}")
            
            # Custom Item Widget ထည့်သွင်းခြင်း
            item_widget = HistoryItemWidget(
                title=title, 
                url=url, 
                status=status, 
                on_delete_callback=self.delete_single_item
            )
            
            self.ui.listHistory.addItem(item)
            self.ui.listHistory.setItemWidget(item, item_widget)

    def delete_single_item(self, url):
        """တစ်ခုချင်းစီ ဖျက်သည့် Function"""
        # 1. Database မှ ဖျက်ခြင်း (db_mgr ရှိပါက)
        if self.db_mgr and hasattr(self.db_mgr, 'delete_history_by_url'):
            self.db_mgr.delete_history_by_url(url)

        # 2. UI ListWidget မှ ဖျက်ခြင်း
        for i in range(self.ui.listHistory.count()):
            item = self.ui.listHistory.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == url:
                self.ui.listHistory.takeItem(i)
                break

    def clear_all_history(self):
        """History အားလုံးကို ဖျက်ခြင်း"""
        if self.ui.listHistory.count() == 0:
            return

        reply = QMessageBox.question(
            self, "Clear History", "Are you sure you want to clear all history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_mgr and hasattr(self.db_mgr, 'clear_all_history'):
                self.db_mgr.clear_all_history()
            self.ui.listHistory.clear()

    def filter_history(self, text):
        search_text = text.lower()
        for i in range(self.ui.listHistory.count()):
            item = self.ui.listHistory.item(i)
            search_data = item.data(Qt.ItemDataRole.UserRole + 1) or ""
            item.setHidden(search_text not in search_data.lower())

    def accept_selection(self):
        selected_item = self.ui.listHistory.currentItem()
        if selected_item:
            self.selected_url = selected_item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def get_selected_url(self):
        return self.selected_url

# ============================================================================
# Global Exception Hook — ✨ Phase 5A
# ============================================================================
def global_exception_hook(exc_type, exc_value, exc_traceback):
    """Uncaught exceptions ကို log လုပ်ပြီး crash မဖြစ်စေရန်"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


if __name__ == "__main__":
    # Install exception hook
    sys.excepthook = global_exception_hook

    app = SingletonApplication(sys.argv, APP_ID)

    if not app.is_primary_instance():
        logger.info("Secondary instance detected — exiting")
        sys.exit(0)

    
    # Font load
    FONT_RESOURCES = [
        ":/fonts/fonts/pyidaungsu.ttf",
        ":/fonts/fonts/yawstar_ui.ttf",
        ":/fonts/fonts/zawgyione2008.ttf",
    ]
    FontService.load_resource_fonts(FONT_RESOURCES)

    # App default font
    myanmar_family = FontService.get_family(
        ":/fonts/fonts/pyidaungsu.ttf", fallback="sans-serif"
    )
    app.setFont(QFont(myanmar_family, 10))
    # main.py — Font load ပြီးတာနဲ့
    
    FontService.load_resource_fonts(FONT_RESOURCES)

    window = MainWindow()
    window.show()

    def restore_and_raise():
        if window.isMinimized():
            window.showNormal()
        window.show()
        window.activateWindow()
        window.raise_()

    app.activationRequested.connect(restore_and_raise)

    # Dependencies check at startup
    dpc_check = window.check_necessary_files()

    if dpc_check[0] != 0:
        logger.warning(f"Missing dependencies at startup: {dpc_check[0]}")
        window.statusbar.showMessage("Need dependencies files...")
        window.open_dep_downloader()

        loop = QEventLoop()
        window.dep_window.destroyed.connect(loop.quit)
        loop.exec()

        dpc_check_after = window.check_necessary_files()
        if dpc_check_after[0] == 0:
            window.statusbar.showMessage(StatusMsg.READY)
        else:
            window.statusbar.showMessage(
                "Dependencies download incomplete or failed!"
            )
    else:
        window.statusbar.showMessage(StatusMsg.READY)

    if is_first_launch:
        QTimer.singleShot(100, window.on_about_button_clicked)

    logger.info("Entering Qt event loop")
    exit_code = app.exec()
    logger.info(f"Application exited with code {exit_code}")
    sys.exit(exit_code)