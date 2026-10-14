import os
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel


class DropThumbnailLabel(QLabel):
    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        # ⭐ Default style ကို .ui ဖိုင်က သတ်မှတ်ထားတဲ့အတိုင်း သိမ်းထား
        # (dropEvent ပြီးရင် ဒီ style ကို ပြန်သတ်မှတ်မယ်)
        self._default_style = (
            "border: 1px solid #888888; "
            "background-color: #0C1D2E;"
        )
        self._hover_style = (
            "border: 2px dashed #4CAF50; "
            "border-radius: 2px; "
            "background-color: rgba(76, 175, 80, 30);"
        )
        self._hover_not_allow_style = (
            "border: 2px dashed #FF0000; "
            "border-radius: 2px; "
            "background-color: rgba(255, 0, 0, 30);"
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                event.acceptProposedAction()
                self.setStyleSheet(self._hover_style)
                # if self.fetch_controller.is_running() or self.download_controller.is_running():
                #     self.setStyleSheet(self._hover_not_allow_style)
                # else:
                #     self.setStyleSheet(self._hover_style)
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # Drag ထွက်သွားရင် default style ပြန်သတ်မှတ်
        self.setStyleSheet(self._default_style)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        # Drop လုပ်ရင် default style ပြန်သတ်မှတ်
        self.setStyleSheet(self._default_style)

        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return

        file_path = urls[0].toLocalFile()
        if not os.path.isfile(file_path):
            event.ignore()
            return

        event.acceptProposedAction()
        self.file_dropped.emit(file_path)