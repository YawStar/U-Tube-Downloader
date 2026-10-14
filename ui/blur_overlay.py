# ui/blur_overlay.py
from PySide6.QtWidgets import QWidget, QGraphicsBlurEffect
from PySide6.QtCore import QCoreApplication

class BlurOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(15)
        self.blur_effect.setEnabled(False)
        
        if self.parent_window:
            self.target = self.parent_window.centralWidget() if hasattr(self.parent_window, 'centralWidget') else self.parent_window
            self.target.setGraphicsEffect(self.blur_effect)

    def show_overlay(self):
        if self.blur_effect and self.parent_window:
            # 1. Blur မဖြစ်မီ Frame Buffer ကို Synchronize လုပ်ပါ
            self.blur_effect.setEnabled(True)
            self.target.repaint()
            QCoreApplication.processEvents()

    def hide_overlay(self):
        if self.blur_effect:
            self.blur_effect.setEnabled(False)
            if hasattr(self, 'target'):
                self.target.repaint()