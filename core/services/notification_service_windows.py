import asyncio
import logging
import os
import shutil
import sys
import threading
from pathlib import Path
from PySide6.QtCore import QFile, QIODevice, QObject, QStandardPaths, Signal, Slot
from desktop_notifier import DEFAULT_SOUND, Button, DesktopNotifier

from core.services.file_opener import FileOpenerService
import core.global_constants as CONST

# Resources
import assets.resources_rc  # noqa: F401

logger = logging.getLogger(__name__)


def ensure_app_icon() -> str:
    """
    APP_DATA_DIR အောက်မှာ app_icon.png ရှိ/မရှိ စစ်ဆေး
    - ရှိရင် အဲဒီ path ကို return ပြန်မယ်။
    - မရှိရင်၊ compiled: QRC (:images/images/app_icon.png) မှ APP_DATA_DIR သို့ extract လုပ်မယ်။
    - မရှိရင်၊ dev mode: ProjectDir/assets/images/app_icon.png မှ copy ကူးမယ်။
    """
    app_data_dir = os.path.normpath(
        QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    )
    os.makedirs(app_data_dir, exist_ok=True)

    target_icon_path = os.path.join(app_data_dir, "app_icon.png")

    # APP_DATA_DIR အောက်မှာ ရှိနေပြီးသားဆိုရင် တိုက်ရိုက် return ပြန်မယ်
    if os.path.exists(target_icon_path):
        return target_icon_path

    is_compiled = getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")

    if is_compiled:
        # QRC ထဲမှ Extract လုပ်ခြင်း
        qrc_icon_path = ":/images/images/app_icon.png"
        qfile = QFile(qrc_icon_path)
        if qfile.open(QIODevice.ReadOnly):
            try:
                with open(target_icon_path, "wb") as out_file:
                    out_file.write(qfile.readAll().data())
            except Exception as e:
                logger.error(f"Failed to extract icon from QRC: {e}")
            finally:
                qfile.close()
    else:
        # Dev Environment
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        source_icon_path = os.path.join(base_dir, "assets", "images", "app_icon.png")

        if os.path.exists(source_icon_path):
            try:
                shutil.copy2(source_icon_path, target_icon_path)
            except Exception as e:
                logger.error(f"Failed to copy icon from assets: {e}")

    return target_icon_path

class NotificationService(QObject):
    """
    Main Thread ထဲတွင် Desktop Notification များကို အလုပ်လုပ်စေမည့် Service Class။
    Open File နှင့် Open Folder button များ ပါဝင်
    """

    _notify_signal = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifier = None
        self.icon_path = ensure_app_icon()

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self._thread.start()

        self._notify_signal.connect(self._handle_send_notification)

    def _start_async_loop(self):
        """ Background Thread ထဲမှာ Event Loop ဖွင့်ပြီး Notifier ကို Init လုပ်မယ် """
        asyncio.set_event_loop(self._loop)
        self.notifier = DesktopNotifier(app_name=CONST.APP_NAME)

        # Windows WinRT Event Queue ကို Instant Process လုပ်ပေးမည့် Keep-Alive Task
        self._loop.create_task(self._keep_event_loop_active())
        self._loop.run_forever()

    async def _keep_event_loop_active(self):
        """
        Windows Toast Notification ၏ Button Click Callback များကို ချက်ချင်း
        တုံ့ပြန်နိုင်ရန် Event Loop ကို Idle မဖြစ်စေဘဲ စက္ကန့်ဝက်တိုင်း Yield လုပ်ပေးမယ့် Task
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
                # desktop_notifier သည် icon အတွက် Path object Path(self.icon_path) သို့ ပြောင်းပေး
                icon_obj = Path(self.icon_path) if os.path.exists(self.icon_path) else None

                await self.notifier.send(
                    title=title,
                    message=message,
                    buttons=buttons,
                    icon=icon_obj,
                    sound=DEFAULT_SOUND,
                )
        except Exception as e:
            logger.error(f"Desktop Notifier Error: {e}")