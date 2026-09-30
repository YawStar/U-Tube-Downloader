# -*- coding: utf-8 -*-
import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QFrame
)
from PySide6.QtCore import Qt


class ModernUpdateDialog(QDialog):
    """ Custom Dark Theme ဖြင့် ပြုလုပ်ထားသော Update Dialog """
    
    def __init__(self, current_ver: str, latest_ver: str, release_notes: str, download_url: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        
        self.setWindowTitle("Update available!")
        self.setFixedSize(440, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # 1. Header (Title)
        lbl_title = QLabel("New version found")
        lbl_title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #ffffff;")
        layout.addWidget(lbl_title)
        
        # 2. Version Badges (v1.0.0.29 -> v1.0.0.30)
        version_layout = QHBoxLayout()
        version_layout.setSpacing(8)
        
        lbl_current = QLabel(f"v{current_ver.lstrip('v')}")
        lbl_current.setStyleSheet("""
            background-color: #27272a;
            color: #a1a1aa;
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 9pt;
            font-weight: bold;
        """)
        
        lbl_arrow = QLabel("➔")
        lbl_arrow.setStyleSheet("color: #71717a; font-size: 10pt;")
        
        lbl_latest = QLabel(f"v{latest_ver.lstrip('v')}")
        lbl_latest.setStyleSheet("""
            background-color: #064e3b;
            color: #34d399;
            border: 1px solid #059669;
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 9pt;
            font-weight: bold;
        """)
        
        version_layout.addWidget(lbl_current)
        version_layout.addWidget(lbl_arrow)
        version_layout.addWidget(lbl_latest)
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        # 3. Release Notes Section
        lbl_notes_hdr = QLabel("Release notes")
        lbl_notes_hdr.setStyleSheet("font-size: 10pt; color: #a1a1aa; font-weight: 500;")
        layout.addWidget(lbl_notes_hdr)
        
        self.txt_notes = QTextBrowser()
        self.txt_notes.setPlainText(release_notes)
        self.txt_notes.setStyleSheet("""
            QTextBrowser {
                background-color: #18181b;
                color: #d4d4d8;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 10px;
                font-size: 9.5pt;
                line-height: 1.4;
            }
            QScrollBar:vertical {
                background: #18181b;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3f3f46;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        layout.addWidget(self.txt_notes)
        
        # 4. Action Buttons (Later / Update now)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        btn_later = QPushButton("Later")
        btn_later.setCursor(Qt.PointingHandCursor)
        btn_later.setStyleSheet("""
            QPushButton {
                background-color: #27272a;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 7px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3f3f46;
            }
            QPushButton:pressed {
                background-color: #18181b;
            }
        """)
        btn_later.clicked.connect(self.reject)
        
        btn_update = QPushButton("Update now")
        btn_update.setCursor(Qt.PointingHandCursor)
        btn_update.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                border: 1px solid #10b981;
                border-radius: 6px;
                padding: 7px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
        """)
        btn_update.clicked.connect(self.on_update_now_clicked)
        
        btn_layout.addWidget(btn_later)
        btn_layout.addWidget(btn_update)
        layout.addLayout(btn_layout)
        
        # Window Background Style
        self.setStyleSheet("""
            QDialog {
                background-color: #09090b;
                color: #ffffff;
            }
        """)

    def on_update_now_clicked(self):
        """ Update Now နှိပ်ပါက Browser ဖြင့် Direct Download URL သို့ သွားရောက်ခြင်း """
        if self.download_url:
            webbrowser.open(self.download_url)
        self.accept()