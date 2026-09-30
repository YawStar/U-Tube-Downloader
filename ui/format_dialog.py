import os
import shutil
from PySide6.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QAbstractItemView, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class FormatDialog(QDialog):
    """ Available Formats Window (High to Low Sort + HD/FHD/UHD Labels) """

    def __init__(self, json_data, current_format_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Available Formats")
        self.resize(1000, 580)
        
        self.raw_info = json_data
        self.parent_win = parent
        self.parsed_formats = []
        self.current_filter = "Default"

        self.saved_format_id = str(current_format_id) if current_format_id is not None else None

        if parent and hasattr(parent, 'styleSheet'):
            self.setStyleSheet(parent.styleSheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # -------------------------------------------------------------
        # Segmented Control (All / Video Only / Audio Only)
        # -------------------------------------------------------------
        filter_container_layout = QHBoxLayout()

        self.segmented_frame = QFrame()
        self.segmented_frame.setObjectName("SegmentedControl")
        
        segmented_layout = QHBoxLayout(self.segmented_frame)
        segmented_layout.setContentsMargins(2, 2, 2, 2)
        segmented_layout.setSpacing(0)

        self.btn_filter_default = QPushButton("Default")
        self.btn_filter_video = QPushButton("Video Only")
        self.btn_filter_audio = QPushButton("Audio Only")
        
        self.btn_filter_default.setObjectName("btn_default")
        self.btn_filter_video.setObjectName("btn_video")
        self.btn_filter_audio.setObjectName("btn_audio")

        for btn in [self.btn_filter_default, self.btn_filter_video, self.btn_filter_audio]:
            btn.setCheckable(True)
            btn.setMinimumHeight(30)
            btn.setMinimumWidth(100)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
            segmented_layout.addWidget(btn)

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
            QPushButton:checked {
                background-color: #2ecc71;
                color: #000000;
                font-weight: bold;
                border-radius: 6px;
            }
        """)

        filter_container_layout.addWidget(self.segmented_frame)
        filter_container_layout.addStretch()
        layout.addLayout(filter_container_layout)

        # -------------------------------------------------------------
        # QTableWidget Setup
        # -------------------------------------------------------------
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(10)
        self.tableWidget.setHorizontalHeaderLabels([
            "Select", "Quality", "Extension", "Resolution", "File Size", "Codec", "Audio", "Language", "FPS", "HDR"
        ])
        
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setAlternatingRowColors(True)
        
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.tableWidget.setColumnWidth(5, 140)

        layout.addWidget(self.tableWidget)

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
        # Bottom Controls & Actions
        # -------------------------------------------------------------
        bottom_layout = QHBoxLayout()
        
        self.lbl_space_info = QLabel("Select a format to check disk space...")
        self.lbl_space_info.setStyleSheet("font-weight: bold;")
        bottom_layout.addWidget(self.lbl_space_info)
        bottom_layout.addStretch()
        
        self.btn_clear_select = QPushButton("Select None")
        self.btn_select = QPushButton("Select Format")
        self.btn_cancel = QPushButton("Cancel")

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

        if parent and hasattr(parent, 'styleSheet'):
            self.setStyleSheet(parent.styleSheet())

        self.setStyleSheet(self.styleSheet() + """
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
            }
        """)
        
        # -------------------------------------------------------------
        # Signals Connecting
        # -------------------------------------------------------------
        self.btn_clear_select.clicked.connect(self.clear_and_accept)
        self.btn_select.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.tableWidget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tableWidget.itemClicked.connect(self.on_item_clicked)
        
        self.btn_filter_default.clicked.connect(lambda: self.change_filter("Default"))
        self.btn_filter_video.clicked.connect(lambda: self.change_filter("Video Only"))
        self.btn_filter_audio.clicked.connect(lambda: self.change_filter("Audio Only"))
        
        self.tableWidget.itemChanged.connect(self.on_item_changed)

        self.prepare_data()
        self.change_filter("Default")

    def on_item_clicked(self, item):
        self.tableWidget.blockSignals(True)
        clicked_row = item.row()
        
        if self.current_filter == "Audio Only":
            current_state = self.tableWidget.item(clicked_row, 0).checkState()
            new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
            self.tableWidget.item(clicked_row, 0).setCheckState(new_state)
        else:
            for row in range(self.tableWidget.rowCount()):
                row_item = self.tableWidget.item(row, 0)
                if row_item:
                    if row == clicked_row:
                        row_item.setCheckState(Qt.CheckState.Checked)
                    else:
                        row_item.setCheckState(Qt.CheckState.Unchecked)
                    
        self.tableWidget.blockSignals(False)
        self.check_disk_space_status()

    def on_item_double_clicked(self, item):
        if self.current_filter in ["Video Only", "Audio Only", "Default"]:
            row = item.row()
            id_item = self.tableWidget.item(row, 0)
            if id_item:
                id_item.setCheckState(Qt.CheckState.Checked)
            
            self.check_disk_space_status()
            self.accept()

    def on_item_changed(self, item):
        if item.column() == 0:
            self.check_disk_space_status()

    def change_filter(self, filter_type):
        current_active_ids = self.get_selected_format_id()
        if current_active_ids:
            self.saved_format_id = current_active_ids

        self.current_filter = filter_type
        
        self.btn_filter_default.setChecked(filter_type == "Default")
        self.btn_filter_video.setChecked(filter_type == "Video Only")
        self.btn_filter_audio.setChecked(filter_type == "Audio Only")
        
        if filter_type == "Audio Only":
            self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        else:
            self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.refresh_table_view()

    def prepare_data(self):
        if not self.raw_info: return
        formats_list = self.raw_info.get('formats', [])

        def format_size_str(bytes_size):
            if not bytes_size: return "N/A"
            bytes_size = float(bytes_size)
            for unit in ['Bytes', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0: return f"{bytes_size:.2f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.2f} TB"

        self.parsed_formats.clear()

        extractor = str(self.raw_info.get('extractor_key', '')).lower()
        is_youtube = 'youtube' in extractor

        for f in formats_list:
            if f.get('format_note') == 'storyboard' or f.get('ext') == 'm4e': 
                continue

            vcodec = str(f.get('vcodec', 'none'))
            acodec = str(f.get('acodec', 'none'))
            
            has_video = vcodec != 'none' and vcodec != 'None' and bool(vcodec)
            has_audio = acodec != 'none' and acodec != 'None' and bool(acodec)

            # Non-YouTube sites များတွင် Codec တန်ဖိုး မပါလာလျှင်လည်း format အဖြစ် အသိအမှတ်ပြု
            if not is_youtube and not has_video and not has_audio:
                if f.get('video_ext') != 'none' or f.get('resolution') or f.get('height') or f.get('format_id'):
                    has_video = True

            if is_youtube and not has_video and not has_audio:
                continue

            filesize = f.get('filesize') or f.get('filesize_approx') or 0
            height = f.get('height') or 0
            fps = f.get('fps') or 0
            abr = f.get('abr') or 0
            
            # Custom Quality Labels
            if height >= 4320:  # 8K
                k_val = round(height * (16 / 9) / 1000)
                quality_str = f"FUHD ({k_val}K)"
            elif height >= 2160: # 4K
                quality_str = "UHD (4K)"
            elif height >= 1440: # 2K
                quality_str = "FHD (2K)"
            elif height >= 1080: # 1080p
                quality_str = f"HD ({height}p)"
            elif height >= 720:  # 720p
                quality_str = f"HD ({height}p)"
            elif height >= 480:  # 480p
                quality_str = f"SD ({height}p)"
            elif height > 0:
                quality_str = f"Low ({height}p)"
            else:
                quality_str = str(f.get('format_note') or f.get('format_id') or 'Standard')

            if has_video and has_audio:
                codec_str = f"{vcodec} / {acodec}"
            elif has_video and vcodec != 'none':
                codec_str = vcodec
            elif has_audio and acodec != 'none':
                codec_str = acodec
            else:
                codec_str = f.get('ext', 'N/A').upper()
            
            res_str = f.get('resolution', 'N/A')
            if not has_video and is_youtube: res_str = "N/A"

            if has_video and has_audio:
                media_type = "Video + Audio"
            elif has_video:
                media_type = "Video Only" if is_youtube else "Video"
            elif has_audio:
                media_type = "Audio Only"
            else:
                media_type = "Standard"

            dynamic_range = f.get('dynamic_range', 'SDR')
            hdr_str = dynamic_range if dynamic_range and dynamic_range != 'SDR' else "SDR"

            self.parsed_formats.append({
                "format_id": str(f.get('format_id', 'N/A')),
                "quality": quality_str,
                "extension": f.get('ext', 'N/A').upper(),
                "resolution": res_str,
                "height": height, 
                "raw_size": filesize, 
                "file_size_str": format_size_str(filesize),
                "codec": codec_str,
                "type": media_type,
                "has_audio": has_audio,
                "has_video": has_video,
                "language": f.get('language') or "N/A",
                "raw_fps": int(fps) if fps else 0,
                "fps": f"{int(fps)}fps" if fps else "N/A",
                "hdr": hdr_str,
                "abr": abr
            })

        # High to Low Sort
        self.parsed_formats.sort(
            key=lambda x: (x['height'], x['raw_fps'], x['abr'], x['raw_size']), 
            reverse=True
        )

    def refresh_table_view(self):
        self.tableWidget.blockSignals(True)

        extractor = str(self.raw_info.get('extractor_key', '')).lower()
        is_youtube = 'youtube' in extractor

        filtered_list = []
        for f in self.parsed_formats:
            if not is_youtube:
                # Non-YouTube များအတွက် ရသမျှ Formats အကုန်လုံးကို ပြသ
                filtered_list.append(f)
            else:
                if self.current_filter == "Default":
                    if f['has_video']: 
                        filtered_list.append(f)
                elif self.current_filter == "Video Only":
                    if f['type'] == "Video Only": 
                        filtered_list.append(f)
                elif self.current_filter == "Audio Only":
                    if f['type'] == "Audio Only": 
                        filtered_list.append(f)

        self.tableWidget.setRowCount(len(filtered_list))
        
        saved_ids = [s.split('+')[0] for s in self.saved_format_id.split("+")] if self.saved_format_id else []

        for row, item_info in enumerate(filtered_list):
            item_id = QTableWidgetItem("")
            item_id.setFlags(item_id.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            if item_info['format_id'] in saved_ids:
                item_id.setCheckState(Qt.CheckState.Checked)
            else:
                item_id.setCheckState(Qt.CheckState.Unchecked)

            item_quality = QTableWidgetItem(item_info['quality'])
            item_ext = QTableWidgetItem(item_info['extension'])
            item_res = QTableWidgetItem(item_info['resolution'])
            item_size = QTableWidgetItem(item_info['file_size_str'])
            item_codec = QTableWidgetItem(item_info['codec'])
            
            if item_info['type'] in ["Video + Audio", "Video", "Standard"]:
                audio_text = "✓ Native" if not is_youtube else "✓ Has Audio"
                audio_color = QColor("#22c55e")
            elif item_info['type'] == "Video Only":
                if self.current_filter == "Default":
                    audio_text = "Auto"
                    audio_color = QColor("#f59e0b")
                else:
                    audio_text = "No Audio"
                    audio_color = QColor("#ef4444")
            else:
                audio_text = "Audio Track"
                audio_color = QColor("#3b82f6")

            item_audio = QTableWidgetItem(audio_text)
            item_lang = QTableWidgetItem(item_info['language'])
            item_fps = QTableWidgetItem(item_info['fps'])
            item_hdr = QTableWidgetItem(item_info['hdr'])

            # Colors & Styling based on Quality
            if item_info['height'] >= 1080:
                item_quality.setForeground(QColor("#2ecc71"))
            elif item_info['height'] >= 720:
                item_quality.setForeground(QColor("#3b82f6"))
            else:
                item_quality.setForeground(QColor("#f59e0b"))

            item_audio.setForeground(audio_color)
            
            if item_info['raw_fps'] >= 50:
                item_fps.setForeground(QColor("#22c55e"))
            elif item_info['raw_fps'] > 0:
                item_fps.setForeground(QColor("#f59e0b"))

            if item_info['hdr'] != "SDR":
                item_hdr.setForeground(QColor("#22c55e"))
            else:
                item_hdr.setForeground(QColor("#94a3b8"))

            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ext.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_res.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_codec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_audio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_lang.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_fps.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_hdr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_id.setData(Qt.ItemDataRole.UserRole, item_info)

            items = [item_id, item_quality, item_ext, item_res, item_size, item_codec, item_audio, item_lang, item_fps, item_hdr]
            for col, item in enumerate(items):
                self.tableWidget.setItem(row, col, item)

            if item_info['format_id'] in saved_ids:
                self.tableWidget.selectRow(row)

        self.tableWidget.blockSignals(False)
        self.check_disk_space_status()

    def check_disk_space_status(self):
        checked_rows_info = []
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                item_info = item.data(Qt.ItemDataRole.UserRole)
                if item_info:
                    checked_rows_info.append(item_info)

        if not checked_rows_info:
            self.lbl_space_info.setText("Select a format to check disk space...")
            self.lbl_space_info.setStyleSheet("color: #ffffff;")
            self.btn_select.setEnabled(False)
            return

        total_file_bytes = sum([f['raw_size'] for f in checked_rows_info])
        download_dir = "./"
        
        if self.parent_win and hasattr(self.parent_win, 'downloadFolderInput'):
            potential_dir = self.parent_win.downloadFolderInput.text().strip()
            if os.path.exists(potential_dir):
                download_dir = potential_dir

        try:
            total, used, free_bytes = shutil.disk_usage(os.path.abspath(download_dir))
            
            def dynamic_format_size(bytes_size):
                if not bytes_size: return "0 Bytes"
                bytes_size = float(bytes_size)
                for unit in ['Bytes', 'KB', 'MB', 'GB']:
                    if bytes_size < 1024.0: return f"{bytes_size:.2f} {unit}"
                    bytes_size /= 1024.0
                return f"{bytes_size:.2f} TB"

            file_size_display = dynamic_format_size(total_file_bytes)
            free_gb_display = f"{free_bytes / (1024**3):.2f} GB"

            if total_file_bytes == 0:
                self.lbl_space_info.setText(f"Drive Space: {free_gb_display} Free (Format size is approximate/unspecified).")
                self.lbl_space_info.setStyleSheet("color: #00A2FF;") 
                self.btn_select.setEnabled(True)
            elif free_bytes < (total_file_bytes * 1.2):
                self.lbl_space_info.setText(f"⚠️ Insufficient Space! Required: {file_size_display} | Free: {free_gb_display}")
                self.lbl_space_info.setStyleSheet("color: #ff3333; font-weight: bold;") 
                self.btn_select.setEnabled(True) 
            else:
                self.lbl_space_info.setText(f"✅ Space Available. File Size: {file_size_display} | Free Space: {free_gb_display}")
                self.lbl_space_info.setStyleSheet("color: #22c55e;") 
                self.btn_select.setEnabled(True)
        except Exception:
            self.lbl_space_info.setText("Could not determine disk free space.")
            self.btn_select.setEnabled(True)
    
    def get_selected_format_id(self):
        checked_ids = []
        extractor = str(self.raw_info.get('extractor_key', '')).lower() if self.raw_info else ''
        is_youtube = 'youtube' in extractor

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                item_info = item.data(Qt.ItemDataRole.UserRole)
                if item_info:
                    f_id = item_info['format_id']
                    if is_youtube and self.current_filter == "Default" and item_info['type'] == "Video Only":
                        checked_ids.append(f"{f_id}+bestaudio")
                    else:
                        checked_ids.append(f_id)
                
        if checked_ids:
            return "+".join(checked_ids)
        return None
    
    def clear_and_accept(self):
        self.tableWidget.blockSignals(True)
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.tableWidget.blockSignals(False)
        self.accept()