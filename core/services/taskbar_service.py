# -*- coding: utf-8 -*-
"""
Windows Taskbar Service

ITaskbarList3 (ui/i_taskbar3.py) ကို wrap လုပ်ပြီး
Windows မဟုတ်တဲ့ OS တွေအတွက် no-op fallback ပေးသည်။

main.py ထဲက ဒီလို block တွေကို စုစည်းထားသည်:

    if CURRENT_OS == "Windows":
        waiting_icon = QIcon(":/icons/icons/waiting.ico")
        self.taskbar.reset()
        self.taskbar.indeterminate(waiting_icon)

ဒီဟာကို:

    self.taskbar_service.set_indeterminate("waiting")

လို့ ရေးနိုင်တော့မည်။

Icon Name → Resource Path mapping ကို service ထဲမှာ စုစည်းထားသည်။
"""
from PySide6.QtGui import QIcon

# Icon resource mapping (main.py မှ စုစည်း)
ICON_PATHS = {
    "waiting":     ":/icons/icons/waiting.ico",
    "downloading": ":/icons/icons/downloading.ico",
    "error":       ":/icons/icons/error.ico",
    "completed":   ":/icons/icons/completed.ico",
}


class TaskbarService:
    """
    Windows Taskbar ကို ထိန်းချုပ်သည်။

    Windows မဟုတ်ပါက method အားလုံး no-op ဖြစ်သည် (silent skip)။
    """

    def __init__(self, hwnd: int = 0, is_windows: bool = False):
        """
        Args:
            hwnd: Native window handle (int)
            is_windows: True ဖြစ်ပါက ITaskbarList3 ကို ဖန်တီးမည်
        """
        self.is_windows = is_windows
        self.taskbar = None

        if is_windows:
            try:
                from ui.i_taskbar3 import ITaskbarList3
                self.taskbar = ITaskbarList3(hwnd)
            except Exception as e:
                print(f"TaskbarService init failed: {e}")
                self.taskbar = None
                self.is_windows = False

    # ------------------------------------------------------------------
    # Icon helper
    # ------------------------------------------------------------------
    @staticmethod
    def _icon(name: str) -> QIcon | None:
        """Icon name → QIcon (resource မရှိရင် None)"""
        path = ICON_PATHS.get(name)
        if not path:
            return None
        return QIcon(path)

    # ------------------------------------------------------------------
    # No-op check
    # ------------------------------------------------------------------
    def _available(self) -> bool:
        return self.is_windows and self.taskbar is not None

    # ------------------------------------------------------------------
    # States
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Progress + overlay အားလုံး ရှင်း"""
        if not self._available():
            return
        try:
            self.taskbar.reset()
        except Exception as e:
            print(f"Taskbar reset error: {e}")

    def set_indeterminate(self, icon_name: str | None = None) -> None:
        """
        Loading/Indeterminate state ပြ။

        Args:
            icon_name: "waiting" / "downloading" / ... (None ဖြစ်နိုင်)
        """
        if not self._available():
            return
        try:
            icon = self._icon(icon_name) if icon_name else None
            self.taskbar.indeterminate(icon)
        except Exception as e:
            print(f"Taskbar indeterminate error: {e}")

    def set_downloading(
        self,
        value: int,
        maximum: int = 100,
        icon_name: str = "downloading",
    ) -> None:
        """Normal progress state ပြ (percent)"""
        if not self._available():
            return
        try:
            icon = self._icon(icon_name) if icon_name else None
            self.taskbar.downloading(value, maximum, icon)
        except Exception as e:
            print(f"Taskbar downloading error: {e}")

    def set_error(
        self,
        value: int = 0,
        maximum: int = 100,
        icon_name: str = "error",
    ) -> None:
        """Error state ပြ"""
        if not self._available():
            return
        try:
            icon = self._icon(icon_name) if icon_name else None
            self.taskbar.error(value, maximum, icon)
        except Exception as e:
            print(f"Taskbar error error: {e}")

    def set_completed(self, icon_name: str = "completed") -> None:
        """Completed state ပြ"""
        if not self._available():
            return
        try:
            icon = self._icon(icon_name) if icon_name else None
            self.taskbar.completed(icon)
        except Exception as e:
            print(f"Taskbar completed error: {e}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        """COM release (app ပိတ်ချိန်)"""
        if self.taskbar is not None:
            try:
                self.taskbar.close()
            except Exception:
                pass
            self.taskbar = None