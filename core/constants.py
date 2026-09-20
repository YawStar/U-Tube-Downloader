# -*- coding: utf-8 -*-
"""
Application Constants

Magic strings များကို စုစည်းထားသည်။
ဒါကြောင့် နေရာတစ်ခုတည်းမှာ ပြင်လို့ရသည်။

Categories:
    • Download stages (yt-dlp output markers)
    • Notification messages
    • UI state names
    • Icon names
"""


# =========================================================================
# yt-dlp Output Markers
# =========================================================================
class YtDlpMarker:
    """yt-dlp stdout/stderr ထဲက marker strings များ။"""

    DOWNLOAD = "[download]"
    DESTINATION = "[download] Destination:"
    MERGER = "[Merger] Merging formats into"
    EXTRACT_AUDIO = "[ExtractAudio]"
    EMBED_FILENAME = "[EmbedFilename]"

    # Cookies error detection
    COOKIES_ERROR_KEYWORDS = [
        "confirm you're not a bot",
        "sign in to confirm you're not a bot",
        "sign in to confirm",
        "use --cookies-from-browser",
        "requires authentication",
        "video requires authentication",
        "login required",
    ]


# =========================================================================
# Notification Messages
# =========================================================================
class NotifyMsg:
    """Notification title/message strings များ။"""

    FETCH_TITLE = "Fetching Completed!"
    DOWNLOAD_STARTED_TITLE = "Download Started."
    DOWNLOAD_COMPLETED_TITLE = "Download Completed!"
    BACKGROUND_TITLE = "YawStar Downloader"
    BACKGROUND_MSG = "App is still working in the background."


# =========================================================================
# UI State Names (set_controls_status method)
# =========================================================================
class UiState:
    """set_controls_status() အတွက် state names။"""

    DOWNLOADING = "downloading"
    FETCHING = "fetching"
    FETCHING_ERROR = "fetching_error"
    FETCHING_FINISHED = "fetching_finished"
    NORMAL = "normal"


# =========================================================================
# Icon Names (TaskbarService)
# =========================================================================
class IconName:
    """TaskbarService အတွက် icon names။"""

    WAITING = "waiting"
    DOWNLOADING = "downloading"
    ERROR = "error"
    COMPLETED = "completed"


# =========================================================================
# Statusbar Messages
# =========================================================================
class StatusMsg:
    """Statusbar မှာ ပြသတဲ့ message strings များ။"""

    READY = "Ready..."
    FETCHING = "Fetching video information..."
    CANCELLING_FETCH = "Cancelling fetch..."
    FETCH_CANCELLED = "Fetching cancelled by user."
    FETCH_FAILED = "Failed to fetch video information."
    DOWNLOAD_CANCELLED = "Download cancelled by user."
    DOWNLOAD_FAILED = "Download failed or encountered an error."
    DOWNLOAD_COMPLETED = "Download completed successfully! 🎉"
    DOWNLOAD_PREPARING = "Preparing to download. Please wait..."
    SETTINGS_SAVED = "Settings updated successfully."


# =========================================================================
# Config Keys (frequently used)
# =========================================================================
class ConfigKey:
    """Config settings keys — frequently used။"""

    LAST_ADDED_URL = "last_added_url"
    DOWNLOAD_PATH = "download_path"
    AWAKE_MODE = "awake_mode"
    USE_PROXY = "use_proxy"
    USE_SPEED_LIMIT = "use_speed_limit"
    COOKIES_TYPE = "cookies_type"
    COOKIES_PATH = "cookies_path"
    EMBED_THUMBNAIL = "embed_thumbnail"
    EMBED_SUBTITLES = "embed_subtitles"
    EMBED_CHAPTERS = "embed_chapters"
    EMBED_METADATA = "embed_metadata"
    USE_MTIME = "use_mtime"
    NOTIFY_FETCHED = "notify_fetched"
    NOTIFY_DOWNLOAD_STARTED = "notify_download_started"
    NOTIFY_DOWNLOAD_COMPLETED = "notify_download_completed"
    MINIMIZE_TO_TRAY = "minimize_to_tray"
    PLAY_AFTER_DOWNLOADED = "play_after_downloaded"
    AUTO_START_DOWNLOAD = "auto_start_download"
    ADD_LINKS_CLIPBOARD = "add_links_clipboard"


# =========================================================================
# Resource Paths
# =========================================================================
class ResourcePath:
    """Qt resource paths များ။"""

    APP_ICON = ":/icons/icons/app_icon.ico"
    WAITING_ICON = ":/icons/icons/waiting.ico"
    DOWNLOADING_ICON = ":/icons/icons/downloading.ico"
    ERROR_ICON = ":/icons/icons/error.ico"
    COMPLETED_ICON = ":/icons/icons/completed.ico"

    DEFAULT_THUMBNAIL = ":/images/images/default_thumbnail.jpg"
    LOADING_GIF = ":/images/images/loading.gif"


# =========================================================================
# Timing Constants
# =========================================================================
class Timing:
    """Timing constants (milliseconds)။"""

    TIPS_INTERVAL_MS = 5000              # 5 seconds
    THUMBNAIL_TIMEOUT_MS = 10000         # 10 seconds
    NOTIFICATION_DURATION_MS = 3000      # 3 seconds
    TRAY_MSG_DURATION_MS = 2000          # 2 seconds