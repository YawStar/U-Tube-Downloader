
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, 
    QLabel, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QCursor, QPixmap, QIcon, QDesktopServices

# CONSTANTS
import core.global_constants as CONST

class ActionCard(QFrame):
    """ညာဘက်ခြမ်းရှိ Icon Image, Title, Subtitle ပါသော Card များအတွက် Widget"""
    def __init__(self, icon_path, title, subtitle, url="", on_click=None, tooltip_text="", parent=None):
        super().__init__(parent)
        self.url = url  # Link URL သိမ်းဆည်းရန်
        self.on_click = on_click  # 👈 Custom Callback Function သိမ်းရန်
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Hover လုပ်လျှင် စာသားပေါ်လာစေရန် Tooltip သတ်မှတ်ခြင်း
        if tooltip_text:
            self.setToolTip(tooltip_text)
            
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # SVG/PNG Icon Image Label
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("border: none; background: transparent;")
        
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
        
        layout.addWidget(icon_label, alignment=Qt.AlignVCenter)

        # Text Layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF; border: none; background: transparent;")
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size: 11px; color: #A0A0B0; border: none; background: transparent;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        layout.addLayout(text_layout)
        layout.addStretch()

    def mousePressEvent(self, event):
        """Card ကို နှိပ်လိုက်ပါက Callback သို့မဟုတ် URL သို့ ပို့ပေးခြင်း"""
        if event.button() == Qt.LeftButton:
            if self.on_click:
                self.on_click()  # custom function/method ထားရှိပါက ခေါ်ပေး
            elif self.url:
                QDesktopServices.openUrl(QUrl(self.url))
        super().mousePressEvent(event)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        info_icon_path = ":/icons/icons/info.ico"
        self.setWindowIcon(QIcon(info_icon_path))
        self.setFixedSize(600, 280)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #12161F;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QToolTip {
                background-color: #1E222D;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 16)
        main_layout.setSpacing(30)

        # ==================== 1. ဘယ်ဘက် Panel ====================
        left_panel = QVBoxLayout()
        left_panel.setSpacing(0)

        logo_header_layout = QVBoxLayout()
        logo_header_layout.setSpacing(8)

        logo_box = QLabel()
        logo_box.setFixedSize(90, 90)
        logo_box.setAlignment(Qt.AlignCenter)
        
        icon_path = ":/icons/icons/app_icon.ico"
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_box.setPixmap(scaled_pixmap)

        logo_box.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E1A3C, stop:1 #1E1A3C);
                border: 1px solid #2092D8;
                border-radius: 20px;
            }
        """)

        app_name = QLabel("YawStar U-Tube Downloader")
        app_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")

        logo_header_layout.addWidget(logo_box, alignment=Qt.AlignHCenter)
        logo_header_layout.addWidget(app_name, alignment=Qt.AlignHCenter)

        app_version = QLabel(f"Version {CONST.APP_VERSION} (64-bit)")
        app_version.setStyleSheet("font-size: 12px; color: #7E8294;")

        app_released_date = QLabel(f"Released date {CONST.APP_RELEASED_DATE}")
        app_released_date.setStyleSheet("font-size: 12px; color: #7E8294;")

        dev_label = QLabel("Developed by YawHackka")
        dev_label.setStyleSheet("font-size: 13px; color: #9E9EB0;")

        donate_btn = QPushButton(" Donate")
        donate_btn.setIcon(QIcon(":/images/images/heart_pink.svg"))
        donate_btn.setCursor(QCursor(Qt.PointingHandCursor))
        donate_btn.setFixedSize(140, 32)
        donate_btn.setToolTip("Support the development of this project")
        donate_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 90, 121, 0.1);
                color: #FF5A79;
                border: 1px solid rgba(255, 90, 121, 0.3);
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 90, 121, 0.2);
                border: 1px solid #FF5A79;
            }
        """)

        donate_btn.clicked.connect(self.open_donate_link)

        left_panel.addLayout(logo_header_layout)
        left_panel.addWidget(app_version, alignment=Qt.AlignHCenter)
        left_panel.addWidget(app_released_date, alignment=Qt.AlignHCenter)
        left_panel.addSpacing(22)
        left_panel.addWidget(dev_label, alignment=Qt.AlignHCenter)
        left_panel.addSpacing(3)
        left_panel.addWidget(donate_btn, alignment=Qt.AlignHCenter)
        left_panel.addStretch()

        # ==================== 2. ညာဘက် Panel ====================
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        card1_icon = ":/images/images/github.svg"
        card2_icon = ":/images/images/license.svg"
        card3_icon = ":/images/images/qt_dark.svg"

        card1 = ActionCard(
            card1_icon, "This is a free & Open Source", "See the Source Code", 
            url=CONST.GITHUB_REPO_URL, 
            tooltip_text="Open GitHub Repository"
        )
        card2 = ActionCard(
            card2_icon, "Open Source License", "View the Open-Source licenses", 
            url="https://github.com/YawStar/U-Tube-Downloader/blob/main/LICENSE", 
            tooltip_text="View Third-party Licenses"
        )
        
        # card3 တွင် url အစား on_click ကိုသုံးပြီး QMessageBox.aboutQt ခေါ်ပြ
        card3 = ActionCard(
            card3_icon, "Powered with Qt Framework", "Designed with using Qt", 
            on_click=self.show_about_qt,
            tooltip_text="About Qt Framework"
        )

        right_panel.addWidget(card1)
        right_panel.addWidget(card2)
        right_panel.addWidget(card3)
        right_panel.addStretch()

        # အောက်ခြေ Icon Bar
        bottom_icons_layout = QHBoxLayout()
        bottom_icons_layout.setSpacing(10)
        bottom_icons_layout.addStretch()

        bottom_icon_data = [
            (":/images/images/globe.svg", CONST.YS_BLOG_URL, "Official Website"),
            (":/images/images/mail.svg", "mailto:yawstar.2009@gmail.com", "Contact via Email"),
            (":/images/images/github.svg", CONST.GITHUB_PROFILE_URL, "GitHub Profile"),
            (":/images/images/groups.svg", CONST.TELEGRAM_URL, "Telegram Community"),
            (":/images/images/bug_report.svg", CONST.GITHUB_REPO_URL, "Bugs Report!"),
        ]

        for icon_path, link, tooltip in bottom_icon_data:
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setToolTip(tooltip)
            
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(18, 18))

            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.08);
                }
            """)

            btn.clicked.connect(lambda checked=False, url=link: self.open_link(url))
            bottom_icons_layout.addWidget(btn)

        bottom_icons_layout.addStretch()
        right_panel.addLayout(bottom_icons_layout)

        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=3)

    # ==================== Methods ====================
    def show_about_qt(self):
        """Qt Framework အကြောင်း MessageBox ပေါ်စေမည့် Method"""
        QMessageBox.aboutQt(self, "About Qt")

    def open_donate_link(self):
        """Donate ခလုတ်နှိပ်ပါက ပွင့်မည့် Link"""
        QDesktopServices.openUrl(QUrl(CONST.DONATE_URL))

    def open_link(self, url: str):
        """အထွေထွေ URL များ ပွင့်စေရန် Method"""
        if url:
            QDesktopServices.openUrl(QUrl(url))