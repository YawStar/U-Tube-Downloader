import asyncio
import logging
import os
import shutil
import sys
import threading
from pathlib import Path

from PySide6.QtCore import (
    QFile,
    QIODevice,
    QObject,
    QStandardPaths,
    Signal,
    Slot,
)

from desktop_notifier import (
    DEFAULT_SOUND,
    Button,
    DesktopNotifier,
    Icon,
)

from core.services.file_opener import FileOpenerService
import core.global_constants as CONST

# Resources
import assets.resources_rc  # noqa: F401


logger = logging.getLogger(__name__)


def ensure_app_icon() -> str:
    """
    APP_DATA_DIR အောက်မှာ app_icon.png ရှိ/မရှိ စစ်ဆေးပြီး
    ရှိတဲ့ absolute path ကို return ပြန်မယ်။
    """

    app_data_dir = os.path.normpath(
        QStandardPaths.writableLocation(
            QStandardPaths.AppDataLocation
        )
    )

    os.makedirs(app_data_dir, exist_ok=True)

    target_icon_path = os.path.join(
        app_data_dir,
        "app_icon.png",
    )

    if os.path.isfile(target_icon_path):
        return target_icon_path

    is_compiled = (
        getattr(sys, "frozen", False)
        or hasattr(sys, "_MEIPASS")
    )

    if is_compiled:
        qrc_icon_path = ":/images/images/app_icon.png"
        qfile = QFile(qrc_icon_path)

        if qfile.open(QIODevice.ReadOnly):
            try:
                with open(target_icon_path, "wb") as out_file:
                    out_file.write(qfile.readAll().data())

            except Exception:
                logger.exception(
                    "Failed to extract icon from QRC"
                )

            finally:
                qfile.close()

    else:
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )

        source_icon_path = os.path.join(
            base_dir,
            "assets",
            "images",
            "app_icon.png",
        )

        if os.path.isfile(source_icon_path):
            try:
                shutil.copy2(
                    source_icon_path,
                    target_icon_path,
                )

            except Exception:
                logger.exception(
                    "Failed to copy icon from assets"
                )

    return target_icon_path


class NotificationService(QObject):
    """
    Linux, Windows, macOS အတွက် cross-platform
    desktop notification service.
    """

    _notify_signal = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.notifier = None
        self.icon_path = ensure_app_icon()

        self._loop = asyncio.new_event_loop()
        self._notifier_ready = threading.Event()

        self._thread = threading.Thread(
            target=self._start_async_loop,
            name="desktop-notifier-loop",
            daemon=True,
        )

        self._thread.start()

        self._notify_signal.connect(
            self._handle_send_notification
        )

    def _start_async_loop(self):
        asyncio.set_event_loop(self._loop)

        try:
            self.notifier = DesktopNotifier(
                app_name=CONST.APP_NAME,
            )

            self._notifier_ready.set()

            logger.info(
                "DesktopNotifier initialized successfully"
            )

            self._loop.run_forever()

        except Exception:
            logger.exception(
                "Failed to start notification event loop"
            )

        finally:
            self._notifier_ready.set()

    def send_notification(
        self,
        title: str,
        message: str,
        file_path: str = "",
    ):
        self._notify_signal.emit(
            title,
            message,
            file_path,
        )

    @Slot(str, str, str)
    def _handle_send_notification(
        self,
        title: str,
        message: str,
        file_path: str,
    ):
        if not self._thread.is_alive():
            logger.error(
                "Notification thread is not running"
            )
            return

        if not self._notifier_ready.wait(timeout=5):
            logger.error(
                "Notifier initialization timed out"
            )
            return

        if self.notifier is None:
            logger.error(
                "DesktopNotifier is not available"
            )
            return

        try:
            future = asyncio.run_coroutine_threadsafe(
                self._async_send(
                    title,
                    message,
                    file_path,
                ),
                self._loop,
            )

            future.add_done_callback(
                self._notification_finished
            )

        except Exception:
            logger.exception(
                "Failed to trigger notification"
            )

    @staticmethod
    def _notification_finished(future):
        try:
            future.result()

        except Exception:
            logger.exception(
                "Notification coroutine failed"
            )

    async def _async_send(
        self,
        title: str,
        message: str,
        file_path: str,
    ):
        buttons = []

        if file_path and os.path.isfile(file_path):
            abs_file_path = os.path.abspath(file_path)

            def open_file():
                try:
                    FileOpenerService.open_folder(
                        abs_file_path
                    )

                except Exception:
                    logger.exception(
                        "Failed to open file"
                    )

            def open_folder():
                try:
                    FileOpenerService.open_folder_and_select_file(
                        abs_file_path
                    )

                except Exception:
                    logger.exception(
                        "Failed to open folder"
                    )

            buttons = [
                Button(
                    title="Open File",
                    on_pressed=open_file,
                ),
                Button(
                    title="Open Folder",
                    on_pressed=open_folder,
                ),
            ]

        try:
            if self.notifier is None:
                logger.error(
                    "DesktopNotifier is not initialized"
                )
                return

            # Icon object ကို Linux မှာပဲ ထည့်မယ်။
            # macOS/Windows မှာ application icon ကို
            # packaged application မှာ သတ်မှတ်ပေးရမယ်။
            icon_obj = None

            if sys.platform.startswith("linux"):
                if self.icon_path and os.path.isfile(
                    self.icon_path
                ):
                    icon_obj = Icon(
                        path=Path(
                            os.path.abspath(
                                self.icon_path
                            )
                        )
                    )

            logger.info(
                "Sending notification: title=%r, icon=%r",
                title,
                icon_obj,
            )

            await self.notifier.send(
                title=title,
                message=message,
                buttons=buttons,
                icon=icon_obj,
                sound=DEFAULT_SOUND,
            )

        except Exception:
            logger.exception(
                "Desktop Notifier Error"
            )
