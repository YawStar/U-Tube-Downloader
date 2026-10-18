# AppName = YawStar U-Tube Downloader
# Author = YawHackka (YawStar)
# main.py

import sys
import os
import re
import platform
import subprocess
import json
import tempfile
import requests

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsBlurEffect,
    QListWidgetItem,
    QMainWindow,
    QSystemTrayIcon,
    QMessageBox,
    QDialog,
    QMenu,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import (
    QByteArray,
    QEventLoop,
    QProcess,
    QRect,
    Qt,
    QSize,
    QStandardPaths,
    QCoreApplication,
    QUrl,
    QTimer,
    QEvent,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QGuiApplication,
    QImage,
    QPainterPath,
    QPen,
    QPixmap,
    QMovie,
    QIcon,
    QFont,
    QBitmap,
    QPainter,
    QCursor,
    QShortcut,
    QKeySequence,
)

from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy

from wakepy import keep

from pymediainfo import MediaInfo

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
from ui.history_dialog import Ui_HistoryDialog

# Modern Update Dialog
from ui.update_dialog import ModernUpdateDialog

# Blur Overlay Import
from ui.blur_overlay import BlurOverlay

# Config
from core.config_manager import ConfigManager

# Database
from core.db_manager import DatabaseManager

# Clipboard
from core.clipboard_monitor import ClipboardMonitor

# Dialogs
from ui.format_dialog import FormatDialog
from ui.settings_dialog import SettingsDialog

# Queue Controller
from controllers.queue_controller import QueueController, DownloadTask

# Playlist Dialog
from ui.playlist_dialog import PlaylistDialog

# Sponsor Block Categories Dialog
from ui.sponsorblock_dialog import SponsorBlockDialog

# Subtitle Select Dialog
from ui.sub_select_dialog import SubtitleSelectDialog, get_readable_language_name

# Dependency Downloader
import core.dependency_downloader

# About
import ui.about

# Circular Rotate Spinner
from ui.circular_spiner import MaterialSpinner

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

# Fonts Services
from core.services.font_service import FontService

# POT Server Services
from utils.pot_server import POTServerThread

# Update Checker
from core.services.update_checker import UpdateCheckerThread

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
logger = get_logger(__name__)
logger.info(f"=== {CONST.APP_NAME} {CONST.APP_VERSION} starting ===")

# ============================================================================
# ပထမဆုံး Run တာလားစစ်ဆေး
# ============================================================================
is_first_launch = not os.path.exists(CONFIG_PATH)

downloads_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
default_download_dir = os.path.normpath(os.path.join(downloads_dir, 'U-Tube Downloader'))
manual_cookies_path = os.path.join(APP_CACHE_DIR, "manual_cookies.txt")

# Default Download Path မရှိရင် ဖန်တီး
if not os.path.exists(default_download_dir):
    os.makedirs(default_download_dir)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Config Manager ကို Init လုပ်
        self.config_mgr = ConfigManager(CONFIG_PATH)

        # =====================================================================
        # 📐 Window Position & Size ကို ပြန် Restore လုပ်
        # =====================================================================
        self.load_window_state()

        # =====================================================================
        # 🌐 POT Server Manager ကို MainWindow မှာ ထား
        # =====================================================================
        self.pot_mgr = POTServerThread(tools_dir=TPT_DIR)
        self.pot_mgr.started_signal.connect(self.on_pot_server_started)
        self.pot_mgr.stopped_signal.connect(self.on_pot_server_stopped)
        self.pot_mgr.log_signal.connect(self.on_pot_server_log)

        # Settings Dialog reference (busy ဖြစ်နေရင် ပိတ်ဖို့ လိုအပ်တဲ့အခါ သုံး)
        self.settings_dialog = None

        # 🧹 Cleanup flag (တစ်ခါပဲ cleanup လုပ်ဖို့လို)
        self._cleanup_done = False

        # Font apply — Designer ရဲ့ font ကို override
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

        # BlurOverlay instance ကို Create လုပ်
        self.blur_overlay = BlurOverlay(self)

        # Current Information Variable တွေကို သတ်မှတ်
        self.c_thumbnail = None
        self.c_title = None
        self.c_duration = None
        self.c_chapters = None
        self.c_uploader = None
        self.c_uploaded_date = None
        self.c_urlInput = None
        self.c_description = None


        # စက်ဝိုင်းလည်တဲ့ပုံကို lblThumbnail ရဲ့ Child Widget အဖြစ် ဖန်တီးမည်
        self.spinner = MaterialSpinner(self.lblThumbnail, size=100, line_width=10, color=QColor("#3B82F6"))
        self.spinner.hide()  # စစချင်းမှာ ဖျောက်ထားမည်

        # =====================================================================
        # 🔷 Tips Rotation
        # =====================================================================
        self.tips_list = [
            "👉 Supports thousands of websites including YouTube, Facebook, Instagram, X, TikTok, Bilibili etc.",
            "🚩 Make sure to set a download directory before downloading.",
            "ℹ️ Having download issues? Go to Settings to configure cookies or update yt-dlp.",
            "😊 Choose video-only or audio-only mode to download as needed.",
            "🖼️ Right-click on the thumbnail to save it.",
            "🕹️ If fetching time is so long, change IPv4.",
            "🧊 Click uploader name to visit the channel.",
            "😎 If you got only 360p resolution turn POT Server and try again!",
            "♦️ You can stop fetching or downloading anytime.",
            "❤️ Support the developer to help improve this program.",
        ]
        self.current_tip_index = 0
        self.show_tips = True

        self.tip_timer = QTimer(self)
        self.tip_timer.setInterval(Timing.TIPS_INTERVAL_MS)
        self.tip_timer.timeout.connect(self.rotate_tips)
        self.start_tips_rotation()

        # =====================================================================
        # 🧾 txtInfoLog link interaction
        # =====================================================================
        self.txtInfoLog.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        # =====================================================================
        # 💤 Sleep mode context
        # =====================================================================
        self.awake_mode = None

        # =====================================================================
        # Single Video or Playlist 
        # =====================================================================
        self.single_video_download = False

        # =====================================================================
        # Available Subtitle အတွက် စာရင်းအလွတ် ကြိုတင်ဖန်တီးထား
        # =====================================================================
        self.saved_selected_subtitles = []

        # =====================================================================
        # 🛜 Network Manager (ThumbnailService အတွက်)
        # =====================================================================
        self.network_manager = QNetworkAccessManager(self)
        
        # =====================================================================
        # 📊 Database Init လုပ်
        # =====================================================================
        self.db_mgr = DatabaseManager(DB_PATH)

        # =====================================================================
        # ⌨️ Shortcut setup Init လုပ်
        # =====================================================================
        self._setup_shortcuts()

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

        last_added_url = loaded_settings.get(ConfigKey.LAST_ADDED_URL, 'https://www.youtube.com/watch?v=gEy-6IWaVh4')
        self.c_urlInput = last_added_url

        self.is_privacy_mode = loaded_settings.get('privacy_mode', False)
        
        if self.is_privacy_mode:
            self.urlInput.setText("🔒 ****************")
            self.changeModeButton.setChecked(True)
        else:
            self.urlInput.setText(last_added_url)
            self.changeModeButton.setChecked(False)

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
        self.skipSponsorsButton.setChecked(
            bool(loaded_settings.get(ConfigKey.SKIP_SPONSORS_BLOCK))
        )

        self.progressBar.setVisible(False)
        self.set_option_controls_status(False)
        self.is_marquee = False
        self.selectFormatsButton.setEnabled(False)
        self.downloadButton.setEnabled(False)
        if self.is_privacy_mode:
            self.display_privacy_thumbnail()
        else:
            self.display_default_thumbnail()

        # =====================================================================
        # Tray + Notification + Menus
        # =====================================================================
        self.tray_icon = None
        self.setup_tray_icon()
        self.notification_service = NotificationService(self)
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
            # (Separator) ခြား
            tray_menu.addSeparator()
            check_update_action = tray_menu.addAction("Check for update")
            check_update_action.triggered.connect(lambda: self.check_for_updates(silent=False))
            # (Separator) ခြား
            tray_menu.addSeparator()
            exit_action = tray_menu.addAction("Quit")
            paste_link_action.triggered.connect(self.paste_link)
            self.auto_add_from_clipboard_action.triggered.connect(self.on_toggle_clipboard_action)
            show_action.triggered.connect(self.showNormal)
            # exit_action.triggered.connect(self.fully_exit_app)
            exit_action.triggered.connect(self.on_tray_quit)
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
        # Always on top
        # =====================================================================
        is_always_on_top = loaded_settings.get("always_on_top", False)
        if is_always_on_top:
            self.toggle_on_top(True)
        else:
            self.toggle_on_top(False)

        # =====================================================================
        # Signals & Slots
        # =====================================================================
        self.historyButton.clicked.connect(self.on_history_clicked)
        self.pasteButton.clicked.connect(self.on_paste_clicked)
        self.getInfoButton.clicked.connect(self.on_fetch_info_clicked)
        self.selectFormatsButton.clicked.connect(self.on_select_formats_clicked)
        self.settingsButton.clicked.connect(self.on_settings_clicked)
        self.openFolderButton.clicked.connect(self.on_open_folder_clicked)
        self.downloadButton.clicked.connect(self.on_download_clicked)
        self.aboutButton.clicked.connect(self.on_about_button_clicked)
        self.changeModeButton.clicked.connect(self.change_ui_mode)
        self.lblThumbnail.file_dropped.connect(self.process_media_file)
        self.skipSponsorsButton.clicked.connect(self.on_skip_sponsors_clicked)
        self.embSubtitlesButton.clicked.connect(self.on_embedSubtitle_clicked)

        # Queue Controller Init
        self.queue_controller = QueueController(self.download_controller, self)
        self.queue_controller.task_updated.connect(self.on_queue_task_updated)
        
        # ✨ Playlist Queue စတင်ချိန်အတွက် ချိတ်ဆက်ခြင်း
        self.queue_controller.queue_started.connect(self.on_queue_started)

        # ✨ Queue တစ်ခုလုံး လုံးဝ ပြီးဆုံးမှသာ ခေါ်ရန် (task တစ်ခုချင်းစီအတွက် မဟုတ်)
        self.queue_controller.all_tasks_finished.connect(self.on_queue_finished)

        # Recent Folders List (State) — Config မှ Load
        saved_history = self.config_mgr.get("download_path_history", [])
        if isinstance(saved_history, list):
            # တကယ်ရှိနေတဲ့ folder တွေကိုပဲ ထားမယ် (မရှိတဲ့ folder ကို ဖျက်)
            self.downloadDirHistory = [p for p in saved_history if os.path.isdir(p)]
        else:
            self.downloadDirHistory = []

        # Initial Combo Options Setup
        self.refresh_combo()

        # Item နှိပ်လိုက်ရင် Signal ဖမ်းမည်
        self.downloadDirCombo.activated.connect(self.on_item_selected)

        # Thumbnail right-click
        self.lblThumbnail.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.lblThumbnail.customContextMenuRequested.connect(
            self.on_thumbnail_context_menu
        )

        self.statusbar.showMessage(StatusMsg.READY)
        logger.info("MainWindow initialized")

        # Settings မှာ Auto Update Check ကိုရွေးထားလား စစ်ဆေး
        if loaded_settings.get("check_auto_update", True):
            # App စတင်ပြီး 3 စက္ကန့်အကြာတွင် Background မှ တိတ်တဆိတ် Update စစ်ပေးမည် (Silent Check)
            QTimer.singleShot(3000, lambda: self.check_for_updates(silent=True))

    def _setup_shortcuts(self):
        """ Application-wide keyboard shortcuts များ """

        shortcuts = [
            # ─── File / URL ───
            ("Ctrl+V",         self.on_paste_clicked),
            ("Ctrl+L",         self._focus_url_input),
            ("Ctrl+Shift+X",   self._clear_url_input),
            ("Ctrl+O",         self.on_open_folder_clicked),
            ("Ctrl+S",         self.save_thumbnail),

            # ─── Actions ───
            ("F5",             self.on_fetch_info_clicked),
            ("Ctrl+R",         self.on_fetch_info_clicked),   # F5 alternative
            ("F4",             self.on_select_formats_clicked),
            ("F9",             self.on_download_clicked),
            ("Ctrl+H",         self.on_history_clicked),
            ("Ctrl+,",         self.on_settings_clicked),
            ("F1",             self.on_about_button_clicked),
            ("Ctrl+Shift+P",   self.change_ui_mode),

            # ─── Cancel ───
            ("Esc",            self._on_escape_pressed),

            # ─── Queue (နောက်မှ ထည့်ရန်) ───
            # ("Ctrl+Q",       self.on_queue_clicked),   # ← နောက်မှာ uncomment
        ]

        self._shortcuts = []  # reference သိမ်း (GC မဖျက်ဖို့)
        for key_seq, slot in shortcuts:
            sc = QShortcut(QKeySequence(key_seq), self)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(slot)
            self._shortcuts.append(sc)

        logger.info(f"Registered {len(self._shortcuts)} keyboard shortcuts")

    def _focus_url_input(self):
        """ URL input ကို focus လုပ်ပြီး အားလုံး select """
        self.urlInput.setFocus()
        self.urlInput.selectAll()

    def _clear_url_input(self):
        """ URL input ကို ရှင်း """
        self.urlInput.clear()
        self.c_urlInput = ""

    def _on_escape_pressed(self):
        """ Esc နှိပ်ရင် fetch/download ရပ် """
        if self.fetch_controller.is_running():
            self.statusbar.showMessage(StatusMsg.CANCELLING_FETCH)
            self.fetch_controller.cancel()
            self.spinner.stop()
            return
        if self.download_controller.is_running():
            self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
            self.download_controller.cancel()
            return
        # ဘာမှ မလုပ်နေရင် URL input ကို focus ပြန်ပေး
        self.urlInput.setFocus()

    def on_pot_server_started(self, success: bool, message: str):
        """ POT Server စတင်ပြီးချိန် MainWindow က လက်ခံ """
        if success:
            logger.info(f"🖲️-✅ MainWindow: {message}")
        else:
            logger.error(f"🖲️-❌ MainWindow: {message}")

    def on_pot_server_stopped(self, success: bool, message: str):
        """ POT Server ရပ်သွားချိန် MainWindow က လက်ခံ """
        if success:
            logger.info(f"🖲️-☑️ MainWindow: {message}")
        else:
            logger.error(f"🖲️-❌ MainWindow: {message}")

    def on_pot_server_log(self, text: str):
        """ POT Server log ကို MainWindow logger ဆီ ပို့ """
        logger.debug(f"🖲️ [POT] {text}")

    def load_window_state(self):
        """ config.json မှ Window Size နဲ့ Position ကို ပြန်ဖတ်ပြီး Restore လုပ်မယ် """
        if not self.config_mgr.get("remember_win_pos_size", True):
            return

        try:
            top = self.config_mgr.get("top")
            left = self.config_mgr.get("left")
            width = self.config_mgr.get("width", 850)
            height = self.config_mgr.get("height", 630)
            is_maximized = self.config_mgr.get("is_maximized", False)

            if is_maximized:
                self.showMaximized()
                return

            # Default Size သတ်မှတ်ခြင်း
            self.resize(width, height)

            # Saved Position ရှိခဲ့လျှင် Screen Bounds ထဲမှာ ရှိမရှိ စစ်ဆေးပြီးမှ ရွှေ့
            if left is not None and top is not None:
                # လက်ရှိ Active ဖြစ်နေသော Screen ရဲ့ Available Bounds ကိုယူမည်
                screen = self.screen() or QGuiApplication.primaryScreen()
                if screen:
                    screen_geo = screen.availableGeometry()

                    # Window ရဲ့ Position က Screen မြင်ကွင်းအတွင်းမှာ ရှိမရှိ စစ် (Off-screen မဖြစ်အောင်)
                    # Window ရဲ့ Top-Left ထောင့်သည် Screen အတွင်း၌ ရှိနေရမယ်
                    if (screen_geo.left() <= left <= screen_geo.right() - 50 and
                        screen_geo.top() <= top <= screen_geo.bottom() - 50):
                        self.move(left, top)
                    else:
                        logger.warning("Saved window position is out of screen bounds. Resetting to default center.")
        except Exception as e:
            logger.error(f"Failed to load window state: {e}")

    def save_window_state(self):
        """ Window ရဲ့ လက်ရှိ Position နဲ့ Size ကို config.json ထဲ သိမ်းမယ် """
        if not self.config_mgr.get("remember_win_pos_size", True):
            return

        try:
            is_maximized = self.isMaximized()

            # Window Maximized ဖြစ်နေချိန် ပိတ်လျှင် Normal Geometry (Restore Rect) ကို ယူရမယ်
            if is_maximized:
                normal_geo = self.normalGeometry()
                left = normal_geo.x()
                top = normal_geo.y()
                width = normal_geo.width()
                height = normal_geo.height()
            else:
                # Frame (Titlebar + Borders) ပါဝင်သော X, Y Position ကိုယူရန် frameGeometry သို့မဟုတ် pos/geometry သုံးနိုင်
                left = self.x()
                top = self.y()
                width = self.width()
                height = self.height()

            # ConfigManager သို့ သိမ်းဆည်းခြင်း
            self.config_mgr.update_multiple({
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "is_maximized": is_maximized
            })
            logger.info(f"Saved window state: x={left}, y={top}, w={width}, h={height}, max={is_maximized}")
        except Exception as e:
            logger.error(f"Failed to save window state: {e}")

    def toggle_on_top(self, enable: bool):
        """ Always on Top Mode ကို Window Buttons တွေ မပျောက်ဘဲ Switch လုပ်"""
        # Base Window Type နှင့် Close/Min/Max Buttons များကို ထိန်းသိမ်းထား
        flags = Qt.Window

        if enable:
            flags |= Qt.WindowStaysOnTopHint

        # Window Flags အသစ်ကို Apply လုပ်
        self.setWindowFlags(flags)

        # Window မပျောက်သွားစေရန်နှင့် Buttons တွေ Active ဖြစ်စေရန် ပြန်ပြပေး
        self.show()

    def refresh_combo(self, selected_path=None):
        self.downloadDirCombo.blockSignals(True)
        self.downloadDirCombo.clear()

        # Fixed Actions
        self.downloadDirCombo.addItem("📁 Choose folder...", userData="ACTION_CHOOSE")
        self.downloadDirCombo.addItem("❌ Clear folder history", userData="ACTION_CLEAR")
        self.downloadDirCombo.insertSeparator(2)

        # History Items
        for path in self.downloadDirHistory:
            self.downloadDirCombo.addItem(path, userData="PATH")

        # Set Selected Item index
        if selected_path and selected_path in self.downloadDirHistory:
            index = self.downloadDirCombo.findText(selected_path)
            if index != -1:
                self.downloadDirCombo.setCurrentIndex(index)
        elif self.downloadDirHistory:
            self.downloadDirCombo.setCurrentIndex(3) # Default to top path item

        self.downloadDirCombo.blockSignals(False)

    def on_item_selected(self, index):
        user_data = self.downloadDirCombo.itemData(index)

        if user_data == "ACTION_CHOOSE":
            current_dir = self.config_mgr.get("download_path", default_download_dir)
            # Folder Dialog ပွင့်မည်
            folder = QFileDialog.getExistingDirectory(self, "Select Folder", current_dir)
            if folder:
                folder_path = os.path.normpath(folder)
                if folder_path in self.downloadDirHistory:
                    self.downloadDirHistory.remove(folder_path)
                self.downloadDirHistory.insert(0, folder_path)
                
                # ✨ Config ကို ချက်ချင်း update (history + default_download_dir)
                self.config_mgr.update_multiple({
                    "download_path_history": self.downloadDirHistory,
                    "download_path": folder_path,
                })
                
                self.refresh_combo(selected_path=folder_path)
            else:
                # Cancel နှိပ်ရင် ယခင် path သို့ ပြန်ထားမည်
                self.refresh_combo()

        elif user_data == "PATH":
            # ✨ User က History ထဲက folder တစ်ခုကို ရွေးလိုက်တဲ့အခါ
            selected_path = self.downloadDirCombo.itemText(index)
            if selected_path and os.path.isdir(selected_path):
                # Config ထဲက download_path ကို update
                self.config_mgr.set("download_path", selected_path)
                
                # History ထဲမှာ ဒီ folder ကို ထိပ်ဆုံးရွှေ့ (recency)
                if selected_path in self.downloadDirHistory:
                    self.downloadDirHistory.remove(selected_path)
                self.downloadDirHistory.insert(0, selected_path)
                self.config_mgr.set("download_path_history", self.downloadDirHistory)
                
                logger.info(f"Download path changed to: {selected_path}")
                self.statusbar.showMessage(f"Download folder: {selected_path}")

        elif user_data == "ACTION_CLEAR":
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Clear History')
            msg_box.setText('Are you sure you want to clear folder history?')
            msg_box.setIcon(QMessageBox.Icon.Question)

            btn_yes = msg_box.addButton(QMessageBox.StandardButton.Yes)
            btn_no = msg_box.addButton(QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(btn_no)

            self.apply_msgbox_style(msg_box)
            msg_box.exec()
            if msg_box.clickedButton() == btn_yes:
                # History ရှင်းမည်
                self.downloadDirHistory.clear()

                # ✨ Default Download Dir ကို ပြန်ထည့် (ရွေးထားပြီးသား ဖြစ်စေရန်)
                self.downloadDirHistory.append(default_download_dir)
                self.config_mgr.set("download_path_history", self.downloadDirHistory)
                self.refresh_combo(selected_path=default_download_dir)
            else:
                self.refresh_combo()  # Reset back

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

    def open_dep_downloader_BAK(self):
        self.dep_window = core.dependency_downloader.MainWindow(parent=self)
        self.dep_window.setAttribute(Qt.WA_DeleteOnClose)
        self.dep_window.setWindowModality(Qt.WindowModal)
        self.dep_window.show()

    def open_dep_downloader_BAK(self):
        self.dep_window = core.dependency_downloader.MainWindow(parent=self)
        self.dep_window.setAttribute(Qt.WA_DeleteOnClose)
        
        # 1. Blur Overlay ကို အရင်ပြမယ်
        if hasattr(self, 'blur_overlay'):
            self.blur_overlay.show_overlay()
            
        # 2. Window ကို ပုံမှန်အတိုင်း show() နဲ့ပြမယ် (QMainWindow ဖြစ်လို့ error မတက်တော့ဘူး)
        self.dep_window.show()
        
        # 3. Window ပိတ်သွားတဲ့အခါ Blur ပြန်ဖြုတ်ပေးဖို့ finished signal (သို့မဟုတ် destroyed) ကို ချိတ်မယ်
        def on_dep_closed():
            if hasattr(self, 'blur_overlay'):
                self.blur_overlay.hide_overlay()
                
        self.dep_window.destroyed.connect(on_dep_closed)

    def open_dep_downloader(self):
        self.dep_window = core.dependency_downloader.MainWindow(parent=self)
        self.dep_window.setAttribute(Qt.WA_DeleteOnClose)
        
        # ✨ ဤနေရာတွင် Window Modality ကို WindowModal အဖြစ် သတ်မှတ်ပေးပါ
        self.dep_window.setWindowModality(Qt.WindowModal)
        
        # Blur Overlay ကို ပြမယ်
        if hasattr(self, 'blur_overlay'):
            self.blur_overlay.show_overlay()
            
        # ✨ show() အစား exec() သုံး၍ (သို့မဟုတ် show() သုံးသော်လည်း WindowModal ဖြင့်) ဖွင့်မည်
        # QMainWindow ဖြစ်သောကြောင့် show() သုံး၍ WindowModal ဖြင့် ချိတ်ဆက်ရပါမည်
        self.dep_window.show()
        
        # Window ပိတ်သွားတဲ့အခါ Blur ပြန်ဖြုတ်ပေးရန်
        def on_dep_closed():
            if hasattr(self, 'blur_overlay'):
                self.blur_overlay.hide_overlay()
                
        self.dep_window.destroyed.connect(on_dep_closed)

    # =========================================================================
    # ❌ Close / Exit
    # =========================================================================
    def closeEvent(self, event):
        # အလုပ်လုပ်နေသေးလား အရင်စစ်ဆေး
        is_info_running = self.fetch_controller.is_running()
        is_download_running = self.download_controller.is_running()

        # Settings က Value တွေကို ဖတ်
        global loaded_settings

        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False)

        if loaded_settings.get(ConfigKey.MINIMIZE_TO_TRAY, True): # MINIMIZE_TO_TRAY ကို on ထားရင်
            event.ignore()
            self.hide()
            if self.tray_icon and (is_info_running or is_download_running):
                self.notification_service.send_notification(
                    "Running in Background",
                    "Tasks are still running in the system tray."
                )
        else: # MINIMIZE_TO_TRAY ကို Off ထားရင်
            # ⚠️ အကယ်၍ ဒေါင်းလုဒ် သို့မဟုတ် Fetching တစ်ခုခု အလုပ်လုပ်နေလားအရင်စစ်
            if is_info_running or is_download_running:
                # Dialog ကို ကြိုတင်ပြင်ဆင်ခြင်း
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Confirm Exit")
                msg_box.setText("1 videos are currently in progress.\n\nDo you want to stop them and quit?")
                msg_box.setIcon(QMessageBox.Icon.Question)
                
                # Yes/No Buttons ထည့်ခြင်း
                yes_button = msg_box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
                no_button = msg_box.addButton("No", QMessageBox.ButtonRole.NoRole)
                
                # Buttons ကို သေးအောင်ပြင်ခြင်း
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
                
                # Dialog ပြခြင်း
                msg_box.exec()
                # self.show_dialog_with_blur(msg_box)
                
                # ဘယ် Button ကိုနှိပ်လဲ စစ်ဆေးခြင်း
                if msg_box.clickedButton() == yes_button:
                    # 💾 Window State ကို အရင်သိမ်း
                    self.save_window_state()

                    # Save Options Status
                    self.save_options_status()

                    # နောက်ဆုံး သွင်းထားတဲ့ url ကိုသိမ်းဆည်း
                    self.config_mgr.set('last_added_url', self.c_urlInput)

                    # နောက်ဆုံး Privacy Mode Status ကိုသိမ်းဆည်း
                    self.config_mgr.set('privacy_mode', is_privacy)

                    # Download လုပ်နေတာကို ရပ်
                    self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
                    self.download_controller.cancel()
        
                    # Thread အားလုံးကို ရပ်
                    self._cleanup_all_threads()
        
                    if self.tray_icon:
                        self.tray_icon.hide()
        
                    logger.info("Application exit — processes stopped")
                    event.accept()  # Application ကို အပြီးတိုင်ပိတ်မည်
                else:
                    event.ignore()  # Application ကို မပိတ်ဘူး၊ ဆက်ထားမယ်
            else:
                # 💾 Window State ကို အရင်သိမ်း
                self.save_window_state()

                # Save Options Status
                self.save_options_status()
                
                # Privacy Mode status စစ်ဆေးခြင်း
                is_privacy = getattr(self, 'is_privacy_mode', False)

                # နောက်ဆုံး သွင်းထားတဲ့ url ကိုသိမ်းဆည်း
                if is_privacy:
                    if self.c_urlInput == None:
                        self.config_mgr.set('last_added_url', "")
                    else:
                        self.config_mgr.set('last_added_url', self.c_urlInput)
                else:
                    self.config_mgr.set('last_added_url', self.urlInput.text())

                # နောက်ဆုံး Privacy Mode Status ကိုသိမ်းဆည်း
                self.config_mgr.set('privacy_mode', is_privacy)

                # Download လုပ်နေတာကို ရပ်
                self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
                self.download_controller.cancel()

                # Thread အားလုံးကို ရပ်
                self._cleanup_all_threads()
    
                if self.tray_icon:
                    self.tray_icon.hide()
    
                logger.info("Application exit — processes stopped")
                event.accept()

    def _cleanup_all_threads(self):
        """ App ပိတ်ချိန်မှာ thread အားလုံးကို ရပ် """
        
        if self._cleanup_done:
            logger.debug("Cleanup already done — skipping")
            return
        self._cleanup_done = True

        logger.info("Cleaning up all threads...")

        # ၁။ MainWindow ရဲ့ POT Server thread
        if hasattr(self, 'pot_mgr') and self.pot_mgr:
            try:
                if self.pot_mgr.isRunning():
                    # Health checker ရပ်
                    if hasattr(self.pot_mgr, '_health') and self.pot_mgr._health:
                        try:
                            self.pot_mgr._health.stop()
                            self.pot_mgr._health.wait(1500)
                        except Exception:
                            pass
                        self.pot_mgr._health = None

                    # Output reader ရပ်
                    if hasattr(self, 'pot_mgr') and hasattr(self.pot_mgr, '_reader') and self.pot_mgr._reader:
                        try:
                            self.pot_mgr._reader.stop()
                            self.pot_mgr._reader.wait(1500)
                        except Exception:
                            pass
                        self.pot_mgr._reader = None

                    # Stop flag သတ်
                    self.pot_mgr._stop_requested_flag = True
                    self.pot_mgr._is_running = False

                    # Process သတ်
                    try:
                        import requests as _req
                        _req.post(f"{self.pot_mgr.server_url}/shutdown", timeout=0.5)
                    except Exception:
                        pass

                    if self.pot_mgr.process and self.pot_mgr.process.poll() is None:
                        self.pot_mgr.process.terminate()
                        try:
                            self.pot_mgr.process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            self.pot_mgr.process.kill()
                    self.pot_mgr.process = None

                    # Port fallback kill
                    try:
                        POTServerThread.kill_process_on_port(4416)
                    except Exception:
                        pass

                    # Thread ကို ကိုယ်တိုင် ရပ်
                    self.pot_mgr.quit()
                    if not self.pot_mgr.wait(2000):
                        logger.warning("POTServerThread did not stop — terminating")
                        self.pot_mgr.terminate()
                        self.pot_mgr.wait(1000)

                    logger.info("Stopped MainWindow pot_mgr")
            except Exception as e:
                logger.error(f"Error stopping MainWindow pot_mgr: {e}")

        # ၂။ SettingsDialog ရဲ့ threads (Dialog ဖွင့်နေသေးရင်)
        if hasattr(self, 'settings_dialog') and self.settings_dialog:
            try:
                self._cleanup_settings_dialog_threads(self.settings_dialog)
            except Exception as e:
                logger.error(f"Settings dialog cleanup failed: {e}")

        # ၃။ MainWindow ရဲ့ Update Checker
        if hasattr(self, 'update_thread') and self.update_thread:
            try:
                if self.update_thread.isRunning():
                    self.update_thread.quit()
                    if not self.update_thread.wait(1500):
                        self.update_thread.terminate()
                        self.update_thread.wait(500)
                    logger.info("Stopped update checker thread")
            except Exception as e:
                logger.error(f"Error stopping update thread: {e}")

        # ၄။ Clipboard Monitor
        if hasattr(self, 'clipboard_thread') and self.clipboard_thread:
            try:
                self.clipboard_thread.stop()
                if hasattr(self.clipboard_thread, 'isRunning') and self.clipboard_thread.isRunning():
                    self.clipboard_thread.wait(1000)
                self.clipboard_thread = None
                logger.info("Stopped clipboard monitor")
            except Exception as e:
                logger.error(f"Error stopping clipboard monitor: {e}")

        # ၅။ Fetch Controller (Fetching လုပ်နေတာကို ရပ်ရန်)
        if hasattr(self, 'fetch_controller') and self.fetch_controller:
            try:
                if self.fetch_controller.is_running():
                    self.fetch_controller.cancel()
                    QApplication.processEvents()
            except Exception as e:
                logger.error(f"Error stopping fetch controller: {e}")

        # ၆။ Queue Controller (Playlist Queue တွေကို အပြီး ရပ်ရန်)
        if hasattr(self, 'queue_controller') and self.queue_controller:
            try:
                if hasattr(self.queue_controller, 'is_running') and self.queue_controller.is_running():
                    self.queue_controller.stop_queue()
                if hasattr(self.queue_controller, 'clear_queue'):
                    self.queue_controller.clear_queue()
                logger.info("Stopped queue controller")
            except Exception as e:
                logger.error(f"Error stopping queue controller: {e}")

        # ၇။ Download Controller (Download လုပ်နေတာတွေကို အပြီး ရပ်ရန်)
        if hasattr(self, 'download_controller') and self.download_controller:
            try:
                if self.download_controller.is_running():
                    self.download_controller.cancel()
                    QApplication.processEvents()
            except Exception as e:
                logger.error(f"Error stopping download controller: {e}")

        # ၈။ Awake Mode ကိုပိတ်
        if hasattr(self, 'awake_mode') and self.awake_mode:
            try:
                self.awake_mode.__exit__(None, None, None)
                self.awake_mode = None
                logger.info("Released awake mode during cleanup")
            except Exception as e:
                logger.error(f"Error releasing awake mode: {e}")

        logger.info("All threads cleanup completed")

    def _cleanup_settings_dialog_threads(self, dialog):
        """ Settings Dialog ရဲ့ background threads အားလုံးကို ရပ် """

        try:
            thread_attrs = (
                'pot_dl_thread', 'plugin_dl_thread',
                'module_downloader', 'update_thread', '_stop_worker'
            )
            for attr in thread_attrs:
                thread = getattr(dialog, attr, None)
                if thread and hasattr(thread, 'isRunning') and thread.isRunning():
                    try:
                        if hasattr(thread, 'stop'):
                            thread.stop()
                        thread.quit()
                        if not thread.wait(1500):
                            thread.terminate()
                            thread.wait(500)
                        logger.info(f"Stopped settings dialog thread: {attr}")
                    except Exception as e:
                        logger.error(f"Error stopping {attr}: {e}")
        except Exception as e:
            logger.error(f"Settings dialog threads cleanup failed: {e}")

    def on_tray_quit(self):
        # အလုပ်လုပ်နေသေးလား အရင်စစ်ဆေး
        is_info_running = self.fetch_controller.is_running()
        is_download_running = self.download_controller.is_running()

        # Settings က Value တွေကို ဖတ်
        global loaded_settings

        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False)

        # 💾 Window State ကို အရင်သိမ်း
        self.save_window_state()

        # Save Options Status
        self.save_options_status()
        
        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False)

        # နောက်ဆုံး သွင်းထားတဲ့ url ကိုသိမ်းဆည်း
        if is_privacy:
            if self.c_urlInput == None:
                self.config_mgr.set('last_added_url', "")
            else:
                self.config_mgr.set('last_added_url', self.c_urlInput)
        else:
            self.config_mgr.set('last_added_url', self.urlInput.text())

        # နောက်ဆုံး Privacy Mode Status ကိုသိမ်းဆည်း
        self.config_mgr.set('privacy_mode', is_privacy)

        # Download လုပ်နေတာကို ရပ်
        self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
        self.download_controller.cancel()

        # Thread အားလုံးကို ရပ်
        self._cleanup_all_threads()

        if self.tray_icon:
            self.tray_icon.hide()

        logger.info("Application exit — processes stopped")
        QApplication.quit()

    def on_tray_icon_activated(self, reason):
        if (reason == QSystemTrayIcon.Trigger
                or reason == QSystemTrayIcon.DoubleClick):
            self.showNormal()
            self.activateWindow()

    def save_options_status(self):
        # GUI override
        embedded_thumbnail = self.embThumbnailButton.isChecked()
        embedded_chapters = self.embChaptersButton.isChecked()
        embedded_subtitle = self.embSubtitlesButton.isChecked()
        embedded_metadata = self.embMetadataButton.isChecked()
        use_mtime = self.useMTimeButton.isChecked()
        skip_sponsors_block = self.skipSponsorsButton.isChecked()
        is_privacy = self.changeModeButton.isChecked()

        updated_data = {
            ConfigKey.IS_PRIVACY: is_privacy,
            ConfigKey.USE_MTIME: use_mtime,
            ConfigKey.SKIP_SPONSORS_BLOCK: skip_sponsors_block,
            ConfigKey.EMBED_THUMBNAIL: embedded_thumbnail,
            ConfigKey.EMBED_SUBTITLES: embedded_subtitle,
            ConfigKey.EMBED_CHAPTERS: embedded_chapters,
            ConfigKey.EMBED_METADATA: embedded_metadata,
        }
        self.config_mgr.update_multiple(updated_data)

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
    # Privacy Thumbnail
    # =========================================================================
    def display_privacy_thumbnail(self):
        try:
            pixmap = QPixmap(ResourcePath.PRIVACY_THUMBNAIL)
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
    # Default Thumbnail
    # =========================================================================
    def display_unavailable_thumbnail(self):
        try:
            pixmap = QPixmap(ResourcePath.UNAVAILABLE_THUMBNAIL)
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
    # Spinner
    # =========================================================================
    def center_spinner(self):
        """ Spinner ကို lblThumbnail ရဲ့ ဗဟိုတည့်တည့်သို့ ရွှေ့ပေးမယ် """
        if hasattr(self, "spinner") and self.lblThumbnail:
            x = (self.lblThumbnail.width() - self.spinner.width()) // 2
            y = (self.lblThumbnail.height() - self.spinner.height()) // 2
            self.spinner.move(x, y)

    def resizeEvent(self, event):
        """ Window Size ပြောင်းရင် Spinner အလယ်တည့်တည့်မှာ ရှိနေစေရန် """
        super().resizeEvent(event)
        self.center_spinner()

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
        
        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False) 
        self.c_urlInput = clipboard.text().strip() # Current Url ကို သိမ်းဆည်း
        if is_privacy:
            self.urlInput.setText("🔒 ****************")
        else:
            self.urlInput.setText(clipboard.text().strip())
        self.on_fetch_info_clicked()

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
            self.on_fetch_info_clicked()

    def on_history_clicked(self):
        if self.clipboard_thread:
            self.clipboard_thread.stop()

        history_records = self.db_mgr.get_all_history()

        # db_mgr parameter ပါ ထည့်ပေး
        dialog = HistoryDialog(self, history_records=history_records, db_mgr=self.db_mgr)

        if self.show_dialog_with_blur(dialog) == QDialog.Accepted:
            selected_url = dialog.get_selected_url()
            if selected_url:
                # 1. ရှေ့က Fetch ထားသော UI Data များကို Default သို့ ပြန်ပြောင်း (Reset)
                self.reset_video_info_ui()
                # Privacy Mode status စစ်ဆေးခြင်း
                is_privacy = getattr(self, 'is_privacy_mode', False)
                if is_privacy:
                    self.urlInput.setText("🔒 ****************")
                else:
                    self.urlInput.setText(selected_url)
                self.c_urlInput = selected_url # Current Url ကို သိမ်းဆည်း

        
        if hasattr(self, 'check_and_toggle_clipboard_monitor'):
            self.check_and_toggle_clipboard_monitor()
        else:
            if self.clipboard_thread:
                self.clipboard_thread.start()

    # ═══════════════════════════════════════════
    # Media Processing (QProcess)
    # ═══════════════════════════════════════════
    def process_media_file(self, file_path):
        """ MediaInfo ကိုသုံးပြီး Media Info ကို ဖတ်မယ် """
        if self.fetch_controller.is_running() or self.download_controller.is_running():
            return
        
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            return

        self._current_file = file_path

        self.reset_video_info_ui()
        self.lblThumbnail.clear()
        self.spinner.stop()
        self.spinner.start()
        logger.info("Processing media file...")

        try:
            # cover_data=True က base64 cover ကို ရယူဖို့ အဓိက parameter
            media_info = MediaInfo.parse(file_path, cover_data=True)
        except Exception as e:
            logger.error(f"MediaInfo parse failed: {e}")
            self.reset_video_info_ui()
            self.spinner.stop()
            self.statusbar.showMessage("❌ Error: Unable to parse media file")
            return

        # Streams / cover / metadata တွေကို MediaInfo track ကနေ ဆွဲထုတ်
        cover_info = self.find_embedded_cover_stream(media_info)

        info = self.media_info_parsing(media_info, file_path, cover_info)

        if info["url"] is None or info["url"] == "":
            logger.error("⚠️ Metadata not found!")
            self.txtInfoLog.setText("⚠️ Metadata not found!")
            self.spinner.stop()
            self.display_default_thumbnail()
            return

        is_privacy = info["is_privacy"]

        # ─── Common fields သိမ်းဆည်း ────────────────
        self.c_urlInput     = info["url"]
        self.c_title        = info["title"]
        self.c_duration     = info["duration_text"]
        self.c_chapters     = info["chapters_text"]
        self.c_uploader     = info["uploader"]
        self.c_upload_date  = info["upload_date"]
        self.c_description  = info["description"]
        self.uploader_url   = None
        
        self.lblUploaderVal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lblUploaderVal.setToolTip("")
        self.lblUploaderVal.setStyleSheet("""
            QLabel:hover {
                color: #3498db;
                text-decoration: underline;
            }
        """)

        # ─── UI မှာ ဖော်ပြခြင်း ──────────────────────
        if is_privacy:
            self.urlInput.setText("🔒 ****************")
            self.lblTitle.setText("🔒 *************************")
            self.lblDurationVal.setText(self.c_duration)
            self.lblChaptersVal.setText(str(self.c_chapters))
            self.lblUploaderVal.setText("🔒 *******")
            self.lblUploadDateVal.setText(self.c_upload_date)
            if not self.fetch_controller.is_running() or not self.download_controller.is_running():
                self.txtInfoLog.setHtml("<i>🔒 Description hidden in Privacy Mode.</i>")
            self.display_privacy_thumbnail()
        else:
            self.urlInput.setText(self.c_urlInput)
            self.lblTitle.setText(self.c_title)
            self.lblDurationVal.setText(self.c_duration)
            self.lblChaptersVal.setText(str(self.c_chapters))
            self.lblUploaderVal.setText(self.c_uploader)
            self.lblUploadDateVal.setText(self.c_upload_date)
            if not self.fetch_controller.is_running() or not self.download_controller.is_running():                
                self.txtInfoLog.setHtml(description_to_html(self.c_description))

        # ─── Thumbnail Handling ─────────────────────
        self._pending_privacy = is_privacy

        if cover_info is not None:
            # MediaInfo က base64 data ကို ပေးထားပြီးသား၊ တိုက်ရိုက် display
            self._display_cover_from_mediainfo(cover_info)
        else:
            self.c_thumbnail = None
            logger.info(f"{self._current_file} is loaded (no cover).")
            self.spinner.stop()
            self.display_default_thumbnail()
    
    def find_embedded_cover_stream(self, media_info):
        """
        MediaInfo parse လုပ်ထားတဲ့ media_info object ကနေ
        embedded cover ရှိမရှိ ရှာပြီး dict တစ်ခု ပြန်ပေးတယ်။

        Returns:
            dict | None: {
                "cover_data": "<base64 string>",
                "cover_mime": "image/jpeg",
                "kind": "cover",
            }
        """
        for track in media_info.tracks:
            cover_data = getattr(track, "cover_data", None)
            if not cover_data:
                continue

            # ပုံများစွာ ရှိရင် " / " နဲ့ ခွဲထားတယ် — ပထမဆုံးကို ယူ
            first_b64 = cover_data.split(" / ")[0].strip()
            if not first_b64:
                continue

            mime = getattr(track, "cover_mime", None) or "image/jpeg"
            # MediaInfo က "image/jpeg / image/png" လို့ ဖြစ်နေနိုင်
            mime = mime.split(" / ")[0].strip()

            return {
                "cover_data": first_b64,
                "cover_mime": mime,
                "kind": "cover",
            }

        return None

    def media_info_parsing(self, media_info, file_path, cover_info):
        """
        MediaInfo object ကနေ metadata ကို ဆွဲထုတ်ပြီး dict ပြန်ပေးတယ်။
        """
        result = {
            "title": None,
            "url": None,
            "uploader": None,
            "upload_date": None,
            "description": None,
            "duration": 0,
            "duration_text": "00:00",
            "chapters_count": 0,
            "chapters_text": "None",
            "is_privacy": False,
        }

        is_privacy = getattr(self, "is_privacy_mode", False)
        result["is_privacy"] = is_privacy

        # ─── General track ကို ရှာ (metadata အားလုံး ဒီမှာ) ───
        general = None

        for track in media_info.tracks:
            if track.track_type == "General":
                general = track
                break

        if general is not None:
            # MediaInfo က attribute နာမည်တွေကို snake_case နဲ့ ပေးတယ်
            # (ဥပမာ: track.title, track.album, track.performer, ...)
            result["title"] = (
                getattr(general, "title", None)
                or getattr(general, "movie_name", None)
                or getattr(general, "track_name", None)
            )
            # URL ကို "Comment" tag မှာ သိမ်းထားလေ့ရှိ
            result["url"] = (
                getattr(general, "comment", None)
                or getattr(general, "description", None)
            )
            result["uploader"] = (
                getattr(general, "performer", None)
                or getattr(general, "artist", None)
                or getattr(general, "album_performer", None)
            )
            result["description"] = (
                getattr(general, "description", None)
                or getattr(general, "comment", None)
            )

            # Date — MediaInfo က recorded_date သို့မဟုတ် tag date ကို ပေးတယ်
            raw_date = (
                getattr(general, "recorded_date", None)
                or getattr(general, "tagged_date", None)
            )
            if raw_date:
                raw_date = str(raw_date).strip()
                # "2024-01-15" လို ဖြစ်နေရင် ဒီအတိုင်း၊ "20240115" ဆိုရင် format ချ
                if len(raw_date) == 8 and raw_date.isdigit():
                    raw_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
                result["upload_date"] = raw_date

            # Duration — MediaInfo က milliseconds နဲ့ ပေးတယ်
            duration_ms = getattr(general, "duration", None)
            if duration_ms:
                seconds = int(float(duration_ms) / 1000.0)
                result["duration"] = seconds
                result["duration_text"] = self.format_duration(seconds)
            else:
                result["duration_text"] = "N/A"

            # ─── Chapters ─────────────────────────────
            # MediaInfo 7.x — Menu track ရဲ့ chapters_pos_begin/end ကနေ count ယူ
            # MediaInfo 6.x — Menu track ရဲ့ extra dict ကနေ count ယူ (fallback)
            chapter_count = 0
            chapter_titles = []

            for track in media_info.tracks:
                if track.track_type not in ("Menu", "Other"):
                    continue

                # ─── နည်းလမ်း ၁: MediaInfo 7.x — chapters_pos_begin/end ───
                pos_begin = getattr(track, "chapters_pos_begin", None)
                pos_end = getattr(track, "chapters_pos_end", None)

                if pos_begin is not None and pos_end is not None:
                    try:
                        chapter_count = int(pos_end) - int(pos_begin)
                    except (TypeError, ValueError):
                        chapter_count = 0

                    # Chapter title တွေကို track ရဲ့ attribute တွေကနေ ယူ
                    # key format: "00_00_00000" → value: chapter title
                    if chapter_count > 0:
                        for key in track.__dict__:
                            # timestamp format key ကို ဖမ်း (ဥပမာ "00_00_00000")
                            if re.match(r"^\d{2}_\d{2}_\d{5}$", key):
                                chapter_titles.append(getattr(track, key, ""))

                    if chapter_count > 0:
                        break

                # ─── နည်းလမ်း ၂: MediaInfo 6.x — extra dict (fallback) ───
                extra = getattr(track, "extra", None)
                if isinstance(extra, dict) and extra:
                    chapter_count = len(extra)
                    chapter_titles = list(extra.values())
                    break

                if isinstance(extra, list) and extra:
                    chapter_count = len(extra)
                    break

            # Result သိမ်း
            result["chapters_count"] = chapter_count
            result["chapters_text"] = str(chapter_count) if chapter_count > 0 else "None"
            result["chapter_titles"] = chapter_titles

        return result

    def _display_cover_from_mediainfo(self, cover_info):
        """
        MediaInfo က ပေးထားတဲ့ base64 cover data ကို memory ထဲမှာတင်
        QPixmap အဖြစ် ပြောင်းပြီး display ပြတယ်။ Disk ပေါ် ဘာမှ မရေးဘူး။
        """
        import base64
        from PySide6.QtCore import QByteArray

        b64 = cover_info.get("cover_data")
        if not b64:
            self.c_thumbnail = None
            self.spinner.stop()
            self.display_default_thumbnail()
            return

        try:
            image_bytes = base64.b64decode(b64)
        except Exception as e:
            logger.error(f"Base64 decode failed: {e}")
            self.c_thumbnail = None
            self.spinner.stop()
            self.display_default_thumbnail()
            return

        image = QImage()
        if not image.loadFromData(QByteArray(image_bytes)):
            logger.warning("QImage could not decode cover data")
            self.c_thumbnail = None
            self.spinner.stop()
            self.display_default_thumbnail()
            return

        pixmap = QPixmap.fromImage(image)
        self._cover_pixmap = pixmap
        self.c_thumbnail = pixmap

        if getattr(self, "_pending_privacy", False):
            self.display_privacy_thumbnail()
            logger.info(f"{self._current_file} is loaded (privacy, cover saved).")
        else:
            scaled = ThumbnailService.scale_for_label(pixmap)
            self.lblThumbnail.setPixmap(scaled)
            logger.info(f"{self._current_file} is loaded.")

        self.spinner.stop()

    def format_duration(self, seconds):
        if seconds <= 0:
            return "N/A"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            formatted_duration = f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            formatted_duration = f"{minutes}:{secs:02d}"
        return formatted_duration

    def format_size(self, bytes_size):
        if bytes_size <= 0:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    # =========================================================================
    # Settings / About
    # =========================================================================
    def on_Goto_Settings_Clicked(self):
        # [CHANGED] MainWindow ရဲ့ pot_mgr ကို SettingsDialog ဆီ ပို့
        dialog = SettingsDialog(
            self.config_mgr, self,
            initial_tab=3,
            pot_mgr=self.pot_mgr
        )
        self.settings_dialog = dialog
        try:
            dialog.exec()
        finally:
            self.settings_dialog = None

    def on_settings_clicked(self):
        if self.clipboard_thread:
            self.clipboard_thread.stop()

        global loaded_settings
        # Dialog မဖွင့်ခင် လက်ရှိ config value ကို အရင်မှတ်ထားခြင်း
        previous_always_on_top_status = self.config_mgr.get("always_on_top", False)

        # [CHANGED] MainWindow ရဲ့ pot_mgr ကို SettingsDialog ဆီ ပို့
        dialog = SettingsDialog(
            self.config_mgr, self,
            initial_tab=None,
            pot_mgr=self.pot_mgr
        )
        self.settings_dialog = dialog

        try:
            if self.show_dialog_with_blur(dialog) == QDialog.DialogCode.Accepted:
                loaded_settings = self.config_mgr.get_all()
                self.check_and_toggle_clipboard_monitor()

                # Download Path အသစ်ကို History ထဲ ထည့်ပြီး ComboBox ကို Sync လုပ်
                self._sync_download_dir_history()

                # Config ထဲမှ နောက်ဆုံး စာရင်းသွင်းထားသော တန်ဖိုးကို ယူခြင်း
                is_auto_add = self.config_mgr.get("add_links_clipboard", False)

                # Tray Menu Action ၏ Checked state ကို Sync လုပ်ခြင်း
                if hasattr(self, 'auto_add_from_clipboard_action'):
                    self.auto_add_from_clipboard_action.setChecked(is_auto_add)

                self.statusbar.showMessage(StatusMsg.SETTINGS_SAVED)
                self.statusbar.showMessage(StatusMsg.READY)
                logger.info("Settings updated")
        finally:
            self.settings_dialog = None

        if hasattr(self, 'check_and_toggle_clipboard_monitor'):
            self.check_and_toggle_clipboard_monitor()
        else:
            if self.clipboard_thread:
                self.clipboard_thread.start()

        # Current Always On Top ကို ပြန်စစ်ခြင်း
        current_always_on_top_status = self.config_mgr.get("always_on_top", False)
        if previous_always_on_top_status != current_always_on_top_status:  # မတူဘူးဆိုရင်
            self.toggle_on_top(current_always_on_top_status)  # အရင် value နဲ့ မတူဘူးဆိုမှ ပြောင်းလဲ

    def _sync_download_dir_history(self):
        """
        Settings Dialog က Save/Restore လုပ်ပြီးချိန်မှာ
        Download Folder History ကို Config မှ ပြန် Load ပြီး
        ComboBox ကို Refresh လုပ်ပေးတယ်။
        """
        try:
            # ၁။ Config မှ download_path_history ကို ပြန်ဖတ်
            saved_history = self.config_mgr.get("download_path_history", [])
            if isinstance(saved_history, list):
                self.downloadDirHistory = [p for p in saved_history if os.path.isdir(p)]
            else:
                self.downloadDirHistory = []

            # ၂။ Config ထဲက download_path (Default/Current) ကို ယူ
            current_dl_path = self.config_mgr.get("download_path", "")

            # ၃။ တကယ်လို့ current_dl_path က History ထဲ မပါသေးရင် ထည့်
            if current_dl_path and os.path.isdir(current_dl_path):
                if current_dl_path not in self.downloadDirHistory:
                    self.downloadDirHistory.insert(0, current_dl_path)
                    # Config ကိုလည်း update (နောက်တစ်ခါ ဖွင့်ရင် ပါစေရန်)
                    self.config_mgr.set("download_path_history", self.downloadDirHistory)

            # ၄။ ComboBox ကို Refresh — current_dl_path ကို ရွေးထားပြီးသား ဖြစ်စေ
            if current_dl_path and current_dl_path in self.downloadDirHistory:
                self.refresh_combo(selected_path=current_dl_path)
            else:
                self.refresh_combo()

            logger.info(f"Download dir history synced: {len(self.downloadDirHistory)} items")
        except Exception as e:
            logger.error(f"Failed to sync download dir history: {e}")

    def on_about_button_clicked(self):
        about_dialog = ui.about.AboutDialog(self)
        self.show_dialog_with_blur(about_dialog)

    # =========================================================================
    # Skip Sponsor Blocks
    # =========================================================================
    def on_skip_sponsors_clicked(self):
        """ skipSponsorsButton ကို နှိပ်လိုက်သည့်အခါ SponsorBlockDialog ကို ဖွင့်မည် """
        # dialog = SponsorBlockDialog(parent=self)
        dialog = SponsorBlockDialog(config_mgr=self.config_mgr, parent=self)

        # Blur Effect ဖြင့် Dialog ကို ပြသရန် (main.py တွင် ရှိပြီးသား show_dialog_with_blur ကို သုံးသည်)
        result = self.show_dialog_with_blur(dialog)

        if result == QDialog.Accepted:
            # OK နှိပ်လိုက်သောအခါ Check လုပ်ထားသည့် categories များကို ရယူခြင်း
            checked_categories = []
            for category_name, checkbox in dialog.get_checked_categories():
                if checkbox.isChecked():
                    checked_categories.append(category_name)

            # ရွေးချယ်ထားသည်များကို Log ထုတ်ရန် သို့မဟုတ် သိမ်းဆည်းရန်
            # logger.info(f"SponsorBlock categories selected: {checked_categories}")
            self.statusbar.showMessage(
                f"SponsorBlock: Selected {len(checked_categories)} categories."
            )
            if len(checked_categories) > 0:
                self.skipSponsorsButton.setChecked(True)
            else:
                self.skipSponsorsButton.setChecked(False)
        else:
            # Cancel နှိပ်လိုက်သောအခါ သို့မဟုတ် ပိတ်လိုက်သောအခါ
            checked_categories = []
            for category_name, checkbox in dialog.get_checked_categories():
                if checkbox.isChecked():
                    checked_categories.append(category_name)

            if len(checked_categories) > 0:
                self.skipSponsorsButton.setChecked(True)
            else:
                self.skipSponsorsButton.setChecked(False)
                
            self.statusbar.showMessage("SponsorBlock selection cancelled.")

    # =========================================================================
    # Subtitle Selection
    # =========================================================================
    def on_embedSubtitle_clicked(self):
        """ CC ခလုတ်ကို နှိပ်လိုက်သည့်အခါ Fetch လုပ်ထားသော info မှ subtitles များကို ယူ၍ Dialog ပြရန် """
        if not hasattr(self, 'info') or not self.info:
            self.statusbar.showMessage("No video information available. Please fetch info first.")
            return

        # yt-dlp info မှ subtitles နှင့် automatic_captions များကို စုဆောင်းခြင်း
        available_subs = []
        
        # Manual subtitles များကို စစ်ဆေးခြင်း
        subtitles = self.info.get("subtitles", {})
        if isinstance(subtitles, dict):
            for lang_code in subtitles.keys():
                available_subs.append(f"({lang_code})")

        # Auto-generated captions များကို စစ်ဆေးခြင်း
        auto_subs = self.info.get("automatic_captions", {})
        if isinstance(auto_subs, dict):
            for lang_code in auto_subs.keys():
                available_subs.append(f"({lang_code}) [Auto-generated]")

        # အကယ်၍ info ထဲတွင် sub တွေ မပါလာသေးပါက အထွေထွေ Language စာရင်းပုံစံ သို့မဟုတ် မူလစာရင်းကို ပြရန်
        if not available_subs:
            # available_subs = ["English (en)", "English (Auto-generated)", "Burmese (my)"]
            available_subs = []

        formatted_available_subs = [get_readable_language_name(sub) for sub in available_subs]

        # SubtitleSelectDialog ကို ဖွင့်မည် (formatted_available_subs ကို ပို့ပေးပါ)
        dialog = SubtitleSelectDialog(
                    subtitles=formatted_available_subs, 
                    pre_selected=self.saved_selected_subtitles,  
                    parent=self
                )
        
        # Dialog ကို Blur အသွင်အပြင်ဖြင့် ပြသရန်
        if self.show_dialog_with_blur(dialog) == QDialog.Accepted:
            selected_subtitles = dialog.get_selected_subtitles()
            self.saved_selected_subtitles = selected_subtitles  # ရွေးထားတာတွေကို သိမ်းဆည်းရန် saved_selected_subtitles ထဲ တိုက်ရိုက်ထည့်
            self.selected_subtitles_list = selected_subtitles
            if len(selected_subtitles) > 0:
                self.embSubtitlesButton.setChecked(True)
            else:
                self.embSubtitlesButton.setChecked(False)

            if selected_subtitles:
                self.statusbar.showMessage(f"Selected Subtitles: {', '.join(selected_subtitles)}")
                logger.info(f"Selected subtitles for embedding: {selected_subtitles}")
            else:
                self.statusbar.showMessage("No subtitles selected.")
        else:
            selected_subtitles = dialog.get_selected_subtitles()
            self.saved_selected_subtitles = selected_subtitles  # 👈 Cancel လုပ်ရင်တောင် လက်ရှိရွေးထားတာတွေကို မှတ်ထားရန်
            self.selected_subtitles_list = selected_subtitles
            if len(selected_subtitles) > 0:
                self.embSubtitlesButton.setChecked(True)
            else:
                self.embSubtitlesButton.setChecked(False)
    
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
    def create_stacked_playlist_thumbnail(self, pixmap: QPixmap, total_items: int = 0) -> QPixmap:
            """
            Create a stacked playlist thumbnail inspired by YouTube's
            playlist thumbnail design.
            """
            if pixmap.isNull():
                return pixmap
    
            scaled = ThumbnailService.scale_for_label(pixmap)
    
            if scaled.isNull():
                return pixmap
    
            width = scaled.width()
            height = scaled.height()
    
            if width <= 0 or height <= 0:
                return pixmap
    
            # ---------------------------------------------------------
            # Canvas
            # ---------------------------------------------------------
            stack_space = 18
    
            result = QPixmap(width, height)
            result.fill(Qt.GlobalColor.transparent)
    
            painter = QPainter(result)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(
                QPainter.RenderHint.SmoothPixmapTransform
            )
    
            # ---------------------------------------------------------
            # Background Stack Layers
            # ---------------------------------------------------------
            painter.setPen(Qt.PenStyle.NoPen)
    
            layers = [
                {
                    "x": 30,
                    "y": 1,
                    "w": width - 60,
                    "h": 12,
                    "color": QColor("#454545"),
                },
                {
                    "x": 18,
                    "y": 5,
                    "w": width - 36,
                    "h": 12,
                    "color": QColor("#595959"),
                },
                {
                    "x": 7,
                    "y": 10,
                    "w": width - 14,
                    "h": 12,
                    "color": QColor("#777777"),
                },
            ]
    
            for layer in layers:
                rect = QRect(
                    layer["x"],
                    layer["y"],
                    layer["w"],
                    layer["h"],
                )
    
                painter.setBrush(layer["color"])
                painter.drawRoundedRect(rect, 7, 7)
    
            # ---------------------------------------------------------
            # Main Thumbnail
            # ---------------------------------------------------------
            main_x = 0
            main_y = stack_space
            main_width = width
            main_height = height - stack_space
    
            main_rect = QRect(
                main_x,
                main_y,
                main_width,
                main_height,
            )
    
            # Keep the original aspect ratio.
            # Do not crop the thumbnail unnecessarily.
            main_pixmap = scaled.scaled(
                main_width,
                main_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
    
            # Center the image inside the main thumbnail area.
            image_x = main_x + (
                main_width - main_pixmap.width()
            ) // 2
    
            image_y = main_y + (
                main_height - main_pixmap.height()
            ) // 2
    
            clip_path = QPainterPath()
            clip_path.addRoundedRect(
                main_rect.adjusted(0, 0, -1, -1),
                5,
                5,
            )
    
            painter.save()
            painter.setClipPath(clip_path)
    
            painter.drawPixmap(
                main_rect,
                scaled,
            )
    
            painter.restore()
    
            # ---------------------------------------------------------
            # Playlist Video Count Badge
            # ---------------------------------------------------------
            if total_items > 0:
                badge_text = f"≡ {total_items} videos"
    
                font = QFont("Segoe UI", 9)
                font.setBold(True)
                painter.setFont(font)
    
                metrics = painter.fontMetrics()
    
                badge_width = metrics.horizontalAdvance(
                    badge_text
                ) + 16
    
                badge_height = metrics.height() + 8
    
                badge_x = max(
                    main_x + 4,
                    main_x + main_width - badge_width - 8,
                )
    
                badge_y = (
                    main_y
                    + main_height
                    - badge_height
                    - 8
                )
    
                badge_rect = QRect(
                    badge_x,
                    badge_y,
                    badge_width,
                    badge_height,
                )
    
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(0, 0, 0, 210))
    
                painter.drawRoundedRect(
                    badge_rect,
                    5,
                    5,
                )
    
                painter.setPen(QColor("#FFFFFF"))
    
                painter.drawText(
                    badge_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    badge_text,
                )
    
            painter.end()
    
            return result

    def on_thumbnail_ready(self, pixmap: QPixmap):
        """ Thumbnail Service မှ ပုံကျလာပါက ခေါ်ပေးသည့် Slot Method """
        self.thumbnail_success = True
        self.thumbnail_failed = False
        
        # 📂 Playlist ဟုတ်မဟုတ် စစ်ဆေးခြင်း
        is_playlist = False
        if hasattr(self, 'info') and isinstance(self.info, dict):
            is_playlist = (self.info.get("_type") == "playlist" or "entries" in self.info)

        # Playlist ဖြစ်မှသာ Stacked Thumbnail ကို သုံးမည်၊ Single Video ဆိုလျှင် မူရင်းပုံအတိုင်း သုံးမည်
        if is_playlist:
            # Playlist ထဲရှိ video အရေအတွက်ကို ရယူမည်
            entries = self.info.get("entries", [])

            if isinstance(entries, (list, tuple)):
                total_items = len(entries)
            else:
                total_items = 0

            processed_pixmap = self.create_stacked_playlist_thumbnail(
                pixmap,
                total_items=total_items
            )
        else:
            # Single video ဖြစ်လျှင် မူရင်းပုံအတိုင်း ပြမည်
            processed_pixmap = ThumbnailService.scale_for_label(pixmap)

        self.c_thumbnail = processed_pixmap

        if hasattr(self, 'spinner'):
            self.spinner.stop()
        if hasattr(self, 'lblThumbnail'):
            self.lblThumbnail.clear()

        # Privacy Mode ဖြစ်နေရင် မူရင်း Thumbnail ကို မပြဘဲ Privacy Thumbnail ပြမည်
        is_privacy = getattr(self, 'is_privacy_mode', False)
        if is_privacy:
            self.display_privacy_thumbnail()
        else:
            # Normal Mode: သင့်လျော်သော thumbnail ကို ပြသခြင်း
            self.lblThumbnail.setPixmap(processed_pixmap)

        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage("Fetch Info successful. Thumbnail ready.")

    def on_thumbnail_failed(self, reason):
        self.thumbnail_success = False
        self.thumbnail_failed = True
        
        # ✨ Thumbnail ကျရှုံးပါက c_thumbnail ကို None ပြန်လုပ်မည်
        self.c_thumbnail = None

        # Spinner ကို ရပ်ပြီး ဖျောက်မည်
        self.spinner.stop()

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
        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False)
        pixmap = self.lblThumbnail.pixmap()
        # Pixel Image မရှိ၊ Privacy Mode ဖြစ်နေရင် ဆက်မလုပ်ပဲပြန်
        if not pixmap or pixmap.isNull() or is_privacy:
            return

        # fetched လုပ်ထားတဲ့ Info က None ဖြစ်နေရင် ဆက်မလုပ်ပဲပြန်
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
        """ FetchController.fetch_started """
        pass

    def on_fetch_completed(self, info):
        """ FetchController.fetch_completed — JSON parse အောင်မြင် """
        self.getInfoButton.setText("Fetch Info")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", False)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()
        
        # Load Settings
        loaded_settings = getattr(self, "loaded_settings", {})

        self.info = info

        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False)

        # ------------------------------------------------------------------
        # ✨ Playlist လား၊ Single Video လား ခွဲခြားပြီး UI Display ပြမည့်အပိုင်း
        # ------------------------------------------------------------------
        if isinstance(info, dict) and (info.get("_type") == "playlist" or "entries" in info):
            self.display_playlist_info(info, is_privacy, loaded_settings)
        else:
            self.display_video_info()
            current_url = self.c_urlInput  
            if current_url and isinstance(info, dict):
                self.db_mgr.save_or_update_fetch(current_url, info)

            self.statusbar.showMessage("Video information fetched successfully.")
            logger.info("Fetch completed")

        # ------------------------------------------------------------------
        # 🔄 နှစ်ခုစလုံးအတွက် အတူတူလုပ်ရမယ့် Common Logic များ
        # ------------------------------------------------------------------

        if self.download_controller.is_running():
            self.set_controls_status(UiState.DOWNLOADING)
        else:
            # တကယ်လို့ Playlist ဖြစ်ပြီး Auto-Download On ထားရင် Download State ပေးချင်ရင် ဒါကို ညှိပေးလို့ရပါတယ်
            self.set_controls_status(UiState.FETCHING_FINISHED)

    def on_fetch_failed(self, error_message):
        """ FetchController.fetch_failed """
        self.getInfoButton.setText("Fetch Info")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", False)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()

        # Spinner ကို ရပ်ပြီး ဖျောက်မည်
        self.spinner.stop()

        # Unavailable Video လား စစ်ဆေး
        is_unavailable = "unavailable" in error_message

        self.statusbar.showMessage(StatusMsg.FETCH_FAILED)
        self.lblThumbnail.setMovie(None)
        if is_unavailable:
            self.display_unavailable_thumbnail()
        else:
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
        """ FetchController.cookies_required """
        self.getInfoButton.setText("Fetch Info")
        self.getInfoButton.setEnabled(True)
        self.getInfoButton.setProperty("working", False)
        self.getInfoButton.style().unpolish(self.getInfoButton)
        self.getInfoButton.style().polish(self.getInfoButton)
        self.getInfoButton.update()

        # Spinner ကို ရပ်ပြီး ဖျောက်မည်
        self.spinner.stop()

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
        """ DownloadController.download_started """
        pass

    def on_download_log(self, log_text):
        """ DownloadController.download_log """
        # Single Video Download လုပ်မှ log ကိုပြ၊ Playlist ဆိုရင် log ကို ရှင်းလင်းအောင်လို့
        if self.single_video_download:
            self.txtInfoLog.insertPlainText(log_text)
            self.txtInfoLog.ensureCursorVisible()

    def on_download_destination_changed(self, path):
        """ DownloadController.download_destination_changed """
        self.final_downloaded_path = path
        self.taskbar_service.reset()
        self.taskbar_service.set_downloading(0, 100, "downloading")
        logger.debug(f"Download destination: {path}")

    def on_download_progress(self, percent, status_text):
        """ DownloadController.download_progress """
        if self.is_marquee:
            self.marquee_progressbar(False)
            self.is_marquee = False

        self.progressBar.setValue(percent)
        self.statusbar.showMessage(status_text)
        self.taskbar_service.set_downloading(percent, 100, "downloading")

    def on_download_indeterminate(self):
        """ DownloadController.download_indeterminate """
        if not self.is_marquee:
            self.marquee_progressbar(True)
            self.is_marquee = True
        self.taskbar_service.reset()
        self.taskbar_service.set_indeterminate()

    def on_download_progress_resumed(self):
        """ DownloadController.download_progress_resumed — marquee ရပ် """
        if self.is_marquee:
            self.marquee_progressbar(False)
            self.is_marquee = False

    def on_download_completed(self, final_path):
        """ DownloadController.download_completed """
        self.final_downloaded_path = final_path
        
        # ✨ အကယ်၍ Queue (Playlist) ဖြင့် ဒေါင်းလုဒ်လုပ်နေခြင်း ဖြစ်ပါက 
        # တစ်ပုဒ်ချင်းစီ ပြီးဆုံးချိန်တွင် UI ကို ချက်ချင်း Reset မလုပ်ဘဲ QueueController သို့သာ အလုပ်ဆက်လုပ်ခွင့်ပေးမည်
        if hasattr(self, 'queue_controller') and self.queue_controller.is_running():
            logger.info(f"Queue task completed: {final_path}")
            return

        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False)

        # [SQLite] Download Success ဖြစ်ကြောင်း DB ထဲမှာ Status Update လုပ်
        current_url = self.c_urlInput   # self.urlInput.text().strip()
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

        # video_title = self.lblTitle.text() or "Video"
        # video_title = self.c_title
        video_title = self.c_title if not is_privacy else "🔒 *************************"

        if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_COMPLETED):
            self.notification_service.send_notification(
                "Download Completed!",
                f"{video_title}",
                file_path=self.final_downloaded_path
            )

        if loaded_settings.get(ConfigKey.PLAY_AFTER_DOWNLOADED):
            if self.final_downloaded_path:
                url = QUrl.fromLocalFile(self.final_downloaded_path)
                success = QDesktopServices.openUrl(url)
                if not success:
                    logger.warning(
                        f"Play failed: {self.final_downloaded_path} not found"
                    )

    def on_download_failed(self, error_message):
        """ DownloadController.download_failed """
        # ✨ အကယ်၍ Queue (Playlist) ဖြင့် ဒေါင်းလုဒ်လုပ်နေခြင်း ဖြစ်ပါက 
        # တစ်ပုဒ်ချင်းစီ Error တက်ချိန်တွင် UI ကို ချက်ချင်း Reset မလုပ်ဘဲ
        # QueueController သို့သာ အလုပ်ဆက်လုပ်ခွင့်ပေးမယ်
        if hasattr(self, 'queue_controller') and self.queue_controller.is_running():
            logger.info(f"Queue task failed: {error_message}")
            return
        
        # [SQLite] Download Error ဖြစ်ကြောင်း DB ထဲမှာ Status Update လုပ်
        current_url = self.c_urlInput   # self.urlInput.text().strip()
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
        """ DownloadController.download_cancelled """
        # [SQLite] User ဘက်မှ Download ကို မပြီးမီ Cancel လုပ်လိုက်ကြောင်း Update လုပ်
        current_url = self.c_urlInput   # self.urlInput.text().strip()
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
    # 🔍 FETCH INFO
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
            "<a href=\"https://github.com/YawStar/Smart-Cookies\">"
            "YawStar Cookies Exporter</a>."
        )

        # TextInteractionFlags တွင် Interaction Flag ကိုသာ ထည့်သွင်း
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

    def on_fetch_info_clicked(self):
        """ Fetch Info — FetchController ကို delegate """
        self.stop_tips_rotation()

        # Stop fetching
        if self.fetch_controller.is_running():
            self.statusbar.showMessage(StatusMsg.CANCELLING_FETCH)
            self.getInfoButton.setEnabled(False)
            self.fetch_controller.cancel()
            # Spinner ကို ရပ်ပြီး ဖျောက်မည်
            self.spinner.stop()
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

        # Privacy Mode status စစ်ဆေးခြင်း
        is_privacy = getattr(self, 'is_privacy_mode', False)
        if is_privacy:
            url = self.c_urlInput
            if not url:
                self.statusbar.showMessage("Please enter a valid URL.")
                return
        else:
            url = self.urlInput.text().strip() # Get InputURL
            if not url:
                self.statusbar.showMessage("Please enter a valid URL.")
                return
            
        self.c_urlInput = url # Current Url ကို သိမ်းဆည်း

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

        # Spinner ကို ရပ်ပြီး ဖျောက်မည်
        self.lblThumbnail.clear()
        self.spinner.stop()
        self.spinner.start()

        # Config Manager မှတစ်ဆင့် last_added_url ကို စနစ်တကျ ပြင်ဆင်ပြီး Load လုပ်မည်
        self.config_mgr.set(ConfigKey.LAST_ADDED_URL, url)
        global loaded_settings
        loaded_settings = self.config_mgr.get_all()
        self.loaded_settings = loaded_settings

        # yt-dlp path check
        yt_dlp_path = self.yt_dlp_service.yt_dlp_path
        if not os.path.exists(yt_dlp_path):
            self.statusbar.showMessage("yt-dlp executable not found.")
            logger.error("yt-dlp not found")

            # Spinner ကို ရပ်ပြီး ဖျောက်မည်
            self.spinner.stop()

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

        # ------------------------------------------------------------------
        # ✨ Playlist Detection (URL ထဲတွင် list= ပါဝင်ခြင်း သို့မဟုတ် /playlist ပါခြင်း သို့ /show/ )
        # ------------------------------------------------------------------
        is_playlist = "list=" in url.lower() or "/playlist" in url.lower() or "/show/" in url.lower()

        # Playlist ဖြစ်ရင် Status bar Message ပုံစံပြောင်းလဲ
        if is_playlist:
            self.statusbar.showMessage(StatusMsg.FETCHING_PLAYLIST)
        else:
            self.statusbar.showMessage(StatusMsg.FETCHING)
        
        # Log ထုတ်ပေး
        logger.info(f"Fetching: {url}")

        # ✨ Controller start (is_playlist flag ထည့်သွင်းပေးခြင်း)
        self.fetch_controller.start(url, loaded_settings, is_playlist=is_playlist)

    # =========================================================================
    # Display Video Info
    # =========================================================================
    def display_video_info(self):
        """ Video Metadata များကို UI တွင် Display ပြပေးသည့် Method (Privacy Aware & Auto-Download Supported) """
        try:
            info = self.info
            if not isinstance(info, dict):
                raise ValueError("Video information is not valid.")

            # Privacy Mode status စစ်ဆေး
            is_privacy = getattr(self, 'is_privacy_mode', False)
            
            # ---------------------------------------------------------
            # 1. Title Processing
            # ---------------------------------------------------------
            fullTitleStr = info.get("fulltitle", info.get("title", "Unknown Title"))
            if not isinstance(fullTitleStr, str):
                fullTitleStr = str(fullTitleStr)

            # Store clean title value
            self.c_title = fullTitleStr[:120] if len(fullTitleStr) >= 120 else fullTitleStr

            if hasattr(self, 'lblTitle'):
                if is_privacy:
                    self.lblTitle.setText("🔒 *************************")
                else:
                    self.lblTitle.setText(self.c_title)

            # ---------------------------------------------------------
            # 2. Duration & Live Status
            # ---------------------------------------------------------
            # Change lblDurationTag Text
            self.lblDurationTag.setText("Duration: ")

            duration_secs = info.get("duration") or 0
            try:
                seconds = int(duration_secs)
            except (TypeError, ValueError):
                seconds = 0
            
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            if hours > 0:
                formatted_duration = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                formatted_duration = f"{minutes}:{seconds:02d}"

            # Live Stream Check
            is_live = info.get("is_live", False)
            if is_live:
                self.c_duration = "🔴 LIVE"
                if hasattr(self, 'lblDurationVal'):
                    self.lblDurationVal.setText("🔴 LIVE")
                if hasattr(self, 'downloadButton'):
                    self.downloadButton.setEnabled(False)
            else:
                self.c_duration = formatted_duration
                if hasattr(self, 'lblDurationVal'):
                    self.lblDurationVal.setText(formatted_duration)
                if hasattr(self, 'downloadButton'):
                    self.downloadButton.setEnabled(True)

            # ---------------------------------------------------------
            # 3. Chapters Processing
            # ---------------------------------------------------------            
            chapters = info.get("chapters") or []
            self.c_chapters = "None" if len(chapters) < 1 else str(len(chapters))
            if hasattr(self, 'lblChaptersVal'):
                self.lblChaptersVal.setText(self.c_chapters)

            # ---------------------------------------------------------
            # 4. Uploader / Channel Name Processing
            # ---------------------------------------------------------
            uploader = info.get("uploader") or info.get("channel") or "Unknown"
            self.c_uploader = str(uploader)
            self.uploader_url = info.get("uploader_url") or info.get("channel_url")

            if hasattr(self, 'lblUploaderVal'):
                if is_privacy:
                    self.lblUploaderVal.setText("🔒 *******")
                else:
                    self.lblUploaderVal.setText(self.c_uploader)

                if self.uploader_url and not is_privacy:
                    self.lblUploaderVal.setCursor(Qt.CursorShape.PointingHandCursor)
                    self.lblUploaderVal.setToolTip(f"Open link: {self.uploader_url}")
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

            # ---------------------------------------------------------
            # 5. Upload Date Processing
            # ---------------------------------------------------------
            upload_date = info.get("upload_date", "Unknown")
            if (isinstance(upload_date, str) and len(upload_date) == 8 and upload_date.isdigit()):
                upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

            self.c_upload_date = str(upload_date)
            if hasattr(self, 'lblUploadDateVal'):
                self.lblUploadDateVal.setText(self.c_upload_date)

            # ---------------------------------------------------------
            # 6. Description Text Processing
            # ---------------------------------------------------------
            desc_text = info.get("description", "No description available.") or "No description available."
            self.original_description = str(desc_text)
            html_text = description_to_html(desc_text)
            self.c_description = self.original_description
            if hasattr(self, 'txtInfoLog') and not self.download_controller.is_running():
                if is_privacy:
                    self.txtInfoLog.setHtml("<i>🔒 Description hidden in Privacy Mode.</i>")
                else:
                    self.txtInfoLog.setHtml(html_text)

            # ---------------------------------------------------------
            # 7. Thumbnail Handling & Fetching
            # ---------------------------------------------------------
            self.thumbnail_success = False
            self.thumbnail_failed = False
            thumbnail_url = info.get("thumbnail")

            if hasattr(self, 'lblThumbnail'):
                self.lblThumbnail.setScaledContents(False)

            if thumbnail_url:
                # Proxy Settings ကို စစ်
                use_proxy = self.config_mgr.get("use_proxy", False)
                proxy_type = self.config_mgr.get("proxy_type", "SOCKS5")
                proxy_host = self.config_mgr.get("proxy_host", "127.0.0.1")
                proxy_port = self.config_mgr.get("proxy_port", 2080)
                proxy_auth_name = self.config_mgr.get("proxy_auth_name", "")
                proxy_auth_password = self.config_mgr.get("proxy_auth_password", "")

                if use_proxy:
                    # Manual proxy သတ်မှတ် (service ဖန်တီးပြီးမှ ခေါ်ရမယ်)
                    if proxy_type == "HTTPS" or proxy_type == "HTTP":
                        if not proxy_auth_name == "" and not proxy_auth_password == "":
                            self.thumbnail_service.set_proxy(
                            host=proxy_host,
                            port=proxy_port,
                            proxy_type=QNetworkProxy.ProxyType.HttpProxy,
                            user=proxy_auth_name, password=proxy_auth_password,   # Aut and Pass
                            )
                        else:
                            self.thumbnail_service.set_proxy(
                            host=proxy_host,
                            port=proxy_port,
                            proxy_type=QNetworkProxy.ProxyType.HttpProxy,
                            )

                    if proxy_type == "SOCKS5":
                        if not proxy_auth_name == "" and not proxy_auth_password == "":
                            self.thumbnail_service.set_proxy(
                            host=proxy_host, port=proxy_port,
                            proxy_type=QNetworkProxy.ProxyType.Socks5Proxy,
                            user=proxy_auth_name, password=proxy_auth_password,   # Aut and Pass
                            )
                        else:
                            self.thumbnail_service.set_proxy(
                            host=proxy_host, port=proxy_port,
                            proxy_type=QNetworkProxy.ProxyType.Socks5Proxy,
                            )

                else:
                    # System Proxy (OS ရဲ့ settings ကို သုံး)
                    self.thumbnail_service.use_system_proxy(True)

                thumbnail_url = str(thumbnail_url)
                current_request_id = getattr(self, "thumbnail_request_id", 0)
                if hasattr(self, 'thumbnail_service'):
                    self.thumbnail_service.request(thumbnail_url, current_request_id)
            else:
                self.thumbnail_success = False
                self.thumbnail_failed = True
                self.c_thumbnail = None

                if hasattr(self, 'spinner'):
                    self.spinner.stop()

                if hasattr(self, 'lblThumbnail'):
                    self.lblThumbnail.setMovie(None)
                    self.display_default_thumbnail()

                if hasattr(self, 'statusbar'):
                    self.statusbar.showMessage("Fetch Info successful. Thumbnail is not available.")

            # ---------------------------------------------------------
            # 8. Privacy Original Data Backup
            # ---------------------------------------------------------
            if is_privacy:
                current_pixmap = self.lblThumbnail.pixmap() if hasattr(self, 'lblThumbnail') else None
                self._privacy_original_data = {
                    "title": self.c_title,
                    "uploader": self.c_uploader,
                    "url": self.urlInput.text() if hasattr(self, 'urlInput') else "",
                    "log": self.c_description,
                    "thumbnail": QPixmap(current_pixmap) if current_pixmap and not current_pixmap.isNull() else None,
                }
                self.urlInput.setText("🔒 ****************")
            else:
                self.urlInput.setText(self.c_urlInput)

            # Taskbar Reset
            if hasattr(self, 'taskbar_service'):
                self.taskbar_service.reset()

            # ---------------------------------------------------------
            # 9. Notification & Auto-Download Triggers
            # ---------------------------------------------------------
            loaded_settings = getattr(self, "loaded_settings", {})

            # Send Notification if Enabled
            if (loaded_settings.get(ConfigKey.NOTIFY_FETCHED) and 
                not loaded_settings.get(ConfigKey.AUTO_START_DOWNLOAD)):
                
                video_title = self.c_title if not is_privacy else "🔒 *************************"
                if hasattr(self, 'notification_service'):
                    self.notification_service.send_notification(
                        "Video Info Fetched",
                        f"{video_title}"
                    )

            # Trigger Auto Download if Enabled
            if loaded_settings.get(ConfigKey.AUTO_START_DOWNLOAD):
                if hasattr(self, 'download_controller') and not self.download_controller.is_running():
                    if hasattr(self, 'on_download_clicked'):
                        self.on_download_clicked()

        except Exception as e:
            error_message = "Error displaying video information: " + str(e)
            logger.exception(error_message)
            if hasattr(self, 'txtInfoLog'):
                self.txtInfoLog.setPlainText(error_message)

            if hasattr(self, 'statusbar'):
                self.statusbar.showMessage("Failed to display video information.")

            if hasattr(self, 'spinner'):
                self.spinner.stop()

            if hasattr(self, 'lblThumbnail'):
                self.lblThumbnail.setMovie(None)
                self.display_default_thumbnail()

            if hasattr(self, 'download_controller') and not self.download_controller.is_running():
                if hasattr(self, 'set_controls_status'):
                    self.set_controls_status(UiState.FETCHING_ERROR)

            if hasattr(self, 'taskbar_service'):
                self.taskbar_service.reset()

    # =========================================================================
    # Display Playlist Info
    # =========================================================================
    def display_playlist_info(self, info, is_privacy, loaded_settings):
        """ Playlist Metadata များကို UI တွင် Display ပြပေးသည့် Method (Dialog မဖွင့်ပါ) """
        if hasattr(self, 'spinner'):
            self.spinner.stop()

        if hasattr(self, 'taskbar_service'):
            self.taskbar_service.reset()

        playlist_title = info.get("title", "YouTube Playlist")
        entries = info.get("entries", [])
        total_items = len(entries) if isinstance(entries, (list, tuple)) else 0
        
        # Change lblDurationTag Text
        self.lblDurationTag.setText("Total Items: ")

        self.c_title = f"✨ Playlist: {playlist_title}"
        if hasattr(self, 'lblTitle') and not is_privacy:
            self.lblTitle.setText(f"✨ Playlist: {playlist_title}")
        else:
            self.lblTitle.setText("🔒 *************************")
            
        if hasattr(self, 'lblDurationVal'):
            self.lblDurationVal.setText(f"{total_items} Videos")

        self.c_uploader = info.get("uploader", "Unknown")
        if hasattr(self, 'lblUploaderVal') and not is_privacy:
            self.lblUploaderVal.setText(info.get("uploader", "Unknown"))
        else:
            self.lblUploaderVal.setText("🔒 *******")
            
        if hasattr(self, 'lblUploadDateVal'):
            self.lblUploadDateVal.setText("Playlist")
        
        if hasattr(self, 'txtInfoLog') and not self.download_controller.is_running():
            html_content = f"<b>Playlist Loaded:</b> {playlist_title}<br><b>Total Items:</b> {total_items} videos found.<br><i>Click the 'Download' button below to select videos and start downloading.</i>"
            self.c_description = None  
            self._playlist_html_message = html_content  
            if is_privacy:
                self.txtInfoLog.setHtml("<i>🔒 Description hidden in Privacy Mode.</i>")
            else:
                self.txtInfoLog.setHtml(html_content)
            
        # Playlist Thumbnail ရယူရန်
        thumb_url = None
        current_url = self.c_urlInput
        
        if current_url:
            playlist_db_info = {
                "title": f"📂 Playlist: {playlist_title} ({total_items} items)",
                "uploader": info.get("uploader", "YouTube"),
                "upload_date": "Playlist"
            }
            self.db_mgr.save_or_update_fetch(current_url, playlist_db_info)
            
        if entries and isinstance(entries, list):
            first_entry = entries[0]
            if isinstance(first_entry, dict):
                vid_id = first_entry.get("id")
                if vid_id:
                    thumb_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                else:
                    thumb_url = first_entry.get("thumbnail")

        if thumb_url and hasattr(self, 'thumbnail_service'):
            self._playlist_total_items = total_items
            current_request_id = getattr(self, "thumbnail_request_id", 0)
            self.thumbnail_service.request(str(thumb_url), current_request_id)
        else:
            self.display_default_thumbnail()

        # Notification if Enabled
        if loaded_settings.get(ConfigKey.NOTIFY_FETCHED):
            video_title = self.c_title if not is_privacy else "🔒 *************************"
            if hasattr(self, 'notification_service'):
                self.notification_service.send_notification(
                    "Video Info Fetched",
                    f"{video_title}"
                )

        # Fetch ပြီးသွားလျှင် UI ကို Normal အခြေအနေသို့ ပို့ပေးမည် (ခလုတ်များ နှိပ်လို့ရအောင်)
        self.set_controls_status(UiState.NORMAL)
        self.statusbar.showMessage("Ready")

    # =========================================================================
    # Queue Management
    # =========================================================================
    def on_queue_task_updated(self, index: int, task):
        """ Queue ထဲရှိ Task တစ်ခုချင်းစီ၏ Progress နှင့် Status ပြောင်းလဲမှုကို UI တွင် ပြသရန် """
        # လက်ရှိ ဒေါင်းလုဒ်လုပ်နေသော task ဖြစ်မှသာ Progressbar ကို တင်ပေးမည်
        logger.info(f"{task.title} --- {task.status}")
        if task.status == "Downloading":
            self.progressBar.setValue(task.progress)
            self.statusbar.showMessage(f"[{index + 1}/{len(self.queue_controller.tasks)}] Downloading: {task.title} ({task.progress}%)")
        elif task.status == "Completed":
            # တစ်ပုဒ်ပြီးသွားတိုင်း Notification/Status ကို ချက်ချင်း မပြဘဲ Queue တစ်ခုလုံး ပြီးမှပြရန်
            self.txtInfoLog.insertPlainText(f"[{index + 1}] {task.title} --- ✅\n")
            self.txtInfoLog.ensureCursorVisible() # Scroll bar အောက်ရောက်အောင်
        elif task.status == "Failed":
            self.txtInfoLog.insertPlainText(f"[{index + 1}] {task.title} --- ❌\n")
            self.txtInfoLog.ensureCursorVisible() # Scroll bar အောက်ရောက်အောင်

    def on_queue_started(self):
        """ Playlist Queue စတင်ဒေါင်းလုဒ်လုပ်သည့်အခါ UI ကို Download State သို့ ပြောင်းမည် """
        self.set_controls_status(UiState.DOWNLOADING)
        self.downloadButton.setText("Stop Download")
        self.progressBar.setVisible(True)
        if not self.is_marquee:
            self.marquee_progressbar(True)
            self.is_marquee = True

        self.downloadButton.setProperty("working", True)
        self.downloadButton.style().unpolish(self.downloadButton)
        self.downloadButton.style().polish(self.downloadButton)
        self.downloadButton.update()
        
        self.statusbar.showMessage("Playlist download queue started...")
        logger.info("Playlist queue download started")

    def on_queue_finished(self):
        """ Playlist Queue အားလုံး လုံးဝ ပြီးဆုံးမှသာ တစ်ကြိမ်တည်း ခေါ်ရန် """
        # Awake mode ဖွင့်ထားရင် ပိတ်ရန်
        if hasattr(self, 'awake_mode') and self.awake_mode:
            try:
                self.awake_mode.__exit__(None, None, None)
                self.awake_mode = None
            except Exception:
                pass

        # အကယ်၍ User က Cancel လုပ်ထားခြင်းဖြစ်ပါက Notification မပြဘဲ ရပ်ရန်
        if hasattr(self, 'queue_controller') and getattr(self.queue_controller, '_is_cancelled', False):
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
            self.statusbar.showMessage("Playlist download cancelled.")
            return
        
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
        
        # # ✨ အကယ်၍ Playlist Message သိမ်းထားတာ ရှိရင် အဲ့ဒါကိုပဲ ပြန်ပြမယ်
        # if hasattr(self, '_playlist_html_message') and self._playlist_html_message:
        #     self.txtInfoLog.setHtml(self._playlist_html_message)
        # else:
        #     org_desc = str(getattr(self, 'c_description', ''))
        #     if org_desc and org_desc != "None":
        #         html_text = description_to_html(org_desc)
        #         self.txtInfoLog.setHtml(html_text)
        #     else:
        #         self.txtInfoLog.setHtml("")

        # Process ပြီးဆုံးကြောင်း Plain Text ကို ထည့်
        self.txtInfoLog.insertPlainText(
                                "✦-------------------- Playlist Download Process Finished --------------------✦\n"
                            )
        
        # နောက်ဆုံး စာကြောင်းပေါ်အောင်လုပ်
        self.txtInfoLog.ensureCursorVisible()

        # ✨ Playlist တစ်ခုလုံး အားလုံး ဒေါင်းပြီးမှသာ ဤစာသားကို တစ်ကြိမ်တည်း ပြမည်
        self.statusbar.showMessage("All items in playlist queue downloaded successfully!")
        logger.info("Playlist queue download finished completely")
        # Notification
        if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_COMPLETED):
            self.notification_service.send_notification(
                "Playlist Download Completed!",
                "Your download has been completed."
            )

    def start_playlist_download_from_entries(self, entries, loaded_settings):
        """ Playlist entries များမှတဆင့် Queue ဆောက်လုပ်ပြီး ဒေါင်းလုဒ် စတင်ပေးသည့် Method """
        tasks = []
        for entry in entries:
            video_url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
            title = entry.get("title", "Unknown Title")
            tasks.append(DownloadTask(title=title, url=video_url))

        self.queue_controller.clear_queue()
        self.queue_controller.add_tasks(tasks)
        self.queue_controller.start_queue(
            settings=loaded_settings,
            selected_format_id=self.selected_format_id,
            is_windows=(CURRENT_OS == "Windows")
        )
        self.statusbar.showMessage(f"Started queue download for {len(tasks)} items.")

    # =========================================================================
    # FORMAT SELECTION
    # =========================================================================
    def on_select_formats_clicked(self):
        """ Formats သို့မဟုတ် Playlist ခလုတ်ကို နှိပ်လိုက်သည့်အခါ """
        if self.info is None:
            self.statusbar.showMessage(
                "No video information available. Please fetch info first."
            )
            return

        # # 📂 Playlist ဖြစ်မဖြစ် စစ်ဆေးခြင်း
        # is_playlist = isinstance(self.info, dict) and (self.info.get("_type") == "playlist" or "entries" in self.info)

        # if is_playlist:
        #     # Playlist Dialog ကို ပြန်ပြရန်
        #     dialog = PlaylistDialog(self.info, parent=self)
        #     if self.show_dialog_with_blur(dialog) == QDialog.Accepted:
        #         selected_entries = dialog.get_selected_entries()
        #         if selected_entries:
        #             from controllers.queue_controller import DownloadTask
        #             tasks = []
        #             for entry in selected_entries:
        #                 video_url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
        #                 title = entry.get("title", "Unknown Title")
        #                 tasks.append(DownloadTask(title=title, url=video_url))

        #             self.queue_controller.clear_queue()
        #             self.queue_controller.add_tasks(tasks)

        #             self.queue_controller.start_queue(
        #                 settings=self.config_mgr.get_all(),
        #                 selected_format_id=self.selected_format_id,
        #                 is_windows=(CURRENT_OS == "Windows")
        #             )
        #             self.statusbar.showMessage(f"Started queue download for {len(tasks)} items.")
        #     return

        # Single Video အတွက် FormatDialog Logic
        current_id = getattr(self, 'selected_format_id', None)
        dialog = FormatDialog(
            self.info, current_format_id=current_id, parent=self
        )

        if self.show_dialog_with_blur(dialog) == QDialog.DialogCode.Accepted:
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
    # ⬇️ DOWNLOAD
    # =========================================================================
    def on_download_clicked_BAK(self):
        """ Download — DownloadController သို့မဟုတ် QueueController ကို delegate """
        # Tip Rotation ပြတာရပ်
        self.stop_tips_rotation()
        
        # Playlist Queue အလုပ်လုပ်နေရင် Queue ကို ရပ်ရန်
        if hasattr(self, 'queue_controller') and self.queue_controller.is_running():
            self.statusbar.showMessage("Playlist download cancelled.")
            self.queue_controller.stop_queue()
            self.on_queue_finished()
            return

        # Single Video Download အလုပ်လုပ်နေရင် Stop download
        if self.download_controller.is_running():
            self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
            self.download_controller.cancel()
            return

        # Dependencies တွေရှိမရှိ စစ်မယ်
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

        # URL ရှိမရှိစစ်မယ်
        url = self.c_urlInput 
        if not url:
            self.statusbar.showMessage("Please enter a valid URL.")
            logger.error("Please enter a valid URL.")
            return
        
        # Config တွေကိုဖတ်မယ်
        loaded_settings = self.config_mgr.get_all()

        # Awake Mode ဖွင့်ထားမထား ဖတ်မယ်
        prevent_sleep_while_dloading = loaded_settings.get(
            ConfigKey.AWAKE_MODE, False
        )

        # Download Path ကို ဖတ်မယ်
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
        skip_sponsors_block = self.skipSponsorsButton.isChecked()

        # ရွေးချယ်ထားသော subtitle များကို ဖတ်ယူခြင်း
        selected_subs = getattr(self, 'selected_subtitles_list', [])
        sub_langs = []
        for sub in selected_subs:
            import re
            # ကွင်းစကွင်းပိတ် ( ) ထဲတွင် ရှိသော ကုဒ်ကို ရှာရန် (ဥပမာ: (my) သို့မဟုတ် (en) စသည်)
            match = re.search(r'\(([a-z\-]+)\)', sub)
            if match:
                lang_code = match.group(1)
                if lang_code not in sub_langs:
                    sub_langs.append(lang_code)
        
        print(f"Selected Sub Lang = {sub_langs}")
        logger.info(f"Selected Sub Langs for yt-dlp: {sub_langs}")
        
        # ---------------------------------------------------------
        # 💡 ဤနေရာတွင် gui_overrides ထဲသို့ sub_langs ကို ထည့်ပေးရန်
        # ---------------------------------------------------------
        gui_overrides = {
            "embed_thumbnail": embedded_thumbnail,
            "embed_chapters": embedded_chapters,
            "embed_subtitles": embedded_subtitle,
            "embed_metadata": embedded_metadata,
            "use_mtime": use_mtime,
            "skip_sponsors_block": skip_sponsors_block,
            "sub_langs": sub_langs,              # 👈 ဤနေရာတွင် ထည့်ပေးပါ
        }
        

        # Config မှာထည့်ဖို့ Value တွေပြင်ဆင်
        updated_data = {
            ConfigKey.EMBED_THUMBNAIL: embedded_thumbnail,
            ConfigKey.EMBED_CHAPTERS: embedded_chapters,
            ConfigKey.EMBED_SUBTITLES: embedded_subtitle,
            ConfigKey.EMBED_METADATA: embedded_metadata,
            ConfigKey.USE_MTIME: use_mtime,
            ConfigKey.SKIP_SPONSORS_BLOCK: skip_sponsors_block,
        }
        # Config မှာ Value တွေထည့်သွင်း
        self.config_mgr.update_multiple(updated_data)
    
        # =====================================================================
        # ✨ Playlist ဖြစ်နေရင် Download ခလုတ်နှိပ်မှသာ Dialog ပြပြီး Queue စတင်မည်
        # =====================================================================
        is_playlist = isinstance(self.info, dict) and (self.info.get("_type") == "playlist" or "entries" in self.info)
        if is_playlist:
            self.single_video_download = False
            entries = self.info.get("entries", [])
            dialog = PlaylistDialog(self.info, parent=self)
            result = self.show_dialog_with_blur(dialog)
            
            if result == QDialog.Accepted:
                selected_entries = dialog.get_selected_entries()
                if selected_entries:
                    # Notification
                    if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_STARTED):
                        self.notification_service.send_notification(
                            "Playlist Download Started",
                            "Your download has been started."
                        )

                    # Taskbar
                    self.taskbar_service.reset()
                    self.taskbar_service.set_indeterminate()
                    
                    # LogOutput ကိုရှင်းပြီး Plain Text ကို ထည့်
                    self.txtInfoLog.clear()
                    self.txtInfoLog.insertPlainText(
                        "✦-------------------- Playlist Download Process Started --------------------✦\n"
                    )

                    # နောက်ဆုံး စာကြောင်းပေါ်အောင်လုပ်
                    self.txtInfoLog.ensureCursorVisible()

                    # Download လုပ်မယ့် Url ကို log ထုတ်ပေး
                    logger.info(f"Playlist Download started: {url}")

                    # Config မှာ Playlist Own Folder ရွေးထားမထား စစ်
                    put_playlist_their_own_dir = loaded_settings.get("playlist_in_own_folder", False)
                    if put_playlist_their_own_dir:
                        playlist_title = self.info.get("title", "Playlist")
                        # 📁 Windows/Linux Path များတွင် မပါသင့်သော Special Characters များကို ဖယ်ရှားရန် (Sanitize)
                        safe_playlist_title = re.sub(r'[\\/*?:"<>|]', "", playlist_title).strip()
                        if not safe_playlist_title:
                            safe_playlist_title = "Playlist"
                        channel_name = self.c_uploader
                        # 📁 Windows/Linux Path များတွင် မပါသင့်သော Special Characters များကို ဖယ်ရှားရန် (Sanitize)
                        safe_channel_id = re.sub(r'[\\/*?:"<>|]', "", channel_name).strip()
                        if not safe_channel_id:
                            safe_channel_id = "Channel_ID"
                        download_path_cfg = os.path.join(download_path_cfg, f"{safe_channel_id}_{safe_playlist_title}")
        
                    # Download Folder ကို မရှိရင် ဖန်တီး
                    if not os.path.exists(download_path_cfg):
                        os.makedirs(download_path_cfg)
                        
                    # Queue / Download Controller ဆီသို့ Path အသစ်ကို ပို့ပေးရန် Settings ကို Copy ကူးပြီး Update လုပ်မည်
                    playlist_settings = dict(loaded_settings)
                    playlist_settings[ConfigKey.DOWNLOAD_PATH] = download_path_cfg
                    
                    # Config မှာ Awake mode ကိုသုံးဖို့ရွေးထားရင် Awake Mode ဖွင့်
                    if prevent_sleep_while_dloading:
                        self.awake_mode = keep.running()
                        self.awake_mode.__enter__()

                    self.start_playlist_download_from_entries(selected_entries, playlist_settings)

                else:
                    self.statusbar.showMessage("No videos selected from playlist.")
                    self.set_controls_status(UiState.NORMAL)
            else:
                self.statusbar.showMessage("Playlist download cancelled.")
                self.set_controls_status(UiState.NORMAL)
                self.downloadButton.setText("Download")
                self.progressBar.setVisible(False)
                if self.is_marquee:
                    self.marquee_progressbar(False)
                    self.is_marquee = False

            return # Playlist ဖြစ်နေလို့ ဆက်မသွားတော့ပဲပြန်

        # =====================================================================
        # 🎥 Single Video အတွက် Download Logic များ
        # =====================================================================
        self.single_video_download = True
        # UI state
        self.set_controls_status(UiState.DOWNLOADING) # Control Button တွေကို Downloading State ပြင်
        self.downloadButton.setText("Stop Download") # Download Button ကို Stop Download စာသားပြောင်း
        self.progressBar.setValue(0) # Progressbar ရာခိုင်နှုန်းကို 0 ပြောင်း
        self.statusbar.showMessage(StatusMsg.DOWNLOAD_PREPARING) # Preparing လို့ ပြ

        self.progressBar.setVisible(True) # Progressbar ကို ဖျောက်ထားတာကနေ ပြန်ဖေါ်

        if not self.is_marquee: # Progressbar က Marquee မဟုတ်ရင် Marquee ပုံစံပြောင်း
            self.marquee_progressbar(True)
            self.is_marquee = True

        self.downloadButton.setProperty("working", True) # Download Button ရဲ့ Property ကို ပြင်
        self.downloadButton.style().unpolish(self.downloadButton) # Download Button ကို Unpolish လုပ်
        self.downloadButton.style().polish(self.downloadButton) # Download Button ကို Polish ပြန်လုပ်
        self.downloadButton.update() # Download Button ကို Update လုပ်
            
        # Config မှာ Start Download လုပ်ရင် Notification ကို ဖွင့်ထားလား စစ်ပြီး လုပ်ဆောင်
        if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_STARTED):
            self.notification_service.send_notification(
                "Download Started",
                "Your download has been started."
            )

        # Taskbar
        self.taskbar_service.reset()
        self.taskbar_service.set_indeterminate()

        # LogOutput ကိုရှင်းပြီး Plain Text ကို ထည့်
        self.txtInfoLog.clear()
        self.txtInfoLog.insertPlainText(
            "✦-------------------- Download Process Started "
            "--------------------✦\n"
        )
        # Cursor ကိုဖျောက်
        self.txtInfoLog.ensureCursorVisible()

        # Download လုပ်မယ့် Url ကို log ထုတ်ပေး
        logger.info(f"Download started: {url}")
        
        # Download Folder ကို မရှိရင် ဖန်တီး
        if not os.path.exists(download_path_cfg):
            os.makedirs(download_path_cfg)

        # Config မှာ Awake mode ကိုသုံးဖို့ရွေးထားရင် Awake Mode ဖွင့်
        if prevent_sleep_while_dloading:
            self.awake_mode = keep.running()
            self.awake_mode.__enter__()

        gui_overrides = {
            "embed_thumbnail": embedded_thumbnail,
            "embed_chapters": embedded_chapters,
            "embed_subtitles": embedded_subtitle,
            "embed_metadata": embedded_metadata,
            "use_mtime": use_mtime,
            "skip_sponsors_block": skip_sponsors_block,
        }

        # Controller start
        self.download_controller.start(
            url=url,
            settings=loaded_settings,
            selected_format_id=self.selected_format_id,
            gui_overrides=gui_overrides,
            is_windows=(CURRENT_OS == "Windows"),
        )

    def on_download_clicked(self):
        """ Download — DownloadController သို့မဟုတ် QueueController ကို delegate """
        # Tip Rotation ပြတာရပ်
        self.stop_tips_rotation()
        
        # Playlist Queue အလုပ်လုပ်နေရင် Queue ကို ရပ်ရန်
        if hasattr(self, 'queue_controller') and self.queue_controller.is_running():
            self.statusbar.showMessage("Playlist download cancelled.")
            self.queue_controller.stop_queue()
            self.on_queue_finished()
            return

        # Single Video Download အလုပ်လုပ်နေရင် Stop download
        if self.download_controller.is_running():
            self.statusbar.showMessage(StatusMsg.DOWNLOAD_CANCELLED)
            self.download_controller.cancel()
            return

        # Dependencies တွေရှိမရှိ စစ်မယ်
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

        # URL ရှိမရှိစစ်မယ်
        url = self.c_urlInput 
        if not url:
            self.statusbar.showMessage("Please enter a valid URL.")
            logger.error("Please enter a valid URL.")
            return
        
        # Config တွေကိုဖတ်မယ်
        loaded_settings = self.config_mgr.get_all()

        # Awake Mode ဖွင့်ထားမထား ဖတ်မယ်
        prevent_sleep_while_dloading = loaded_settings.get(
            ConfigKey.AWAKE_MODE, False
        )

        # Download Path ကို ဖတ်မယ်
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
        skip_sponsors_block = self.skipSponsorsButton.isChecked()

        # ရွေးချယ်ထားသော subtitle များကို ဖတ်ယူခြင်း
        selected_subs = getattr(self, 'selected_subtitles_list', [])
        sub_langs = []
        for sub in selected_subs:
            import re
            # ကွင်းစကွင်းပိတ် ( ) ထဲတွင် ရှိသော ကုဒ်ကို ရှာရန် (ဥပမာ: (my) သို့မဟုတ် (en) စသည်)
            match = re.search(r'\(([a-z\-]+)\)', sub)
            if match:
                lang_code = match.group(1)
                if lang_code not in sub_langs:
                    sub_langs.append(lang_code)
                    
        logger.info(f"Selected Sub Langs for yt-dlp: {sub_langs}")
        
        # ---------------------------------------------------------
        # 💡 ဤနေရာတွင် gui_overrides ထဲသို့ sub_langs ကို ထည့်ပေးရန်
        # ---------------------------------------------------------
        gui_overrides = {
            "embed_thumbnail": embedded_thumbnail,
            "embed_chapters": embedded_chapters,
            "embed_subtitles": embedded_subtitle,
            "embed_metadata": embedded_metadata,
            "use_mtime": use_mtime,
            "skip_sponsors_block": skip_sponsors_block,
            "sub_langs": sub_langs,
        }
        

        # Config မှာထည့်ဖို့ Value တွေပြင်ဆင်
        updated_data = {
            ConfigKey.EMBED_THUMBNAIL: embedded_thumbnail,
            ConfigKey.EMBED_CHAPTERS: embedded_chapters,
            ConfigKey.EMBED_SUBTITLES: embedded_subtitle,
            ConfigKey.EMBED_METADATA: embedded_metadata,
            ConfigKey.USE_MTIME: use_mtime,
            ConfigKey.SKIP_SPONSORS_BLOCK: skip_sponsors_block,
        }
        # Config မှာ Value တွေထည့်သွင်း
        self.config_mgr.update_multiple(updated_data)
    
        # =====================================================================
        # ✨ Playlist ဖြစ်နေရင် Download ခလုတ်နှိပ်မှသာ Dialog ပြပြီး Queue စတင်မည်
        # =====================================================================
        is_playlist = isinstance(self.info, dict) and (self.info.get("_type") == "playlist" or "entries" in self.info)
        if is_playlist:
            self.single_video_download = False
            entries = self.info.get("entries", [])
            dialog = PlaylistDialog(self.info, parent=self)
            result = self.show_dialog_with_blur(dialog)
            
            if result == QDialog.Accepted:
                selected_entries = dialog.get_selected_entries()
                if selected_entries:
                    # Notification
                    if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_STARTED):
                        self.notification_service.send_notification(
                            "Playlist Download Started",
                            "Your download has been started."
                        )

                    # Taskbar
                    self.taskbar_service.reset()
                    self.taskbar_service.set_indeterminate()
                    
                    # LogOutput ကိုရှင်းပြီး Plain Text ကို ထည့်
                    self.txtInfoLog.clear()
                    self.txtInfoLog.insertPlainText(
                        "✦-------------------- Playlist Download Process Started --------------------✦\n"
                    )

                    # နောက်ဆုံး စာကြောင်းပေါ်အောင်လုပ်
                    self.txtInfoLog.ensureCursorVisible()

                    # Download လုပ်မယ့် Url ကို log ထုတ်ပေး
                    logger.info(f"Playlist Download started: {url}")

                    # Config မှာ Playlist Own Folder ရွေးထားမထား စစ်
                    put_playlist_their_own_dir = loaded_settings.get("playlist_in_own_folder", False)
                    if put_playlist_their_own_dir:
                        playlist_title = self.info.get("title", "Playlist")
                        # 📁 Windows/Linux Path များတွင် မပါသင့်သော Special Characters များကို ဖယ်ရှားရန် (Sanitize)
                        safe_playlist_title = re.sub(r'[\\/*?:"<>|]', "", playlist_title).strip()
                        if not safe_playlist_title:
                            safe_playlist_title = "Playlist"
                        channel_name = self.c_uploader
                        # 📁 Windows/Linux Path များတွင် မပါသင့်သော Special Characters များကို ဖယ်ရှားရန် (Sanitize)
                        safe_channel_id = re.sub(r'[\\/*?:"<>|]', "", channel_name).strip()
                        if not safe_channel_id:
                            safe_channel_id = "Channel_ID"
                        download_path_cfg = os.path.join(download_path_cfg, f"{safe_channel_id}_{safe_playlist_title}")
        
                    # Download Folder ကို မရှိရင် ဖန်တီး
                    if not os.path.exists(download_path_cfg):
                        os.makedirs(download_path_cfg)
                        
                    # Queue / Download Controller ဆီသို့ Path အသစ်ကို ပို့ပေးရန် Settings ကို Copy ကူးပြီး Update လုပ်မည်
                    playlist_settings = dict(loaded_settings)
                    playlist_settings[ConfigKey.DOWNLOAD_PATH] = download_path_cfg
                    
                    # Config မှာ Awake mode ကိုသုံးဖို့ရွေးထားရင် Awake Mode ဖွင့်
                    if prevent_sleep_while_dloading:
                        self.awake_mode = keep.running()
                        self.awake_mode.__enter__()

                    self.start_playlist_download_from_entries(selected_entries, playlist_settings)

                else:
                    self.statusbar.showMessage("No videos selected from playlist.")
                    self.set_controls_status(UiState.NORMAL)
            else:
                self.statusbar.showMessage("Playlist download cancelled.")
                self.set_controls_status(UiState.NORMAL)
                self.downloadButton.setText("Download")
                self.progressBar.setVisible(False)
                if self.is_marquee:
                    self.marquee_progressbar(False)
                    self.is_marquee = False

            return # Playlist ဖြစ်နေလို့ ဆက်မသွားတော့ပဲပြန်

        # =====================================================================
        # 🎥 Single Video အတွက် Download Logic များ
        # =====================================================================
        self.single_video_download = True
        # UI state
        self.set_controls_status(UiState.DOWNLOADING) # Control Button တွေကို Downloading State ပြင်
        self.downloadButton.setText("Stop Download") # Download Button ကို Stop Download စာသားပြောင်း
        self.progressBar.setValue(0) # Progressbar ရာခိုင်နှုန်းကို 0 ပြောင်း
        self.statusbar.showMessage(StatusMsg.DOWNLOAD_PREPARING) # Preparing လို့ ပြ

        self.progressBar.setVisible(True) # Progressbar ကို ဖျောက်ထားတာကနေ ပြန်ဖေါ်

        if not self.is_marquee: # Progressbar က Marquee မဟုတ်ရင် Marquee ပုံစံပြောင်း
            self.marquee_progressbar(True)
            self.is_marquee = True

        self.downloadButton.setProperty("working", True) # Download Button ရဲ့ Property ကို ပြင်
        self.downloadButton.style().unpolish(self.downloadButton) # Download Button ကို Unpolish လုပ်
        self.downloadButton.style().polish(self.downloadButton) # Download Button ကို Polish ပြန်လုပ်
        self.downloadButton.update() # Download Button ကို Update လုပ်
            
        # Config မှာ Start Download လုပ်ရင် Notification ကို ဖွင့်ထားလား စစ်ပြီး လုပ်ဆောင်
        if loaded_settings.get(ConfigKey.NOTIFY_DOWNLOAD_STARTED):
            self.notification_service.send_notification(
                "Download Started",
                "Your download has been started."
            )

        # Taskbar
        self.taskbar_service.reset()
        self.taskbar_service.set_indeterminate()

        # LogOutput ကိုရှင်းပြီး Plain Text ကို ထည့်
        self.txtInfoLog.clear()
        self.txtInfoLog.insertPlainText(
            "✦-------------------- Download Process Started "
            "--------------------✦\n"
        )
        # Cursor ကိုဖျောက်
        self.txtInfoLog.ensureCursorVisible()

        # Download လုပ်မယ့် Url ကို log ထုတ်ပေး
        logger.info(f"Download started: {url}")
        
        # Download Folder ကို မရှိရင် ဖန်တီး
        if not os.path.exists(download_path_cfg):
            os.makedirs(download_path_cfg)

        # Config မှာ Awake mode ကိုသုံးဖို့ရွေးထားရင် Awake Mode ဖွင့်
        if prevent_sleep_while_dloading:
            self.awake_mode = keep.running()
            self.awake_mode.__enter__()

        gui_overrides = {
            "embed_thumbnail": embedded_thumbnail,
            "embed_chapters": embedded_chapters,
            "embed_subtitles": embedded_subtitle,
            "embed_metadata": embedded_metadata,
            "use_mtime": use_mtime,
            "skip_sponsors_block": skip_sponsors_block,
            "sub_langs": sub_langs,          # 👈 ဤနေရာတွင် Single Video အတွက် sub_langs ကို ထည့်သွင်းပေးထားပါသည်
        }

        # Controller start
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
            self.set_option_controls_status(False)
            self.urlInput.setEnabled(True)
            self.pasteButton.setEnabled(True)
            self.historyButton.setEnabled(True)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(False)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(True)
        elif method == UiState.FETCHING:
            self.set_option_controls_status(False)
            self.urlInput.setEnabled(False)
            self.pasteButton.setEnabled(False)
            self.historyButton.setEnabled(False)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(False)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(False)
        elif method == UiState.FETCHING_ERROR:
            self.set_option_controls_status(False)
            self.urlInput.setEnabled(True)
            self.pasteButton.setEnabled(True)
            self.historyButton.setEnabled(True)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(False)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(False)
        elif method == UiState.FETCHING_FINISHED:
            self.set_option_controls_status(True)
            self.urlInput.setEnabled(True)
            self.pasteButton.setEnabled(True)
            self.historyButton.setEnabled(True)
            self.getInfoButton.setEnabled(True)
            self.selectFormatsButton.setEnabled(True)
            self.settingsButton.setEnabled(True)
            self.openFolderButton.setEnabled(True)
            self.downloadButton.setEnabled(True)
        else:
            self.set_option_controls_status(True)
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

    def set_option_controls_status(self, status: bool):
        self.embThumbnailButton.setEnabled(status)
        self.embSubtitlesButton.setEnabled(status)
        self.embChaptersButton.setEnabled(status)
        self.embMetadataButton.setEnabled(status)
        self.useMTimeButton.setEnabled(status)
        self.skipSponsorsButton.setEnabled(status)

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
                # Privacy Mode status စစ်ဆေးခြင်း
                is_privacy = getattr(self, 'is_privacy_mode', False)
                if is_privacy:
                    self.urlInput.setText("🔒 ****************")
                else:
                    self.urlInput.setText(captured_url)

                self.c_urlInput = captured_url
                self.statusbar.showMessage(
                    f"Captured link from clipboard: {captured_url}"
                )
                logger.info(f"Clipboard captured: {captured_url}")
                self.on_fetch_info_clicked()
            else:
                logger.warning(
                    "Fetching already running — clipboard URL ignored"
                )
                if self.clipboard_thread:
                    self.clipboard_thread.last_clipboard_content = ""

    def on_toggle_clipboard_action(self):
        # Tray Menu action ရဲ့ checked state (True/False) ကို ယူ
        sender = self.sender()
        is_checked = sender.isChecked() if sender else False

        # Config မှာ တန်ဖိုး Update လုပ်ပြီး သိမ်းဆည်း
        self.config_mgr.set(ConfigKey.ADD_LINKS_CLIPBOARD, is_checked)

        # global loaded_settings ကိုလည်း Update လုပ်
        global loaded_settings
        loaded_settings[ConfigKey.ADD_LINKS_CLIPBOARD] = is_checked

        # Clipboard Monitor thread ကို ချက်ချင်း Toggle (ON/OFF) လုပ်
        self.check_and_toggle_clipboard_monitor()
        logger.info(f"Auto add clipboard toggled: {is_checked}")

    def check_for_updates(self, silent=False):
        """ Update စစ်ဆေးသည့် Method (silent=True ဆိုပါက Update မရှိလျှင် Alert မပြပါ) """
        self.is_silent_update_check = silent

        # GitHub Releases API Endpoint
        UPDATE_URL = "https://api.github.com/repos/YawStar/U-Tube-Downloader/releases/latest"

        if not silent:
            self.statusbar.showMessage("Checking for updates...")

        self.update_thread = UpdateCheckerThread(
            current_version=CONST.APP_VERSION,
            update_url=UPDATE_URL
        )
        self.update_thread.update_checked.connect(self._on_update_checked)
        self.update_thread.check_failed.connect(self._on_update_failed)
        self.update_thread.start()

    def _on_update_checked(self, is_available: bool, latest_version: str, release_notes: str, download_url: str):
        if is_available:
            # Standard Message Box အစား Custom Modern Dialog ပြ
            dialog = ModernUpdateDialog(
                current_ver=CONST.APP_VERSION,
                latest_ver=latest_version,
                release_notes=release_notes,
                download_url="https://github.com/YawStar/U-Tube-Downloader/releases",
                parent=self
            )
            dialog.exec()

        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage("Ready")

    def _on_update_checked_New(self, is_available: bool, latest_version: str, release_notes: str, download_url: str):
        if is_available:
            # ModernUpdateDialog ထဲသို့ တကယ့် zip asset download_url ကို ထည့်ပေးပါ
            dialog = ModernUpdateDialog(
                current_ver=CONST.APP_VERSION,
                latest_ver=latest_version,
                release_notes=release_notes,
                download_url=download_url,  # <-- ဤနေရာတွင် html_url အစား zip link ကို သုံးပါ
                parent=self
            )

            
            dialog.exec()
            # ModernUpdateDialog တွင် Update ခလုတ်နှိပ်သည့်အခါ 
            # (သို့မဟုတ် Dialog လက်ခံလိုက်သည့်အခါ) အောက်ပါအတိုင်း Auto Update လုပ်မည့် Function ကို ချိတ်ဆက်နိုင်ပါသည်
            dialog.updateRequested.connect(lambda: self.start_auto_update(download_url))

            
            # dialog.exec()

        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage("Ready")

    def start_auto_update(self, download_url, release_data_assets=None):
        """
        OS Platform ကို အခြေခံ၍ GitHub Release Assets ထဲမှ သင့်လျော်သော 
        ZIP ဖိုင်ကို ရွေးချယ် Download ဆွဲပြီး Updater Script ဖြင့် Update လုပ်ရန်
        """
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        temp_dir = tempfile.gettempdir()
        zip_path = os.path.join(temp_dir, "update.zip")
        
        # OS Platform အလိုက် File နာမည် သို့မဟုတ် Keyword ကို သတ်မှတ်ခြင်း
        target_keyword = ""
        exe_name = "U-Tube-Downloader"
        
        if CURRENT_OS == "Windows":
            target_keyword = "win"  # ဥပမာ - u-tube-downloader-windows.zip သို့မဟုတ် win-x64.zip
            exe_name = "U-Tube-Downloader.exe"
        elif CURRENT_OS == "Darwin":  # macOS
            target_keyword = "mac"
        else:  # Linux
            target_keyword = "linux"

        actual_download_url = download_url

        # အကယ်၍ Assets စာရင်း ပေးထားပါက OS နဲ့ အကိုက်ညီဆုံး Asset URL ကို ရှာမည်
        if release_data_assets and isinstance(release_data_assets, list):
            for asset in release_data_assets:
                asset_name = asset.get("name", "").lower()
                if target_keyword in asset_name and asset_name.endswith(".zip"):
                    actual_download_url = asset.get("browser_download_url")
                    break

        try:
            self.statusbar.showMessage("Downloading update package...")
            logger.info(f"Downloading update from: {actual_download_url}")
            
            response = requests.get(actual_download_url, stream=True, timeout=15)
            if response.status_code != 200:
                raise Exception(f"Server responded with status code: {response.status_code}")

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # OS အလိုက် Updater Script ဖန်တီးခြင်း
            if CURRENT_OS == "Windows":
                script_path = os.path.join(temp_dir, "updater.bat")
                exe_path = os.path.join(app_dir, exe_name)
                
                batch_content = f"""@echo off
setlocal
echo Waiting for application to close...
timeout /t 2 /nobreak > nul

echo Extracting update...
powershell -Command "Expand-Archive -Path '{zip_path}' -DestinationPath '{app_dir}' -Force"

if %errorlevel% neq 0 (
    echo Update extraction failed!
    pause
    exit /b %errorlevel%
)

echo Cleaning up...
del /f /q "{zip_path}"

echo Starting updated application...
start "" "{exe_path}"

del "%~f0"
exit
"""
                with open(script_path, "w") as f:
                    f.write(batch_content)

                subprocess.Popen(["cmd.exe", "/c", script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)

            else:
                script_path = os.path.join(temp_dir, "updater.sh")
                exe_path = os.path.join(app_dir, exe_name)
                
                sh_content = f"""#!/bin/bash
sleep 2
echo "Extracting update..."
unzip -o "{zip_path}" -d "{app_dir}"

if [ $? -ne 0 ]; then
    echo "Update extraction failed!"
    exit 1
fi

echo "Cleaning up..."
rm -f "{zip_path}"

echo "Starting updated application..."
"{exe_path}" &

rm -- "$0"
"""
                with open(script_path, "w") as f:
                    f.write(sh_content)

                os.chmod(script_path, 0o755)
                subprocess.Popen(["bash", script_path])

            # ဖိုင်များ လွတ်လပ်စွာ Overwrite လုပ်နိုင်ရန် Main App ကို အပြီးတိုင် ပိတ်မည်
            QApplication.quit()

        except Exception as e:
            logger.error(f"Auto update failed: {e}")
            QMessageBox.warning(self, "Update Failed", f"Could not complete update:\n{e}")
            self.statusbar.showMessage("Update failed.")

    def _on_update_failed(self, error_msg: str):
        if not self.is_silent_update_check:
            QMessageBox.warning(self, "Update Check Failed", f"Could not check for updates:\n{error_msg}\n\nမအေလိုး မင်းအောင်လှိုင်ကောင်းမှုကြောင့် GitHub Api ကိုဖတ်မရပါသဖြင့် VPN သုံးပြီး ပြန်စစ်ပါ..")
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage("Ready")

    def show_dialog_with_blur(self, dialog):
        """ Dialog ပွင့်ချိန် Blur ပြပေးပြီး ပိတ်သွားချိန် Blur ပြန်ဖြုတ်ပေးမည် """
        self.blur_overlay.show_overlay()   # Blur ဖွင့်မည်
        try:
            return dialog.exec()
        finally:
            self.blur_overlay.hide_overlay()  # Dialog ပိတ်သွားလျှင် Blur ပြန်ပိတ်မည်

    # =========================================================================
    # PRIVACY MODE CONTROLS
    # =========================================================================
    def show_original_thumbnail(self):
        """ Privacy Mode ပိတ်လိုက်ချိန်တွင် Original Thumbnail Pixmap ကို ပြန်ပြပေးမည် """
        original = getattr(self, '_privacy_original_data', {})
        pixmap = original.get("thumbnail")
        
        if pixmap and not pixmap.isNull():
            self.lblThumbnail.setPixmap(pixmap)
        else:
            # တကယ်လို့ မူလ Thumbnail pixmap မရှိခဲ့ရင် Default Thumbnail ကို ပြမည်
            self.display_default_thumbnail()

    def enable_privacy_mode(self):
        """ Privacy Mode ကို ဖွင့်မည် (Thumbnail အစားထိုးမည်၊ စာသားများကို Mask လုပ်မည်) """
        if getattr(self, 'is_privacy_mode', False):
            return  # Privacy Mode ပွင့်နေပြီးသားဆိုလျှင် ထပ်မလုပ်ပါ

        self.is_privacy_mode = True

        if hasattr(self, 'urlInput'):
            self.urlInput.setText("🔒 ****************")
                        
        # Fetching လုပ်နေသလား စစ်ဆေး
        if not self.fetch_controller.is_running():
            # ၁။ Spinner ကို ရပ်ပြီး ဖျောက်မည်
            if hasattr(self, 'spinner'):
                self.spinner.stop()

            # ၂။ Thumbnail ကို Privacy Thumbnail သို့ အစားထိုးခြင်း
            if hasattr(self, 'lblThumbnail'):
                self.display_privacy_thumbnail()

            # ၃။ UI Controls များကို Masked Text များဖြင့် အစားထိုးခြင်း
            if not self.lblTitle.text() == "": self.lblTitle.setText("🔒 *************************")

            if not self.lblUploaderVal.text() == "": self.lblUploaderVal.setText("🔒 *******")

            if not self.c_urlInput: self.c_urlInput = self.urlInput.text()
            if hasattr(self, 'urlInput'):
                self.urlInput.setText("🔒 ****************")

            if not self.download_controller.is_running():
                if hasattr(self, 'txtInfoLog'):
                    self.txtInfoLog.setHtml("<i>🔒 Description hidden in Privacy Mode.</i>")

        logger.info("Privacy Mode enabled")

    def disable_privacy_mode(self):
        """ Standard Mode သို့ ပြန်ပြောင်းမည် (Original UI Data များကို ပြန်ဖော်မည်) """
        if not getattr(self, 'is_privacy_mode', False):
            return  # Privacy Mode ပိတ်နေပြီးသားဆိုလျှင် ထပ်မလုပ်ပါ...

        self.is_privacy_mode = False

        if not self.fetch_controller.is_running():
            # Spinner ကို ရပ်ပြီး ဖျောက်မည်
            if hasattr(self, 'spinner'):
                self.spinner.stop()

            if hasattr(self, 'lblTitle'):
                self.lblTitle.setText(getattr(self, 'c_title', ''))

            if hasattr(self, 'lblUploaderVal'):
                self.lblUploaderVal.setText(getattr(self, 'c_uploader', ''))

            if hasattr(self, 'urlInput'):
                self.urlInput.setText(getattr(self, 'c_urlInput', ''))

            if hasattr(self, 'urlInput'):
                self.urlInput.setText(self.c_urlInput)

            if not self.download_controller.is_running():
                # ------------------------------------------------------------------
                # ✨ Playlist Detection (URL ထဲတွင် list= ပါဝင်ခြင်း သို့မဟုတ် /playlist ပါခြင်း သို့ /show/ )
                # ------------------------------------------------------------------
                url = self.c_urlInput
                is_playlist = "list=" in url.lower() or "/playlist" in url.lower() or "/show/" in url.lower()
                if hasattr(self, 'txtInfoLog'):
                    # ✨ အကယ်၍ Playlist Message သိမ်းထားတာ ရှိရင် အဲ့ဒါကိုပဲ ပြန်ပြမယ်
                    if hasattr(self, '_playlist_html_message') and self._playlist_html_message and is_playlist:
                        self.txtInfoLog.setHtml(self._playlist_html_message)
                    else:
                        org_desc = str(getattr(self, 'c_description', ''))
                        if org_desc and org_desc != "None":
                            html_text = description_to_html(org_desc)
                            self.txtInfoLog.setHtml(html_text)
                        else:
                            self.txtInfoLog.setHtml("")

            # ✨ self.c_thumbnail ကို စစ်ဆေးပြီး Original Thumbnail ကို ပြန်ဖော်ပေးခြင်း
            if hasattr(self, 'c_thumbnail') and self.c_thumbnail is not None:
                # Normal Mode: Scaled Thumbnail ပြသခြင်း
                scaled_pixmap = ThumbnailService.scale_for_label(self.c_thumbnail)
                self.lblThumbnail.setPixmap(scaled_pixmap)
            else:
                # c_thumbnail မရှိပါက သို့မဟုတ် show_original_thumbnail မက်သဒ်ရှိပါက ခေါ်ပေးမည်
                if hasattr(self, 'show_original_thumbnail'):
                    self.show_original_thumbnail()
                else:
                    self.display_default_thumbnail()

        logger.info("Privacy Mode disabled")

    def toggle_privacy_mode(self, enable: bool = None):
        """ Privacy Mode ကို On/Off Switch လုပ်မည် """
        if enable is None:
            enable = not getattr(self, 'is_privacy_mode', False)

        if enable:
            self.enable_privacy_mode()
        else:
            self.disable_privacy_mode()

    def change_ui_mode(self):
        if self.is_privacy_mode:
            self.toggle_privacy_mode(False)
            self.is_privacy_mode = False
            self.changeModeButton.setChecked(False)
        else:
            self.toggle_privacy_mode(True)
            self.is_privacy_mode = True
            self.changeModeButton.setChecked(True)

    def reset_video_info_ui(self):
        """ Fetch မလုပ်မီ သို့မဟုတ် Link အသစ်ရောက်ချိန်တွင် UI ကို Initial State သို့ ပြန်ပြောင်း """
        self.c_urlInput = None
        # 1. Title, Duration, Chapters, Uploader, Upload Date Label များကို ရှင်းထုတ်ခြင်း
        self.urlInput.setText("")
        self.lblTitle.setText("")
        self.lblDurationVal.setText("")
        self.lblChaptersVal.setText("")
        self.lblUploaderVal.setText("")
        self.lblUploadDateVal.setText("")
        self.c_title = None
        self.c_duration = None
        self.c_chapters = None
        self.c_uploader = None
        self.c_upload_date = None
        self.c_description = None
        self.c_thumbnail = None

        
        # 2. Thumbnail 
        self.spinner.stop() # Spinner ကို ရပ်ပြီး ဖျောက်
        self.lblThumbnail.setMovie(None)
        self.display_default_thumbnail()
        
        if not self.download_controller.is_running():
            # 3. Format / Quality Combobox များကို Clear လုပ်ခြင်း
            self.txtInfoLog.setText("")
        
            # 4. Download Button ကို Disable လုပ်ထားခြင်း (Fetch ပြီးမှ Enable ပြန်လုပ်ရန်)
            self.downloadButton.setEnabled(False)
            self.selectFormatsButton.setEnabled(False)

        # 5. informations data ကို Reset လုပ်
        self.info = None

        # 6. Select Formats / Playlist Button Reset
        self.selectFormatsButton.setText("Formats")
        self.selectFormatsButton.setProperty("selected", False)
        self.selectFormatsButton.style().unpolish(self.selectFormatsButton)
        self.selectFormatsButton.style().polish(self.selectFormatsButton)
        self.selectFormatsButton.update()

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
        
        # --- သင်မေးထားသော Code များထည့်ရမည့်နေရာ ---
        status_html = self.get_status_html(status)
        full_url_text = f"{url}{status_html}"
        self.lbl_url.setText(full_url_text)
        # ----------------------------------------

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

    def get_status_html(self, status):
        if not status:
            return ""
            
        status_lower = str(status).lower()
        
        # Status အလိုက် အရောင် Hex Code သတ်မှတ်ခြင်း
        if "completed" in status_lower or "downloaded" in status_lower:
            color = "#4CAF50"  # အစိမ်းရောင် (Green)
            display_text = "Downloaded"
        elif "fetched" in status_lower or "ready" in status_lower:
            color = "#2196F3"  # အပြာရောင် (Blue)
            display_text = "Fetched"
        elif "error" in status_lower or "failed" in status_lower:
            color = "#F44336"  # အနီရောင် (Red)
            display_text = "Error"
        else:
            color = "#9E9E9E"  # Default မီးခိုးရောင် (Grey)
            display_text = status.capitalize()
            
        return f' <span style="color: {color}; font-weight: bold;">[{display_text}]</span>'

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

            # UserRole ထဲတွင် Search အတွက် Data သိမ်းဆည်း
            item.setData(Qt.ItemDataRole.UserRole, url)
            item.setData(Qt.ItemDataRole.UserRole + 1, f"{title} {url}")

            # Custom Item Widget ထည့်သွင်း
            item_widget = HistoryItemWidget(
                title=title,
                url=url,
                status=status,
                on_delete_callback=self.delete_single_item
            )

            self.ui.listHistory.addItem(item)
            self.ui.listHistory.setItemWidget(item, item_widget)

    def delete_single_item(self, url):
        """ တစ်ခုချင်းစီ ဖျက်သည့် Function """
        # Database မှ ဖျက် (db_mgr ရှိရင်)
        if self.db_mgr and hasattr(self.db_mgr, 'delete_history_by_url'):
            self.db_mgr.delete_history_by_url(url)

        # UI ListWidget မှ ဖျက်
        for i in range(self.ui.listHistory.count()):
            item = self.ui.listHistory.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == url:
                self.ui.listHistory.takeItem(i)
                break

    def clear_all_history(self):
        """ History အားလုံးကို ဖျက်ခြင်း """
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
    """ Uncaught exceptions ကို log လုပ်ပြီး crash မဖြစ်စေရန် """
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
    
    # App ပိတ်ချိန် နောက်ဆုံး ကာကွယ်မှု — QThread warning ကာကွယ်
    def _on_about_to_quit():
        logger.info("aboutToQuit — final thread cleanup")
        try:
            window._cleanup_all_threads()
            # pass
        except Exception as e:
            logger.error(f"Cleanup in aboutToQuit failed: {e}")

    app.aboutToQuit.connect(_on_about_to_quit)

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
            window.statusbar.showMessage("Dependencies download incomplete or failed!")
    else:
        window.statusbar.showMessage(StatusMsg.READY)

    if is_first_launch:
        QTimer.singleShot(100, window.on_about_button_clicked)
    
    logger.info("Entering Qt event loop")
    exit_code = app.exec()
    logger.info(f"Application exited with code {exit_code}")
    sys.exit(exit_code)