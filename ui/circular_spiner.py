import sys
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

class MaterialSpinner(QWidget):
    def __init__(self, parent=None, size=50, line_width=4, color=QColor("#FFFFFF")):
        super().__init__(parent)
        self._size = size
        self._line_width = line_width
        self._color = color
        
        self.setFixedSize(self._size, self._size)
        
        self._start_angle = 0
        self._span_angle = 20  # အနည်းဆုံး အလျား
        self._growing = True    # ကြီးလာနေသလား / သေးသွားနေသလား စစ်ရန်
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        
    def _animate(self):
        # Overall rotation (တစ်ပတ်လုံး လှည့်နေစေရန်)
        self._start_angle = (self._start_angle + 6) % 360
        
        # Arc အလျား တိုး/လျော့ လုပ်ပေးခြင်း (Video ထဲကလို တိုးလိုက် ကျုံ့လိုက်ဖြစ်ရန်)
        if self._growing:
            self._span_angle += 4
            if self._span_angle >= 280:  # အများဆုံး ရှည်ထွက်နိုင်သည့် ပမာဏ
                self._growing = False
        else:
            self._span_angle -= 4
            if self._span_angle <= 20:   # အနည်းဆုံး ပြန်ကျုံ့မည့် ပမာဏ
                self._growing = True
                
        self.update()

    def start(self):
        if not self.timer.isActive():
            self.timer.start(16) # ~60 FPS smooth ဖြစ်စေရန်
            self.show()

    def stop(self):
        if self.timer.isActive():
            self.timer.stop()
            self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        margin = self._line_width / 2
        rect = QRectF(margin, margin, self.width() - self._line_width, self.height() - self._line_width)

        # နောက်ခံ လိုင်းကြောင်း မပါ
        pen = QPen(self._color, self._line_width)
        pen.setCapStyle(Qt.RoundCap) # အနားသတ် ဝိုင်းစေရန်
        painter.setPen(pen)

        # Qt Arc တွက်ချက်မှု (1/16th degree)
        start = int(-self._start_angle * 16)
        span = int(-self._span_angle * 16)

        painter.drawArc(rect, start, span)
        painter.end()


# --- စမ်းသပ်ရန် UI Example ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(300, 200)
        self.setStyleSheet("background-color: #1e1e1e;") # အမှောင် Theme

        layout = QVBoxLayout(self)

        # Material Spinner (နောက်ခံ လိုင်းမပါ၊ အစအဆုံး ကျုံ့/ကား အလုပ်လုပ်သည်)
        self.spinner = MaterialSpinner(self, size=48, line_width=4, color=QColor("#FFFFFF"))
        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)

        self.spinner.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())