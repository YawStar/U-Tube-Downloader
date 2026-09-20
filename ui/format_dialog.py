import os
import shutil  # Drive Free Space စစ်ဆေးရန်
from PySide6.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QAbstractItemView, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class FormatDialog(QDialog):
    """ Available Formats များကို တစ်ဆက်တည်း Segmented Buttons (All, Video Only, Audio Only)၊
    Auto-Select စနစ်၊ Free Space စစ်ဆေးမှုစနစ်တို့ဖြင့် ပြသပေးမည့် Window """

    # current_format_id ပါရာမီတာကို လက်ခံရန် ထည့်သွင်းခြင်း (Default: None)
    def __init__(self, json_data, current_format_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Available Formats")
        self.resize(850, 550)
        
        self.raw_info = json_data
        self.parent_win = parent
        self.parsed_formats = [] # Parse လုပ်ပြီးသား အချက်အလက်အားလုံး သိုလှောင်ရန်
        self.current_filter = "All" # လက်ရှိ ရွေးထားတဲ့ Filter (Default: All)

        # လက်ရှိရွေးထားသော Format ID ကို စာသား (String) ပုံစံဖြင့် သိမ်းဆည်းမှတ်သားခြင်း
        self.saved_format_id = str(current_format_id) if current_format_id is not None else None

        # Main Window ရဲ့ StyleSheet ကို အမွေဆက်ခံခြင်း
        if parent and hasattr(parent, 'styleSheet'):
            self.setStyleSheet(parent.styleSheet())

        # ပင်မ Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # -------------------------------------------------------------
        # Segmented Control တည်ဆောက်ခြင်း
        # -------------------------------------------------------------
        filter_container_layout = QHBoxLayout()

        # ခလုတ်များကို တစ်သားတည်းဖြစ်အောင် Container Frame တစ်ခုဆောက်ပြီး ထည့်ခြင်း
        self.segmented_frame = QFrame()
        self.segmented_frame.setObjectName("SegmentedControl")
        
        # Frame ထဲရှိ ခလုတ်များ ကပ်နေစေရန် Spacing ကို 0 ထားပြီး Margin ကို သပ်ရပ်အောင် ချိန်ခြင်း
        segmented_layout = QHBoxLayout(self.segmented_frame)
        segmented_layout.setContentsMargins(2, 2, 2, 2)
        segmented_layout.setSpacing(0)

        # ခလုတ်များ ဖန်တီးခြင်း
        self.btn_filter_all = QPushButton("All")
        self.btn_filter_video = QPushButton("Video Only")
        self.btn_filter_audio = QPushButton("Audio Only")
        
        self.btn_filter_all.setObjectName("btn_all")
        self.btn_filter_video.setObjectName("btn_video")
        self.btn_filter_audio.setObjectName("btn_audio")

        for btn in [self.btn_filter_all, self.btn_filter_video, self.btn_filter_audio]:
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            btn.setMinimumWidth(100)
            # Focus Box အစစ်အမှန်ကြီး ပတ်လည်ပေါ်နေခြင်းကို ဖျောက်ရန် FocusPolicy သတ်မှတ်ခြင်း
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
            segmented_layout.addWidget(btn)

        # အဝိုင်းစတိုင်လ် QSS stylesheet
        self.segmented_frame.setStyleSheet("""
            QFrame#SegmentedControl {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                font-size: 13px;
                font-weight: 500;
                padding: 5px 15px;
            }
            
            QPushButton:hover {
                color: #ffffff;
                background-color: #273549;
            }
            
            /* နှိပ်လိုက်တဲ့အခါ တောက်ပြောင်ပြီး အနားသတ်ဝိုင်းဝိုင်းလေးနဲ့ ထွက်လာမယ့် အစိမ်းရောင် Active State */
            QPushButton:checked {
                background-color: #2ecc71;
                color: #000000;
                font-weight: bold;
                border-radius: 6px;
            }
            
            /* ခလုတ်များ တစ်ခုနဲ့တစ်ခုအကူးအစပ်တွင် ပိုမိုသပ်ရပ်စေရန် Border Radius ထိန်းချုပ်မှု */
            QPushButton#btn_all:checked {
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QPushButton#btn_audio:checked {
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
            }
        """)

        filter_container_layout.addWidget(self.segmented_frame)
        filter_container_layout.addStretch() # ညာဘက်သို့ ကပ်ထားရန်
        layout.addLayout(filter_container_layout)

        # -------------------------------------------------------------
        # QTableWidget (ဇယားကွက်) တည်ဆောက်ခြင်း
        # -------------------------------------------------------------
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels([
            "Format ID", "Type", "Resolution / Quality", "Extension", "File Size"
        ])
        
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setAlternatingRowColors(True)
        
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tableWidget)

        # Table Widget အတွက် Hover ရော၊ Selection အရောင်ပါ သီးသန့်ခွဲခြားသတ်မှတ်ခြင်း
        self.tableWidget.setStyleSheet("""
            QTableWidget::item:hover {
                background-color: #334155 !important;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #2563eb !important;
                color: #ffffff;
                font-weight: bold;
            }
        """)

        # -------------------------------------------------------------
        # အောက်ခြေ စာသားနှင့် ခလုတ်များ (Free Space Warning & Buttons)
        # -------------------------------------------------------------
        bottom_layout = QHBoxLayout()
        
        self.lbl_space_info = QLabel("Select a format to check disk space...")
        self.lbl_space_info.setStyleSheet("font-weight: bold;")
        bottom_layout.addWidget(self.lbl_space_info)
        bottom_layout.addStretch()
        
        self.btn_clear_select = QPushButton("Select None")
        self.btn_select = QPushButton("Select Format")
        self.btn_cancel = QPushButton("Cancel")

        # ခလုတ်များကို သီးသန့် Control လုပ်နိုင်ရန် Object Name များ တပ်
        self.btn_select.setObjectName("btn_dialog_action")
        self.btn_clear_select.setObjectName("btn_dialog_secondary")
        self.btn_cancel.setObjectName("btn_dialog_secondary")

        self.btn_select.setMinimumHeight(32)
        self.btn_clear_select.setMinimumHeight(32)
        self.btn_cancel.setMinimumHeight(32)

        bottom_layout.addWidget(self.btn_select)
        bottom_layout.addWidget(self.btn_clear_select)
        bottom_layout.addWidget(self.btn_cancel)
        layout.addLayout(bottom_layout)

        # Main Window ရဲ့ StyleSheet ကို အမွေဆက်ခံခြင်း
        if parent and hasattr(parent, 'styleSheet'):
            self.setStyleSheet(parent.styleSheet())

        # Global CSS ၏ ဖိနှိပ်မှုကို Overwrite လုပ်ရန် FormatDialog အတွက် သီးသန့် Style ထပ်ပေါင်းထည့်ခြင်း
        self.setStyleSheet(self.styleSheet() + """
            /* Select Format ခလုတ် (Primary Accent Button) */
            QPushButton#btn_dialog_action {
                background-color: #2563eb !important;
                color: #ffffff !important;
                border: 1px solid #3b82f6 !important;
                border-radius: 6px !important;
                padding: 5px 15px !important;
                font-weight: bold !important;
            }
            QPushButton#btn_dialog_action:hover {
                background-color: #1d4ed8 !important;
            }
            QPushButton#btn_dialog_action:disabled {
                background-color: #334155 !important;
                color: #64748b !important;
                border: 1px solid #475569 !important;
            }

            /* Select None နှင့် Cancel ခလုတ်များ (Secondary Dark Buttons) */
            QPushButton#btn_dialog_secondary {
                background-color: #1e293b !important;
                color: #f8fafc !important;
                border: 1px solid #475569 !important;
                border-radius: 6px !important;
                padding: 5px 15px !important;
                font-weight: normal !important;
            }
            QPushButton#btn_dialog_secondary:hover {
                background-color: #334155 !important;
                border-color: #64748b !important;
            }
            QPushButton#btn_dialog_secondary:pressed {
                background-color: #0f172a !important;
            }
        """)
        
        # -------------------------------------------------------------
        # Signals နှင့် ခလုတ်နှိပ်ခြင်း Logic များ
        # -------------------------------------------------------------
        self.btn_clear_select.clicked.connect(self.clear_and_accept)
        self.btn_select.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.tableWidget.itemDoubleClicked.connect(lambda item: self.accept())
        
        # Segmented Filter Buttons များအတွက် Click Signal ချိတ်ဆက်ခြင်း
        self.btn_filter_all.clicked.connect(lambda: self.change_filter("All"))
        self.btn_filter_video.clicked.connect(lambda: self.change_filter("Video Only"))
        self.btn_filter_audio.clicked.connect(lambda: self.change_filter("Audio Only"))
        
        # Table ထဲမှာ စာကြောင်း ရွေးချယ်မှု ပြောင်းလဲတိုင်း Disk Space စစ်ခိုင်းခြင်း
        self.tableWidget.itemSelectionChanged.connect(self.check_disk_space_status)

        # ဒေတာများကို ပထမဦးဆုံးအကြိမ် Parsing ပြုလုပ်ခြင်း
        self.prepare_data()
        
        # စဖွင့်ချင်း "All" ခလုတ်အား Active အဖြစ် သတ်မှတ်ခြင်း
        self.change_filter("All")

    def change_filter(self, filter_type):
        """ ခလုတ်တစ်ခုနှိပ်လျှင် Frame တစ်ခုတည်းအတွင်း၌ တစ်သားတည်း ရွေ့သွားသကဲ့သို့ ပုံစံမျိုး ထိန်းချုပ်ခြင်း """
        # ခလုတ်မပြောင်းခင် User လက်ရှိတကယ် ရွေးချယ်ထားတဲ့ Row ရဲ့ ID ကို ဖမ်းယူပြီး saved_format_id ထဲ ခဏပြောင်းသိမ်းလိုက်ခြင်း
        # ဒါမှ Filter ပြောင်းသွားတဲ့အခါ လက်ရှိရွေးထားတဲ့ ID အမှန်ကို သိရှိပြီး လိုက်ရှာနိုင်မှာ ဖြစ်ပါတယ်
        current_active_id = self.get_selected_format_id()
        if current_active_id:
            self.saved_format_id = current_active_id

        self.current_filter = filter_type
        
        # Toggle Status များကို စနစ်တကျ လိုက်ပြောင်းပေးခြင်း
        self.btn_filter_all.setChecked(filter_type == "All")
        self.btn_filter_video.setChecked(filter_type == "Video Only")
        self.btn_filter_audio.setChecked(filter_type == "Audio Only")
        
        # ဇယားကွက်ကို Filter အသစ်ဖြင့် ပြန်လည်ရေးဆွဲခြင်း
        self.refresh_table_view()

    def prepare_data(self):
        """ yt-dlp JSON မှ Format များကို ကြိုတင် Parse လုပ်၍ သိမ်းဆည်းထားခြင်း """
        if not self.raw_info: return
        formats_list = self.raw_info.get('formats', [])

        def format_size_str(bytes_size):
            if not bytes_size: return "Unknown Size"
            bytes_size = float(bytes_size)
            for unit in ['Bytes', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0: return f"{bytes_size:.2f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.2f} TB"

        for f in formats_list:
            if f.get('format_note') == 'storyboard': continue

            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            filesize = f.get('filesize') or f.get('filesize_approx') or 0
            height = f.get('height') or 0
            
            if vcodec != 'none' and acodec != 'none': media_type = "Video + Audio"
            elif vcodec != 'none': media_type = "Video Only"
            elif acodec != 'none': media_type = "Audio Only"
            else: media_type = "Unknown"

            self.parsed_formats.append({
                "format_id": f.get('format_id', 'N/A'),
                "extension": f.get('ext', 'N/A').upper(),
                "type": media_type,
                "quality_note": f.get('format_note', f.get('resolution', 'N/A')),
                "resolution": f.get('resolution', 'N/A'),
                "height": height, 
                "raw_size": filesize, 
                "file_size_str": format_size_str(filesize)
            })

    def refresh_table_view1(self):
        """ ရွေးချယ်ထားသော Filter အလိုက် ဇယားကွက်ကို တိကျစွာ ပြန်လည်ရေးဆွဲပေးခြင်း """
        filtered_list = []
        for f in self.parsed_formats:
            if self.current_filter == "Video Only" and f['type'] != "Video Only": continue
            if self.current_filter == "Audio Only" and f['type'] != "Audio Only": continue
            filtered_list.append(f)

        self.tableWidget.setRowCount(len(filtered_list))
        
        video_color = QColor("#1e293b")
        audio_color = QColor("#064e3b")
        muxed_color = QColor("#111827") 
        
        best_row_index = 0
        max_height = -1

        for row, item_info in enumerate(filtered_list):
            item_id = QTableWidgetItem(item_info['format_id'])
            item_type = QTableWidgetItem(item_info['type'])
            item_quality = QTableWidgetItem(f"{item_info['resolution']} ({item_info['quality_note']})")
            item_ext = QTableWidgetItem(item_info['extension'])
            item_size = QTableWidgetItem(item_info['file_size_str'])

            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ext.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            if item_info['type'] == "Video Only":
                current_color = video_color
            elif item_info['type'] == "Audio Only":
                current_color = audio_color
            else:
                current_color = muxed_color 

            for item in [item_id, item_type, item_quality, item_ext, item_size]:
                item.setBackground(current_color)

            item_id.setData(Qt.ItemDataRole.UserRole, item_info)

            self.tableWidget.setItem(row, 0, item_id)
            self.tableWidget.setItem(row, 1, item_type)
            self.tableWidget.setItem(row, 2, item_quality)
            self.tableWidget.setItem(row, 3, item_ext)
            self.tableWidget.setItem(row, 4, item_size)

            if "Video" in item_info['type'] and item_info['height'] > max_height:
                max_height = item_info['height']
                best_row_index = row

        if len(filtered_list) > 0:
            self.tableWidget.selectRow(best_row_index)
            self.tableWidget.scrollToItem(self.tableWidget.item(best_row_index, 0))

    def refresh_table_view(self):
        """ ရွေးချယ်ထားသော Filter အလိုက် ဇယားကွက်ကို တိကျစွာ ပြန်လည်ရေးဆွဲပေးခြင်း 
        (Auto-Select မလုပ်တော့ဘဲ Best Row ကို သီးသန့် Highlight အရောင်ဖြင့်သာ ပြသခြင်း) """
        filtered_list = []
        for f in self.parsed_formats:
            if self.current_filter == "Video Only" and f['type'] != "Video Only": continue
            if self.current_filter == "Audio Only" and f['type'] != "Audio Only": continue
            filtered_list.append(f)

        self.tableWidget.setRowCount(len(filtered_list))
        
        video_color = QColor("#1e293b")
        audio_color = QColor("#064e3b")
        muxed_color = QColor("#111827") 
        
        # Best Row ကို ရှာဖွေရန် Variable များ
        best_row_index = -1
        max_height = -1
        
        # ယခင်ရွေးချယ်ထားခဲ့ဖူးသော ID တည်ရှိသည့် စာကြောင်း (Row) ကို သိရှိရန်
        target_select_row = -1

        # ပထမအဆင့် - အကောင်းဆုံး လိုင်း (Best Quality Row) ဘယ်နေရာမှာလဲဆိုတာ အရင်ရှာဖွေခြင်း
        for row, item_info in enumerate(filtered_list):
            if "Video" in item_info['type'] and item_info['height'] > max_height:
                max_height = item_info['height']
                best_row_index = row
                
            # လက်ရှိ Row ရဲ့ ID က ယခင်ရွေးခဲ့ဖူးတဲ့ ID ဖြစ်နေသလား စစ်ဆေးခြင်း
            if self.saved_format_id and item_info['format_id'] == self.saved_format_id:
                target_select_row = row

        # ဒုတိယအဆင့် - ဇယားကွက်ထဲသို့ Data များ ထည့်သွင်းခြင်း
        for row, item_info in enumerate(filtered_list):
            item_id = QTableWidgetItem(item_info['format_id'])
            item_type = QTableWidgetItem(item_info['type'])
            item_quality = QTableWidgetItem(f"{item_info['resolution']} ({item_info['quality_note']})")
            item_ext = QTableWidgetItem(item_info['extension'])
            item_size = QTableWidgetItem(item_info['file_size_str'])

            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ext.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # မူရင်း Type အလိုက် Background အရောင် သတ်မှတ်ခြင်း
            if item_info['type'] == "Video Only":
                current_color = video_color
            elif item_info['type'] == "Audio Only":
                current_color = audio_color
            else:
                current_color = muxed_color 

            for item in [item_id, item_type, item_quality, item_ext, item_size]:
                item.setBackground(current_color)
                
                # အကောင်းဆုံး Format (Best Row) ဖြစ်ပါက အစိမ်းရောင်ဖျော့ဖျော့ စာသားဖြင့် Highlight လုပ်ပေးခြင်း
                if row == best_row_index:
                    # စာသားအရောင်ကို အစိမ်းရောင်တောက်တောက် (#2ecc71) သို့မဟုတ် ရွှေရောင် ပြောင်းပေးနိုင်ပါတယ်
                    item.setForeground(QColor("#2ecc71"))
                    # စာသားကိုပါ Bold (အထူ) လုပ်ပေးပြီး ပိုမိုသိသာစေခြင်း
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

            item_id.setData(Qt.ItemDataRole.UserRole, item_info)

            self.tableWidget.setItem(row, 0, item_id)
            self.tableWidget.setItem(row, 1, item_type)
            self.tableWidget.setItem(row, 2, item_quality)
            self.tableWidget.setItem(row, 3, item_ext)
            self.tableWidget.setItem(row, 4, item_size)

        # တိကျသော Selection Logic]
        # အသုံးပြုသူ ယခင်က ရွေးချယ်ထားခဲ့ဖူးသော ID ဇယားကွက်ထဲတွင် တည်ရှိနေပါက ၎င်းကို အပြာရောင် Selected Highlight ဖြင့် တန်းပြသပေးမည်
        if target_select_row != -1:
            self.tableWidget.selectRow(target_select_row)
            self.tableWidget.scrollToItem(self.tableWidget.item(target_select_row, 0))
        # Filter အကူးအပြောင်းကြောင့် လက်ရှိဇယားထဲမှာ အဆိုပါ ID မရှိတော့ပါက
        # အတင်းအဓမ္မ တခြား Row တွေကို လျှောက်မရွေးတော့ဘဲ Selection လုံးဝ ဖြုတ်ပစ်ပါမည်။ ဘာမှမရွေးထားတဲ့ သန့်ရှင်းတဲ့ အခြေအနေ ဖြစ်သွားပါမယ်။
        else:
            self.tableWidget.clearSelection()
            # Selection မရှိသော်လည်း အမြင်အဆင်ပြေစေရန် အကောင်းဆုံးလိုင်းဆီသို့ Scroll သာ ဆွဲပေးထားပါမည်
            if best_row_index != -1:
                self.tableWidget.scrollToItem(self.tableWidget.item(best_row_index, 0))

    def check_disk_space_status1(self):
        """ ရွေးချယ်လိုက်သော Format ၏ ဖိုင်ဆိုဒ်သည် ဒေါင်းလုဒ်လုပ်မည့် Drive ၏ Free Space ထက် လောက်/မလောက် စစ်ဆေးခြင်း """
        selected_ranges = self.tableWidget.selectedRanges()
        if not selected_ranges:
            self.lbl_space_info.setText("Select a format to check disk space...")
            self.lbl_space_info.setStyleSheet("color: #ffffff;")
            self.btn_select.setEnabled(False)
            return

        selected_row = selected_ranges[0].topRow()
        item_info = self.tableWidget.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not item_info: return

        file_bytes = item_info['raw_size']
        download_dir = "./"
        
        if self.parent_win and hasattr(self.parent_win, 'downloadFolderInput'):
            potential_dir = self.parent_win.downloadFolderInput.text().strip()
            if os.path.exists(potential_dir):
                download_dir = potential_dir

        try:
            total, used, free_bytes = shutil.disk_usage(os.path.abspath(download_dir))
            def to_gb(b): return b / (1024**3)

            if file_bytes == 0:
                self.lbl_space_info.setText(f"Drive Space: {to_gb(free_bytes):.2f} GB Free (Format size is approximate/unspecified).")
                self.lbl_space_info.setStyleSheet("color: #00A2FF;") 
                self.btn_select.setEnabled(True)
            elif free_bytes < (file_bytes * 1.2):
                self.lbl_space_info.setText(f"⚠️ Insufficient Space! Required: {to_gb(file_bytes):.2f} GB | Free: {to_gb(free_bytes):.2f} GB")
                self.lbl_space_info.setStyleSheet("color: #ff3333; font-weight: bold;") 
                self.btn_select.setEnabled(True) 
            else:
                self.lbl_space_info.setText(f"✅ Space Available. File Size: {to_gb(file_bytes):.2f} GB | Free Space: {to_gb(free_bytes):.2f} GB")
                self.lbl_space_info.setStyleSheet("color: #22c55e;") 
                self.btn_select.setEnabled(True)
        except Exception:
            self.lbl_space_info.setText("Could not determine disk free space.")
            self.btn_select.setEnabled(True)

    def check_disk_space_status(self):
        """ ဖိုင်ဆိုဒ်အလိုက် လိုက်ဖက်မည့် ယူနစ် (MB/GB) ဖြင့် အောက်ခြေတွင် ကွက်တိ ပြသခြင်း """
        selected_ranges = self.tableWidget.selectedRanges()
        if not selected_ranges:
            self.lbl_space_info.setText("Select a format to check disk space...")
            self.lbl_space_info.setStyleSheet("color: #ffffff;")
            self.btn_select.setEnabled(False)
            return

        selected_row = selected_ranges[0].topRow()
        item_info = self.tableWidget.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not item_info: return

        file_bytes = item_info['raw_size']
        download_dir = "./"
        
        if self.parent_win and hasattr(self.parent_win, 'downloadFolderInput'):
            potential_dir = self.parent_win.downloadFolderInput.text().strip()
            if os.path.exists(potential_dir):
                download_dir = potential_dir

        try:
            total, used, free_bytes = shutil.disk_usage(os.path.abspath(download_dir))
            
            # ဖိုင်ဆိုဒ်ကို ဇယားကွက်ထဲကအတိုင်း လိုက်ဖက်မည့် စာသားအဖြစ် ပြောင်းလဲပေးမည့် Function
            def dynamic_format_size(bytes_size):
                if not bytes_size: return "0 Bytes"
                bytes_size = float(bytes_size)
                for unit in ['Bytes', 'KB', 'MB', 'GB']:
                    if bytes_size < 1024.0: return f"{bytes_size:.2f} {unit}"
                    bytes_size /= 1024.0
                return f"{bytes_size:.2f} TB"

            # အောက်ခြေအတွက် သီးသန့် တွက်ချက်မှုများ
            file_size_display = dynamic_format_size(file_bytes)
            free_gb_display = f"{free_bytes / (1024**3):.2f} GB"

            # ဖိုင်ဆိုဒ်က ၀ ဖြစ်နေရင်
            if file_bytes == 0:
                self.lbl_space_info.setText(f"Drive Space: {free_gb_display} Free (Format size is approximate/unspecified).")
                self.lbl_space_info.setStyleSheet("color: #00A2FF;") 
                self.btn_select.setEnabled(True)
            # ❌ စက်ထဲမှာ နေရာမလောက်ဘူးဆိုရင်
            elif free_bytes < (file_bytes * 1.2):
                self.lbl_space_info.setText(f"⚠️ Insufficient Space! Required: {file_size_display} | Free: {free_gb_display}")
                self.lbl_space_info.setStyleSheet("color: #ff3333; font-weight: bold;") 
                self.btn_select.setEnabled(True) 
            # ✅ နေရာလောက်တယ်ဆိုရင်
            else:
                # 🎯 ဤနေရာတွင် ဇယားကွက်ထဲကအတိုင်း 91.61 MB ဆိုလျှင် 91.61 MB အတိုင်း ကွက်တိ ပြသသွားမည် ဖြစ်ပါသည်
                self.lbl_space_info.setText(f"✅ Space Available. File Size: {file_size_display} | Free Space: {free_gb_display}")
                self.lbl_space_info.setStyleSheet("color: #22c55e;") 
                self.btn_select.setEnabled(True)
        except Exception:
            self.lbl_space_info.setText("Could not determine disk free space.")
            self.btn_select.setEnabled(True)
    
    def get_selected_format_id(self):
        """ အသုံးပြုသူ လက်ရှိ ရွေးချယ်ထားသော စာကြောင်းအားလုံးမှ Format ID များကို '+' ဖြင့် ချိတ်ဆက်ပြီး ပြန်ပေးမည့် Method """
        selected_ranges = self.tableWidget.selectedRanges()
        if not selected_ranges: 
            return None
            
        selected_rows = set()
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                selected_rows.add(row)
                
        format_ids = []
        for row in sorted(selected_rows):
            item = self.tableWidget.item(row, 0) # Column 0 သည် Format ID ဖြစ်သည်
            if item:
                format_ids.append(item.text())
                
        if format_ids:
            # ဥပမာ- ['137', '140'] ဖြစ်ခဲ့လျှင် '137+140' ဟု ပြန်ပေးမည်။ yt-dlp မှ အလိုအလျောက် တွဲပြီး Download ဆွဲသွားပါလိမ့်မည်။
            return "+".join(format_ids)
        return None
    
    def clear_and_accept(self):
        """ ဇယားကွက်ထဲတွင် ရွေးချယ်ထားမှုများကို လုံးဝဖယ်ထုတ်ပြီး ပိတ်ပေးမည် (None အခြေအနေသို့ ရောက်ရှိစေရန်) """
        self.tableWidget.clearSelection() # ဇယားကွက် Selection ဖြုတ်ပစ်ခြင်း
        self.accept() # Window ကို ပိတ်ပြီး အောင်မြင်စွာ ထွက်ခွာခြင်း

    def on_selection_changed(self):
        """ အသုံးပြုသူမှ Table ထဲတွင် Row တစ်ခု (သို့မဟုတ်) တစ်ခုထက်ပို၍ ရွေးချယ်လိုက်သည့်အခါ စုစုပေါင်း File Size ကို တွက်ချက်ပေးမည့် နေရာ """
        # လက်ရှိ ရွေးချယ်ထားသော Ranges များကို ယူသည်
        selected_ranges = self.tableWidget.selectedRanges()
        if not selected_ranges:
            self.lbl_space_info.setText("Select a video and audio format to download.")
            self.lbl_space_info.setStyleSheet("color: #94a3b8;")
            self.btn_select.setEnabled(False)
            return

        # ရွေးချယ်ထားသော ရိုး (Rows) အားလုံးကို စုစည်းမည် (ထပ်နေတာတွေ ဖယ်ဖို့ set သုံးပါမည်)
        selected_rows = set()
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                selected_rows.add(row)

        total_bytes = 0
        
        # ရွေးချယ်ထားသော Row တစ်ခုချင်းစီ၏ Byte အရွယ်အစားကို လိုက်ပေါင်းခြင်း
        for row in selected_rows:
            # Row index ကို သုံးပြီး parsed_formats ထဲက သက်ဆိုင်ရာ data ကို လှမ်းယူခြင်း
            # Filter ကြောင့် ရှုပ်ထွေးမှုမရှိစေရန် table widget item ရဲ့ custom data သို့မဟုတ် row index နဲ့ ချိတ်ဆက်တွက်ချက်ပါသည်
            # (ဒီနေရာတွင် filter ကြောင့် row နေရာ အပြောင်းအလဲရှိနိုင်၍ table item ထဲမှ size_bytes ကို ယူခြင်းက ပိုစိတ်ချရပါသည်)
            size_item = self.tableWidget.item(row, 4) # Column 4 သည် Size ပြသသည့်နေရာဖြစ်သည်
            if size_item and hasattr(size_item, 'raw_bytes'):
                total_bytes += size_item.raw_bytes
            else:
                # အကယ်၍ custom attribute မရှိပါက format data ထဲမှ ပြန်ရှာသည်
                format_id_item = self.tableWidget.item(row, 0)
                if format_id_item:
                    f_id = format_id_item.text()
                    for fmt in self.parsed_formats:
                        if fmt['format_id'] == f_id:
                            total_bytes += fmt.get('filesize_bytes', 0)
                            break

        # စုစုပေါင်း ပမာဏအား Display ပုံစံပြောင်းလဲခြင်း
        if total_bytes >= 1024**3:
            file_size_display = f"{total_bytes / (1024**3):.2f} GB"
        else:
            file_size_display = f"{total_bytes / (1024**2):.2f} MB"

        # စက်ထဲက Free Space ကို စစ်ဆေးခြင်း
        try:
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            total, used, free = shutil.disk_usage(download_dir)
            free_gb_display = f"{free / (1024**3):.2f} GB"

            if total_bytes > free:
                self.lbl_space_info.setText(f"⚠️ Insufficient Space! Required: {file_size_display} | Free: {free_gb_display}")
                self.lbl_space_info.setStyleSheet("color: #ff3333; font-weight: bold;") 
                self.btn_select.setEnabled(False) # နေရာမလောက်လျှင် ခလုတ်ပိတ်မည်
            else:
                self.lbl_space_info.setText(f"✅ Space Available. Total Size: {file_size_display} | Free Space: {free_gb_display}")
                self.lbl_space_info.setStyleSheet("color: #22c55e;") 
                self.btn_select.setEnabled(True)
        except Exception:
            self.lbl_space_info.setText(f"Selected Size: {file_size_display} (Could not determine disk free space.)")
            self.btn_select.setEnabled(True)