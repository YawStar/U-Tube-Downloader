import asyncio
import logging
import os
import threading
from PySide6.QtCore import QObject, Signal, Slot
from desktop_notifier import DEFAULT_SOUND, Button, DesktopNotifier

from core.services.file_opener import FileOpenerService

logger = logging.getLogger(__name__)


class NotificationService(QObject):
    """
    Main Thread ထဲတွင် Desktop Notification များကို အလုပ်လုပ်စေမည့် Service Class။
    Open File နှင့် Open Folder button များ ပါဝင်သည်။
    """

    _notify_signal = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifier = None

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self._thread.start()

        self._notify_signal.connect(self._handle_send_notification)

    def _start_async_loop(self):
        """Background Thread ထဲတွင် Event Loop ဖွင့်ပြီး Notifier ကို Init လုပ်မည်"""
        asyncio.set_event_loop(self._loop)
        self.notifier = DesktopNotifier(app_name="YawStar U-Tube Downloader")

        # Windows WinRT Event Queue ကို Instant Process လုပ်ပေးမည့် Keep-Alive Task
        self._loop.create_task(self._keep_event_loop_active())
        self._loop.run_forever()

    async def _keep_event_loop_active(self):
        """
        Windows Toast Notification ၏ Button Click Callback များကို ချက်ချင်း
        တုံ့ပြန်နိုင်ရန် Event Loop ကို Idle မဖြစ်စေဘဲ စက္ကန့်ဝက်တိုင်း Yield လုပ်ပေးမည့် Task
        """
        while True:
            await asyncio.sleep(0.5)

    def send_notification(self, title: str, message: str, file_path: str = ""):
        self._notify_signal.emit(title, message, file_path)

    @Slot(str, str, str)
    def _handle_send_notification(self, title: str, message: str, file_path: str):
        try:
            asyncio.run_coroutine_threadsafe(
                self._async_send(title, message, file_path), self._loop
            )
        except Exception as e:
            logger.error(f"Failed to trigger notification: {e}")

    async def _async_send(self, title: str, message: str, file_path: str):
        buttons = []

        if file_path and os.path.exists(file_path):
            abs_file_path = os.path.abspath(file_path)

            def open_file():
                try:
                    FileOpenerService.open_folder(abs_file_path)
                except Exception as e:
                    logger.error(f"Failed to open file: {e}")

            def open_folder():
                try:
                    FileOpenerService.open_folder_and_select_file(abs_file_path)
                except Exception as e:
                    logger.error(f"Failed to open folder: {e}")

            buttons = [
                Button(title="Open File", on_pressed=open_file),
                Button(title="Open Folder", on_pressed=open_folder),
            ]

        try:
            if self.notifier:
                await self.notifier.send(
                    title=title,
                    message=message,
                    buttons=buttons,
                    sound=DEFAULT_SOUND,
                )
        except Exception as e:
            logger.error(f"Desktop Notifier Error: {e}")