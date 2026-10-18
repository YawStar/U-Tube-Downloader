import sys
import os
import pycountry
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Dark Theme Style (မူလအတိုင်း)
DARK_STYLE = """
QDialog, QMainWindow {
    background-color: #1e1e1e;
}
QLabel {
    color: #e0e0e0;
    font-family: 'Segoe UI';
    font-size: 13px;
}
QLineEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 8px 12px;
    font-family: 'Segoe UI';
}
QLineEdit:focus {
    border: 1px solid #00d26a;
}
QListWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 4px;
}
QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}
QListWidget::item:hover {
    background-color: #3d3d3d;
}
QCheckBox {
    color: #e0e0e0;
    font-family: 'Segoe UI';
    spacing: 8px;
}
QPushButton {
    font-family: 'Segoe UI';
    font-weight: bold;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton#DeselectBtn {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
}
QPushButton#DeselectBtn:hover {
    background-color: #3d3d3d;
}
QPushButton#CancelBtn {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
}
QPushButton#CancelBtn:hover {
    background-color: #3d3d3d;
}
QPushButton#OkBtn {
    background-color: #00d26a;
    color: #1e1e1e;
    border: none;
}
QPushButton#OkBtn:hover {
    background-color: #00b359;
}
"""

def get_readable_language_name(sub_string):
    import re
    match = re.search(r'\((.*?)\)', sub_string)
    if not match:
        return sub_string
        
    lang_code = match.group(1).lower()
    is_auto = "Auto-generated" in sub_string
    
    try:
        lang = pycountry.languages.get(alpha_2=lang_code)
        if not lang:
            lang = pycountry.languages.get(alpha_3=lang_code)
            
        if lang:
            lang_name = lang.name
            if is_auto:
                return f"{lang_name} ({lang_code}) [Auto-generated]"
            else:
                return f"{lang_name} ({lang_code})"
    except Exception:
        pass
        
    return sub_string


class SubtitleSelectDialog(QDialog):
  def __init__(self, subtitles, pre_selected=None, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Select Subtitles")
    self.resize(515, 433)
    self.setMinimumSize(515, 435)
    
    self.setStyleSheet(DARK_STYLE)
    
    self.pre_selected = pre_selected if pre_selected is not None else []

    layout = QVBoxLayout(self)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)

    # 1. Search / Filter Box
    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText("Filter languages (e.g., Burmese, my, en)...")
    self.search_input.setClearButtonEnabled(True) # Clear (✕) Button လေး ပေါ်လာစေရန် ထည့်သွင်းခြင်း
    self.search_input.textChanged.connect(self.filter_subtitles)
    layout.addWidget(self.search_input)

    # 2. Subtitles List
    self.list_widget = QListWidget()
    self.list_widget.setAutoScroll(False)
    
    self.all_subtitles = [get_readable_language_name(sub) for sub in subtitles]
    
    self.populate_list(self.all_subtitles)
    layout.addWidget(self.list_widget)

    # 3. Bottom Action Buttons Layout
    bottom_layout = QHBoxLayout()
    bottom_layout.setContentsMargins(0, 0, 0, 0)

    self.deselect_btn = QPushButton("Deselect all")
    self.deselect_btn.setObjectName("DeselectBtn")
    self.deselect_btn.setCursor(Qt.PointingHandCursor)
    self.deselect_btn.clicked.connect(self.deselect_all)
    bottom_layout.addWidget(self.deselect_btn)

    # 👇 ပုံထဲကလိုမျိုး Selected အရေအတွက်ပြမည့် QLabel ကို ဖန်တီး၍ ထည့်သွင်းခြင်း
    self.selected_count_lbl = QLabel("0 Selected")
    self.selected_count_lbl.setStyleSheet("color: #a0a0a0; font-weight: bold;")
    bottom_layout.addWidget(self.selected_count_lbl)

    bottom_layout.addStretch()

    self.ok_btn = QPushButton("OK")
    self.ok_btn.setObjectName("OkBtn")
    self.ok_btn.setCursor(Qt.PointingHandCursor)
    self.ok_btn.clicked.connect(self.accept)
    bottom_layout.addWidget(self.ok_btn)

    self.cancel_btn = QPushButton("Cancel")
    self.cancel_btn.setObjectName("CancelBtn")
    self.cancel_btn.setCursor(Qt.PointingHandCursor)
    self.cancel_btn.clicked.connect(self.reject)
    bottom_layout.addWidget(self.cancel_btn)

    layout.addLayout(bottom_layout)

    # ပထမအကြိမ် ဖွင့်ချိန်မှာ pre_selected ပါလာရင် ကောင်တာကို ချက်ချင်း Update လုပ်ရန်
    self.update_selected_count()

  def populate_list(self, subtitles):
    self.list_widget.clear()
    for sub in subtitles:
      item = QListWidgetItem(self.list_widget)
      checkbox = QCheckBox(sub)
      
      if sub in self.pre_selected:
        checkbox.setChecked(True)
        
      # 👇 Checkbox State ပြောင်းလဲတိုင်း update_selected_count ကို ချိတ်ဆက်ပေးခြင်း
      checkbox.stateChanged.connect(self.update_selected_count)
      
      self.list_widget.setItemWidget(item, checkbox)
      item.setData(Qt.ItemDataRole.UserRole, sub)

  def update_selected_count(self):
    """ Realtime ဖြင့် အမှန်ခြစ်ထားသော အရေအတွက်ကို ရေတွက်ပြီး Label တွင် ပြသရန် """
    count = 0
    for i in range(self.list_widget.count()):
      item = self.list_widget.item(i)
      widget = self.list_widget.itemWidget(item)
      if isinstance(widget, QCheckBox) and widget.isChecked():
        count += 1
    self.selected_count_lbl.setText(f"{count} Selected")

  def filter_subtitles(self, text):
    search_text = text.lower()
    for i in range(self.list_widget.count()):
      item = self.list_widget.item(i)
      sub_text = item.data(Qt.ItemDataRole.UserRole) or ""
      
      if search_text in sub_text.lower():
        item.setHidden(False)
      else:
        item.setHidden(True)

  def deselect_all(self):
    for i in range(self.list_widget.count()):
      item = self.list_widget.item(i)
      widget = self.list_widget.itemWidget(item)
      if isinstance(widget, QCheckBox):
        widget.blockSignals(True)   # Signal ခဏပိတ်ပြီး ဖြုတ်မည် (စွမ်းဆောင်ရည်ကောင်းစေရန်)
        widget.setChecked(False)
        widget.blockSignals(False)
    # အားလုံးဖြုတ်ပြီးပါက ကောင်တာကို ချက်ချင်း Update လုပ်ရန်
    self.update_selected_count()

  def get_selected_subtitles(self):
    selected = []
    for i in range(self.list_widget.count()):
      item = self.list_widget.item(i)
      widget = self.list_widget.itemWidget(item)
      if isinstance(widget, QCheckBox) and widget.isChecked():
        selected.append(widget.text())
    return selected


class MainWindow(QMainWindow):

  def __init__(self):
    super().__init__()
    self.setWindowTitle("Subtitle Dialog Test")
    self.resize(500, 300)
    
    # 🌟 ရွေးချယ်ခဲ့ပြီးသား Subtitle များကို သိမ်းဆည်းထားမည့် variable (Memory တွင် မှတ်ထားခြင်း)
    self.saved_selected_subtitles = []

    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    open_dialog_btn = QPushButton("Open Subtitle Selector")
    open_dialog_btn.clicked.connect(self.show_dialog)
    layout.addWidget(open_dialog_btn)

  def show_dialog(self):
    subtitles = [
        "(ab) [Auto-generated]",
        "(af) [Auto-generated]",
        "(aa) [Auto-generated]",
        "(am) [Auto-generated]",
        "(ar) [Auto-generated]",
        "(hy) [Auto-generated]",
        "(as) [Auto-generated]",
        "(az) [Auto-generated]",
        "(bn) [Auto-generated]",
        "(eu) [Auto-generated]",
        "(be) [Auto-generated]",
        "(my) [Auto-generated]",
        "(zh) [Auto-generated]",
        "(en) [Auto-generated]",
        "(fr) [Auto-generated]",
        "(de) [Auto-generated]",
        "(ja) [Auto-generated]",
        "(ko) [Auto-generated]",
        "(es) [Auto-generated]",
        "(th) [Auto-generated]",
        "(vi) [Auto-generated]",
    ]
    
    # Dialog ကို ခေါ်တဲ့အခါ သိမ်းထားတဲ့ saved_selected_subtitles ကို ထည့်ပေးလိုက်ပါ
    dialog = SubtitleSelectDialog(subtitles, pre_selected=self.saved_selected_subtitles, parent=self)
    
    if dialog.exec() == QDialog.Accepted:
      # OK နှိပ်လိုက်သည့်အခါ ရွေးချယ်ထားသည်များကို variable ထဲ ပြန်သိမ်းမည်
      self.saved_selected_subtitles = dialog.get_selected_subtitles()
      print("Selected & Saved:", self.saved_selected_subtitles)


if __name__ == "__main__":
  app = QApplication(sys.argv)
  app.setStyleSheet(DARK_STYLE)
  window = MainWindow()
  window.show()
  sys.exit(app.exec())