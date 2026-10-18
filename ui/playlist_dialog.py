# -*- coding: utf-8 -*-
"""
Playlist Selection Dialog

Playlist ထဲမှ ဗီဒီယိုများကို Checkbox များဖြင့် ရွေးချယ်နိုင်သည့် UI Dialog
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QCheckBox, QWidget
)
from PySide6.QtCore import Qt


class PlaylistDialog(QDialog):
    def __init__(self, playlist_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Videos from Playlist")
        self.resize(750, 480)

        self.playlist_info = playlist_info
        self.selected_entries = []

        layout = QVBoxLayout(self)

        # Header Info
        title = playlist_info.get("title", "Playlist")
        entries = playlist_info.get("entries", [])
        self.lblInfo = QLabel(f"<b>Playlist:</b> {title} ({len(entries)} items found)")
        layout.addWidget(self.lblInfo)

        # Table Widget
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Select", "Title", "Duration"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        # ပထမ Select column ရဲ့ အကျယ်ကို ၆၀ Pixel သတ်မှတ်
        self.tableWidget.setColumnWidth(0, 50)
        
        # ✨ Double click နှိပ်၍ Edit လုပ်ခြင်းကို တားမြစ်ရန်
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # ✨ Row တစ်ခုခုကို နှိပ်လိုက်ပါက Checkbox ကို Toggle လုပ်ရန် Signal ချိတ်ဆက်ခြင်း
        self.tableWidget.itemClicked.connect(self.on_item_clicked)

        layout.addWidget(self.tableWidget)

        # Populate Table
        self.populate_table(entries)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()

        self.chkSelectAll = QCheckBox("Select / Deselect All")
        self.chkSelectAll.setChecked(True)
        self.chkSelectAll.stateChanged.connect(self.toggle_select_all)
        btn_layout.addWidget(self.chkSelectAll)
        
        # ခလုတ်များ၏ အရွယ်အစားနှင့် ပုံစံကို သင့်တင့်မျှတအောင် ပြင်ဆင်ခြင်း
        button_style = """
            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 2px 7px;
                font-size: 11pt;
                font-weight: normal;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #64748b;
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
            QPushButton:disabled {
                background-color: #121212;
                color: #555555;
                border-color: #2a2a2a;
            }
        """

        btn_layout.addStretch()

        # Start Download Button
        self.btnAddQueue = QPushButton("Start Download")
        self.btnAddQueue.setStyleSheet(button_style)
        self.btnAddQueue.clicked.connect(self.accept_selection)
        btn_layout.addWidget(self.btnAddQueue)

        # Save Playlist Button
        self.btnSave = QPushButton("Save Playlist")
        self.btnSave.setStyleSheet(button_style)
        self.btnSave.clicked.connect(self.save_playlist_to_file)
        btn_layout.addWidget(self.btnSave)

        self.btnCancel = QPushButton("Cancel")
        self.btnCancel.setStyleSheet(button_style)
        self.btnCancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btnCancel)

        layout.addLayout(btn_layout)

        # စစဖွင့်ချင်း Selected State ကို စစ်ဆေးမည်
        self.update_add_queue_button_state()

    def populate_table(self, entries):
        self.tableWidget.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            # Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(True)
            # Checkbox တစ်ခုချင်းစီ နှိပ်လိုက်တိုင်း Button State ကို စစ်ဆေးရန် ချိတ်ဆက်ခြင်း
            chk.stateChanged.connect(self.update_add_queue_button_state)
            chk_layout.addWidget(chk)
            self.tableWidget.setCellWidget(row, 0, chk_widget)

            # Title (Editable မဖြစ်စေရန် Flag များကို သတ်မှတ်ခြင်း)
            item_title = entry.get("title", "Unknown Title")
            title_item = QTableWidgetItem(item_title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
            self.tableWidget.setItem(row, 1, title_item)

            # Duration (Editable မဖြစ်စေရန် Flag များကို သတ်မှတ်ခြင်း)
            duration = entry.get("duration") or 0
            try:
                sec = int(duration)
                dur_str = f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60}:{sec % 60:02d}"
            except Exception:
                dur_str = "N/A"
            dur_item = QTableWidgetItem(dur_str)
            dur_item.setFlags(dur_item.flags() & ~Qt.ItemIsEditable)
            self.tableWidget.setItem(row, 2, dur_item)

    def on_item_clicked(self, item):
        """ Table ထဲရှိ Row တစ်ခုခုကို နှိပ်လိုက်လျှင် Checkbox ကို Toggle လုပ်ပေးရန် """
        row = item.row()
        chk_widget = self.tableWidget.cellWidget(row, 0)
        if chk_widget:
            chk = chk_widget.findChild(QCheckBox)
            if chk:
                # လက်ရှိ Check ပြီးသားဆိုရင် ဖြုတ်မည်၊ မပါရင် ထည့်မည်
                chk.setChecked(not chk.isChecked())

    def toggle_select_all(self, state):
        is_checked = (state == Qt.CheckState.Checked.value or state == True)
        for row in range(self.tableWidget.rowCount()):
            chk_widget = self.tableWidget.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk:
                    chk.blockSignals(True)
                    chk.setChecked(is_checked)
                    chk.blockSignals(False)
        # အားလုံးပြောင်းပြီးပါက Button State ကို တစ်ခါတည်း စစ်ဆေး update လုပ်မည်
        self.update_add_queue_button_state()

    def update_add_queue_button_state(self):
        """ ရွေးချယ်ထားသော (Checked) ဗီဒီယို အရေအတွက် 0 ဖြစ်နေပါက Add to Queue ခလုတ်ကို ပိတ်မည် """
        selected_count = 0
        for row in range(self.tableWidget.rowCount()):
            chk_widget = self.tableWidget.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    selected_count += 1

        if selected_count > 0:
            self.btnAddQueue.setEnabled(True)
            self.btnAddQueue.setText(f"Start Download ({selected_count})")
        else:
            self.btnAddQueue.setEnabled(False)
            self.btnAddQueue.setText("Select Videos to Download")

    def accept_selection(self):
        entries = self.playlist_info.get("entries", [])
        self.selected_entries = []

        for row in range(self.tableWidget.rowCount()):
            chk_widget = self.tableWidget.cellWidget(row, 0)
            if chk_widget:
                chk = chk_widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    if row < len(entries):
                        self.selected_entries.append(entries[row])

        self.accept()

    def get_selected_entries(self) -> list[dict]:
        return self.selected_entries

    def save_playlist_to_file(self):
        """ Playlist ထဲရှိ ဗီဒီယိုစာရင်းများကို .txt, .m3u, .csv, .json ပုံစံများဖြင့် သိမ်းဆည်းရန် """
        import os
        import csv
        import json
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        # Current Output Folder Path ကို ရှာဖွေခြင်း (parent window မှတဆင့်)
        output_dir = ""
        if self.parent() and hasattr(self.parent(), "config_mgr"):
            # Config မှ download_path ကို ယူမည် (မရှိပါက default_download_dir သို့ အသုံးပြုမည်)
            output_dir = self.parent().config_mgr.get("download_path", "")
        
        # တကယ်လို့ output_dir မရှိပါက သို့မဟုတ် path မမှန်ပါက default path ကို သုံးမည်
        if not output_dir or not os.path.isdir(output_dir):
            from PySide6.QtCore import QStandardPaths
            downloads_loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            output_dir = os.path.normpath(os.path.join(downloads_loc, 'U-Tube Downloader'))
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

        # Default file name အဖြစ် Playlist title ကို သုံးရန်
        playlist_title = self.playlist_info.get("title", "playlist")
        # File နာမည်မသင့်လျော်တာတွေ မပါအောင် ရှင်းထုတ်ခြင်း
        safe_title = "".join(c for c in playlist_title if c.isalnum() or c in (' ', '_', '-')).strip()
        default_filename = os.path.join(output_dir, f"{safe_title}.json")

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Playlist",
            default_filename,
            "JSON Files (*.json);;Text Files (*.txt);;M3U Playlist (*.m3u);;CSV Files (*.csv)"
        )

        if not file_path:
            return

        entries = self.playlist_info.get("entries", [])
        
        try:
            if file_path.endswith(".json"):
                # JSON Format ဖြင့် သိမ်းဆည်းရန်
                data_to_save = {
                    "title": playlist_title,
                    "total_items": len(entries),
                    "entries": entries
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=4)

            elif file_path.endswith(".txt"):
                # Plain Text Format ဖြင့် သိမ်းဆည်းရန်
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Playlist: {playlist_title}\n")
                    f.write(f"Total Items: {len(entries)}\n")
                    f.write("=" * 50 + "\n\n")
                    for i, entry in enumerate(entries, 1):
                        title = entry.get("title", "Unknown")
                        url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
                        duration = entry.get("duration", 0)
                        f.write(f"{i}. {title}\n   URL: {url}\n   Duration: {duration}s\n\n")

            elif file_path.endswith(".m3u"):
                # M3U Playlist Format ဖြင့် သိမ်းဆည်းရန် (Media players တွေမှာ ဖွင့်လို့ရရန်)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    for entry in entries:
                        title = entry.get("title", "Unknown")
                        url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
                        duration = entry.get("duration", -1)
                        f.write(f"#EXTINF:{duration},{title}\n")
                        f.write(f"{url}\n")

            elif file_path.endswith(".csv"):
                # CSV Format ဖြင့် သိမ်းဆည်းရန်
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Index", "Title", "Duration", "URL"])
                    for i, entry in enumerate(entries, 1):
                        title = entry.get("title", "Unknown")
                        url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
                        duration = entry.get("duration", 0)
                        writer.writerow([i, title, duration, url])

            QMessageBox.information(self, "Success", f"Playlist successfully saved to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save playlist:\n{str(e)}")