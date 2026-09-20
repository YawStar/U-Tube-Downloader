# -*- coding: utf-8 -*-
"""
Notification Service

QSystemTrayIcon ကို အသုံးပြုပြီး Desktop Notification ပို့ပေးသည်။
main.py ထဲက ဒီ notification block များကို စုစည်းထားသည်:

    • Fetch completed notification (display_video_info)
    • Download started notification (on_download_clicked)
    • Download completed notification (on_download_finished)
    • Cookies error notification (closeEvent)

Config ကို လိုက်နာသည်:
    • notify_fetched
    • notify_download_started
    • notify_download_completed
"""
from PySide6.QtWidgets import QSystemTrayIcon

# Application Name (tooltip / title အတွက်)
try:
    import core.global_constants as CONST
    APP_NAME = CONST.APP_NAME
except Exception:
    APP_NAME = "YawStar U-Tube Downloader"


class NotificationService:
    """
    System Tray မှတစ်ဆင့် Notification ပို့ပေးသည့် Service။

    tray_icon မရှိပါက (Linux တစ်ချို့) print သာ လုပ်သည်။
    """

    def __init__(self, tray_icon: QSystemTrayIcon | None, parent=None):
        """
        Args:
            tray_icon: MainWindow မှ ဖန်တီးထားသော QSystemTrayIcon (None ဖြစ်နိုင်)
            parent: (unused — Qt parent မလိုအပ်)
        """
        self.tray_icon = tray_icon

    # ------------------------------------------------------------------
    # Core notify
    # ------------------------------------------------------------------
    def notify(
        self,
        title: str,
        message: str = "",
        duration_ms: int = 3000,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
    ) -> bool:
        """
        Notification ပို့သည်။ tray_icon မရှိပါက print သာ လုပ်ပြီး False ပြန်သည်။

        Returns:
            True — ပို့အောင်မြင်ပြီ
            False — tray_icon မရှိ / error
        """
        if self.tray_icon is None:
            print(f"[Notification skipped] {title}: {message}")
            return False

        try:
            self.tray_icon.showMessage(
                title,
                message,
                icon,
                duration_ms,
            )
            return True
        except Exception as e:
            print(f"Tray notification error: {e}")
            return False

    # ------------------------------------------------------------------
    # Domain-specific wrappers
    # ------------------------------------------------------------------
    def notify_fetch_completed(self, video_title: str, duration_ms: int = 3000) -> bool:
        """Fetch Info ပြီးဆုံးသည့်အခါ ပို့သော notification"""
        return self.notify(
            "Fetching Completed!",
            video_title,
            duration_ms,
        )

    def notify_download_started(self, duration_ms: int = 3000) -> bool:
        """Download စတင်သည့်အခါ ပို့သော notification (message မလို)"""
        return self.notify(
            "Download Started.",
            "",
            duration_ms,
        )

    def notify_download_completed(self, video_title: str, duration_ms: int = 3000) -> bool:
        """Download ပြီးဆုံးသည့်အခါ ပို့သော notification"""
        return self.notify(
            "Download Completed!",
            video_title,
            duration_ms,
        )

    def notify_background_work(self, duration_ms: int = 2000) -> bool:
        """App ကို tray ထဲဝှက်စဉ် background work ရှိကြောင်း ပြ"""
        return self.notify(
            APP_NAME,
            "App is still working in the background.",
            duration_ms,
        )