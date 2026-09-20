# -*- coding: utf-8 -*-
"""
Notification Service

QSystemTrayIcon နှင့် desktop-notifier တို့ကို အသုံးပြုပြီး Desktop Notification ပို့ပေးသည်။
"""
import asyncio
import os
import platform
import subprocess
import threading
from pathlib import Path
from desktop_notifier import DesktopNotifier, Button
from PySide6.QtWidgets import QSystemTrayIcon

# Application Name
try:
    import core.global_constants as CONST
    APP_NAME = CONST.APP_NAME
except Exception:
    APP_NAME = "YawStar U-Tube Downloader"


class NotificationService:
    def __init__(self, tray_icon: QSystemTrayIcon | None = None, parent=None):
        self.tray_icon = tray_icon
        
        # desktop-notifier initialize
        self._notifier = DesktopNotifier(app_name=APP_NAME)
        
        # PySide6 နှင့် မဆန့်ကျင်စေရန် background thread ထဲတွင် asyncio loop run ခြင်း
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()

    def _run_async_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    # ------------------------------------------------------------------
    # Helper Functions for File / Folder Open Operations
    # ------------------------------------------------------------------
    def _open_file(self, file_path_str: str):
        current_os = platform.system()
        try:
            if current_os == "Darwin":
                subprocess.run(["open", file_path_str])
            elif current_os == "Linux":
                subprocess.run(["xdg-open", file_path_str])
            elif current_os == "Windows":
                os.startfile(os.path.normpath(file_path_str))
        except Exception as e:
            print(f"[Notification] Error opening file: {e}")

    def _open_folder(self, folder_path_str: str):
        current_os = platform.system()
        try:
            if current_os == "Darwin":
                subprocess.run(["open", folder_path_str])
            elif current_os == "Linux":
                subprocess.run(["xdg-open", folder_path_str])
            elif current_os == "Windows":
                os.startfile(os.path.normpath(folder_path_str))
        except Exception as e:
            print(f"[Notification] Error opening folder: {e}")

    # ------------------------------------------------------------------
    # Core notify (QSystemTrayIcon fallback)
    # ------------------------------------------------------------------
    def notify(
        self,
        title: str,
        message: str = "",
        duration_ms: int = 3000,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
    ) -> bool:
        if self.tray_icon is None:
            print(f"[Notification skipped] {title}: {message}")
            return False

        try:
            self.tray_icon.showMessage(title, message, icon, duration_ms)
            return True
        except Exception as e:
            print(f"Tray notification error: {e}")
            return False

    # ------------------------------------------------------------------
    # Domain-specific wrappers
    # ------------------------------------------------------------------
    def notify_fetch_completed(self, video_title: str, duration_ms: int = 3000) -> bool:
        return self.notify("Fetching Completed!", video_title, duration_ms)

    def notify_download_started(self, duration_ms: int = 3000) -> bool:
        return self.notify("Download Started.", "", duration_ms)

    def notify_download_completed(self, video_title: str, file_path_str: str = "") -> bool:
        """
        Download ပြီးဆုံးသည့်အခါ desktop-notifier ၏ send() ကိုသုံးပြီး 
        Open File နှင့် Open Folder ခလုတ်များပါသော Notification ပြသပေးမည်။
        """
        if not file_path_str:
            return self.notify("Download Complete", video_title)

        try:
            file_path = Path(file_path_str).resolve()

            # Buttons တည်ဆောက်ခြင်း
            buttons = [
                Button(
                    title="Open File",
                    on_pressed=lambda: self._open_file(str(file_path))
                ),
                Button(
                    title="Open Folder",
                    on_pressed=lambda: self._open_folder(str(file_path.parent))
                )
            ]

            # Async send coroutine ကို background loop ထဲသို့ပို့ပေးခြင်း
            asyncio.run_coroutine_threadsafe(
                self._notifier.send(
                    title="Download Complete",
                    message=file_path.name,
                    buttons=buttons,
                ),
                self._loop
            )
            return True

        except Exception as e:
            print(f"[desktop-notifier error]: {e}")
            return self.notify("Download Complete", video_title)

    def notify_background_work(self, duration_ms: int = 2000) -> bool:
        return self.notify(APP_NAME, "App is still working in the background.", duration_ms)