# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainui_11GQVjRf.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QMetaObject, QSize, Qt)
from PySide6.QtGui import (QFont, QIcon,
    QDesktopServices)
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QVBoxLayout, QWidget, QTextBrowser)

# Resources file ကို import လုပ်
import assets.resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(850, 630)
        MainWindow.setMinimumSize(QSize(680, 630))
        font = QFont()
        font.setFamilies([u"Pyidaungsu"])
        font.setPointSize(12)
        MainWindow.setFont(font)
        app_icon = QIcon(":/icons/icons/app_icon.ico")
        MainWindow.setWindowIcon(app_icon)
        MainWindow.setStyleSheet(u"QMainWindow { background-color: #161616; }\n"
"QWidget { color: #ffffff; font-family: \"Pyidaungsu\"; font-size: 11pt; }\n"
"QLineEdit, QTextEdit { background-color: #111111; border: 1px solid #444444; border-radius: 2px; padding: 6px; color: #ffffff; }\n"
"QLineEdit:focus, QTextEdit:focus { border: 1px solid #ffffff; }\n"
"QPushButton { background-color: #ffffff; color: #161616; border: 1px solid #ffffff; border-radius: 4px; padding: 8px 16px; font-weight: bold; }\n"
"QPushButton:hover { background-color: #00A2FF; }\n"
"QPushButton:pressed { background-color: #cccccc; }\n"
"QPushButton:disabled { background-color: #555555; color: #888888; border: 1px solid #555555;}\n"
"QPushButton[selected=\"true\"] { background-color: #27AE60; }\n"
"QPushButton[selected=\"true\"]:hover { background-color: #1AD76A; }\n"
"QPushButton[selected=\"true\"]:pressed { background-color: #229954; }\n"
"QPushButton[selected=\"true\"]:disabled { background-color: #555555; color: #888888; border: 1px solid #555555; }\n"
"QPushButton[selected=\"true\"]:disabled { background-color: #555555; color: #888888; border: 1px solid #555555; }\n"
"QPushButton[working=\"true\"] { background-color: #FF3E00; color: #FFFFFF }\n"
"QPushButton[working=\"true\"]:hover { background-color: #FF4E00; color: #FFFFFF }\n"
"QPushButton[working=\"true\"]:pressed { background-color: #229954; color: #FFFFFF }\n"
"QProgressBar { border: 1px solid #444444; border-radius: 2px; text-align: center; background-color: #111111; color: #ffffff; font-weight: bold; }\n"
"QProgressBar::chunk { background-color: #00A2FF; }")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.mainVerticalLayout = QVBoxLayout(self.centralwidget)
        self.mainVerticalLayout.setSpacing(15)
        self.mainVerticalLayout.setObjectName(u"mainVerticalLayout")
        self.mainVerticalLayout.setContentsMargins(20, 20, 20, 10)
        self.topHorizontalLayout = QHBoxLayout()
        self.topHorizontalLayout.setSpacing(20)
        self.topHorizontalLayout.setObjectName(u"topHorizontalLayout")
        self.lblThumbnail = QLabel(self.centralwidget)
        self.lblThumbnail.setObjectName(u"lblThumbnail")
        self.lblThumbnail.setMinimumSize(QSize(340, 190))
        self.lblThumbnail.setMaximumSize(QSize(340, 190))
        self.lblThumbnail.setStyleSheet(u"border: 1px solid #888888; background-color: #222C36;")
        self.lblThumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.topHorizontalLayout.addWidget(self.lblThumbnail)

        self.metaVerticalLayout = QVBoxLayout()
        self.metaVerticalLayout.setSpacing(8)
        self.metaVerticalLayout.setObjectName(u"metaVerticalLayout")
        self.lblTitle = QLabel(self.centralwidget)
        self.lblTitle.setObjectName(u"lblTitle")
        font1 = QFont()
        font1.setFamilies([u"Pyidaungsu"])
        font1.setPointSize(14)
        font1.setBold(True)
        font1.setItalic(False)
        self.lblTitle.setFont(font1)
        self.lblTitle.setStyleSheet(u"font: 14pt \"Pyidaungsu\";\n"
"font-weight: bold;")
        self.lblTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblTitle.setWordWrap(True)

        self.metaVerticalLayout.addWidget(self.lblTitle)

        self.lineTop = QLabel(self.centralwidget)
        self.lineTop.setObjectName(u"lineTop")
        self.lineTop.setMaximumSize(QSize(16777215, 2))
        self.lineTop.setStyleSheet(u"background-color: #888888;")

        self.metaVerticalLayout.addWidget(self.lineTop)

        self.metadataGrid = QGridLayout()
        self.metadataGrid.setSpacing(10)
        self.metadataGrid.setObjectName(u"metadataGrid")
        self.lblDurationTag = QLabel(self.centralwidget)
        self.lblDurationTag.setObjectName(u"lblDurationTag")
        self.lblDurationTag.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.metadataGrid.addWidget(self.lblDurationTag, 0, 0, 1, 1)

        self.lblDurationVal = QLabel(self.centralwidget)
        self.lblDurationVal.setObjectName(u"lblDurationVal")

        self.metadataGrid.addWidget(self.lblDurationVal, 0, 1, 1, 1)

        self.lblChaptersTag = QLabel(self.centralwidget)
        self.lblChaptersTag.setObjectName(u"lblChaptersTag")
        self.lblChaptersTag.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.metadataGrid.addWidget(self.lblChaptersTag, 1, 0, 1, 1)

        self.lblChaptersVal = QLabel(self.centralwidget)
        self.lblChaptersVal.setObjectName(u"lblChaptersVal")

        self.metadataGrid.addWidget(self.lblChaptersVal, 1, 1, 1, 1)

        self.lblUploaderTag = QLabel(self.centralwidget)
        self.lblUploaderTag.setObjectName(u"lblUploaderTag")
        self.lblUploaderTag.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.metadataGrid.addWidget(self.lblUploaderTag, 2, 0, 1, 1)

        self.lblUploaderVal = QLabel(self.centralwidget)
        self.lblUploaderVal.setObjectName(u"lblUploaderVal")

        self.metadataGrid.addWidget(self.lblUploaderVal, 2, 1, 1, 1)

        self.lblUploadDateTag = QLabel(self.centralwidget)
        self.lblUploadDateTag.setObjectName(u"lblUploadDateTag")
        self.lblUploadDateTag.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.metadataGrid.addWidget(self.lblUploadDateTag, 3, 0, 1, 1)

        self.lblUploadDateVal = QLabel(self.centralwidget)
        self.lblUploadDateVal.setObjectName(u"lblUploadDateVal")

        self.metadataGrid.addWidget(self.lblUploadDateVal, 3, 1, 1, 1)


        self.metaVerticalLayout.addLayout(self.metadataGrid)

        self.lineBottom = QLabel(self.centralwidget)
        self.lineBottom.setObjectName(u"lineBottom")
        self.lineBottom.setMaximumSize(QSize(16777215, 2))
        self.lineBottom.setStyleSheet(u"background-color: #888888;")

        self.metaVerticalLayout.addWidget(self.lineBottom)


        self.topHorizontalLayout.addLayout(self.metaVerticalLayout)


        self.mainVerticalLayout.addLayout(self.topHorizontalLayout)

        self.urlLayout = QHBoxLayout()
        self.urlLayout.setSpacing(5)
        self.urlLayout.setObjectName(u"urlLayout")
        self.urlInput = QLineEdit(self.centralwidget)
        self.urlInput.setObjectName(u"urlInput")
        self.urlInput.setMinimumSize(QSize(0, 0))
        self.urlInput.setMaximumSize(QSize(16777215, 30))
        self.urlInput.setClearButtonEnabled(True)

        self.urlLayout.addWidget(self.urlInput)

        # History Button ထည့်သွင်းခြင်း
        self.historyButton = QPushButton(self.centralwidget)
        self.historyButton.setObjectName(u"historyButton")
        self.historyButton.setMinimumSize(QSize(30, 30))
        self.historyButton.setMaximumSize(QSize(30, 30))
        self.historyButton.setStyleSheet(u"QPushButton{\n"
"padding: 3px;\n"
"}")
        self.historyButton.setIcon(QIcon(":/icons/icons/history.ico"))
        self.historyButton.setIconSize(QSize(20, 20))

        self.urlLayout.addWidget(self.historyButton)

        self.pasteButton = QPushButton(self.centralwidget)
        self.pasteButton.setObjectName(u"pasteButton")
        self.pasteButton.setEnabled(True)
        self.pasteButton.setMinimumSize(QSize(70, 0))
        self.pasteButton.setMaximumSize(QSize(90, 30))
        self.pasteButton.setStyleSheet(u"QPushButton{\n"
"font-size: 10pt;\n"
"font-weight: bold;\n"
"padding-top: 5px;\n"
"padding-bottom: 5px;\n"
"padding-left: 5px;\n"
"padding-right: 5px;\n"
"}")
        self.pasteButton.setIcon(QIcon(":/images/images/paste.svg"))
        self.pasteButton.setIconSize(QSize(20, 20))

        self.urlLayout.addWidget(self.pasteButton)


        self.mainVerticalLayout.addLayout(self.urlLayout)

        self.optionLayout = QHBoxLayout()
        self.optionLayout.setSpacing(5)
        self.optionLayout.setObjectName(u"optionLayout")
        self.embThumbnailButton = QPushButton(self.centralwidget)
        self.embThumbnailButton.setObjectName(u"embThumbnailButton")
        self.embThumbnailButton.setMinimumSize(QSize(28, 28))
        self.embThumbnailButton.setMaximumSize(QSize(28, 28))
        self.embThumbnailButton.setStyleSheet(u"/* \u1015\u102f\u1036\u1019\u103e\u1014\u103a Off \u1016\u103c\u1005\u103a\u1014\u1031\u1001\u103b\u102d\u1014\u103a (\u101e\u102d\u102f\u1037) \u1019\u1014\u103e\u102d\u1015\u103a\u101b\u101e\u1031\u1038\u1001\u1004\u103a \u1021\u1001\u103c\u1031\u1021\u1014\u1031 */\n"
"QPushButton {\n"
"    background-color: #E0E0E0;\n"
"    color: black;\n"
"    border: 1px solid #A0A0A0;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"/* \u1014\u103e\u102d\u1015\u103a\u101c\u102d\u102f\u1000\u103a\u101c\u102d\u102f\u1037 On (Toggle / Checked) \u1016\u103c\u1005\u103a\u101e\u103d\u102c\u1038\u1001\u103b\u102d\u1014\u103a Background \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u1019\u100a\u1037\u103a\u1015\u102f\u1036\u1005\u1036 */\n"
"QPushButton:checked {\n"
"    background-color: #00A2FF; /* \u1005\u102d\u1019\u103a\u1038\u101b\u1031\u102c\u1004\u103a \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u101e\u103d\u102c\u1038\u1019\u100a\u103a */\n"
"    color: white;\n"
"    border: 1px solid #388E3C;\n"
"}")
        self.embThumbnailButton.setIcon(QIcon(":/images/images/thumbnail.svg"))
        self.embThumbnailButton.setIconSize(QSize(28, 28))
        self.embThumbnailButton.setCheckable(True)

        self.optionLayout.addWidget(self.embThumbnailButton)

        self.embSubtitlesButton = QPushButton(self.centralwidget)
        self.embSubtitlesButton.setObjectName(u"embSubtitlesButton")
        self.embSubtitlesButton.setMinimumSize(QSize(28, 28))
        self.embSubtitlesButton.setMaximumSize(QSize(28, 28))
        self.embSubtitlesButton.setStyleSheet(u"/* \u1015\u102f\u1036\u1019\u103e\u1014\u103a Off \u1016\u103c\u1005\u103a\u1014\u1031\u1001\u103b\u102d\u1014\u103a (\u101e\u102d\u102f\u1037) \u1019\u1014\u103e\u102d\u1015\u103a\u101b\u101e\u1031\u1038\u1001\u1004\u103a \u1021\u1001\u103c\u1031\u1021\u1014\u1031 */\n"
"QPushButton {\n"
"    background-color: #E0E0E0;\n"
"    color: black;\n"
"    border: 1px solid #A0A0A0;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"/* \u1014\u103e\u102d\u1015\u103a\u101c\u102d\u102f\u1000\u103a\u101c\u102d\u102f\u1037 On (Toggle / Checked) \u1016\u103c\u1005\u103a\u101e\u103d\u102c\u1038\u1001\u103b\u102d\u1014\u103a Background \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u1019\u100a\u1037\u103a\u1015\u102f\u1036\u1005\u1036 */\n"
"QPushButton:checked {\n"
"    background-color: #00A2FF; /* \u1005\u102d\u1019\u103a\u1038\u101b\u1031\u102c\u1004\u103a \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u101e\u103d\u102c\u1038\u1019\u100a\u103a */\n"
"    color: white;\n"
"    border: 1px solid #388E3C;\n"
"}")
        self.embSubtitlesButton.setIcon(QIcon(":/images/images/subtitles.svg"))
        self.embSubtitlesButton.setIconSize(QSize(22, 22))
        self.embSubtitlesButton.setCheckable(True)

        self.optionLayout.addWidget(self.embSubtitlesButton)

        self.embChaptersButton = QPushButton(self.centralwidget)
        self.embChaptersButton.setObjectName(u"embChaptersButton")
        self.embChaptersButton.setMinimumSize(QSize(28, 28))
        self.embChaptersButton.setMaximumSize(QSize(28, 28))
        self.embChaptersButton.setStyleSheet(u"/* \u1015\u102f\u1036\u1019\u103e\u1014\u103a Off \u1016\u103c\u1005\u103a\u1014\u1031\u1001\u103b\u102d\u1014\u103a (\u101e\u102d\u102f\u1037) \u1019\u1014\u103e\u102d\u1015\u103a\u101b\u101e\u1031\u1038\u1001\u1004\u103a \u1021\u1001\u103c\u1031\u1021\u1014\u1031 */\n"
"QPushButton {\n"
"    background-color: #E0E0E0;\n"
"    color: black;\n"
"    border: 1px solid #A0A0A0;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"/* \u1014\u103e\u102d\u1015\u103a\u101c\u102d\u102f\u1000\u103a\u101c\u102d\u102f\u1037 On (Toggle / Checked) \u1016\u103c\u1005\u103a\u101e\u103d\u102c\u1038\u1001\u103b\u102d\u1014\u103a Background \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u1019\u100a\u1037\u103a\u1015\u102f\u1036\u1005\u1036 */\n"
"QPushButton:checked {\n"
"    background-color: #00A2FF; /* \u1005\u102d\u1019\u103a\u1038\u101b\u1031\u102c\u1004\u103a \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u101e\u103d\u102c\u1038\u1019\u100a\u103a */\n"
"    color: white;\n"
"    border: 1px solid #388E3C;\n"
"}")
        self.embChaptersButton.setIcon(QIcon(":/images/images/chapters.svg"))
        self.embChaptersButton.setIconSize(QSize(28, 28))
        self.embChaptersButton.setCheckable(True)

        self.optionLayout.addWidget(self.embChaptersButton)

        self.embMetadataButton = QPushButton(self.centralwidget)
        self.embMetadataButton.setObjectName(u"embMetadataButton")
        self.embMetadataButton.setMinimumSize(QSize(28, 28))
        self.embMetadataButton.setMaximumSize(QSize(28, 28))
        self.embMetadataButton.setStyleSheet(u"/* \u1015\u102f\u1036\u1019\u103e\u1014\u103a Off \u1016\u103c\u1005\u103a\u1014\u1031\u1001\u103b\u102d\u1014\u103a (\u101e\u102d\u102f\u1037) \u1019\u1014\u103e\u102d\u1015\u103a\u101b\u101e\u1031\u1038\u1001\u1004\u103a \u1021\u1001\u103c\u1031\u1021\u1014\u1031 */\n"
"QPushButton {\n"
"    background-color: #E0E0E0;\n"
"    color: black;\n"
"    border: 1px solid #A0A0A0;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"/* \u1014\u103e\u102d\u1015\u103a\u101c\u102d\u102f\u1000\u103a\u101c\u102d\u102f\u1037 On (Toggle / Checked) \u1016\u103c\u1005\u103a\u101e\u103d\u102c\u1038\u1001\u103b\u102d\u1014\u103a Background \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u1019\u100a\u1037\u103a\u1015\u102f\u1036\u1005\u1036 */\n"
"QPushButton:checked {\n"
"    background-color: #00A2FF; /* \u1005\u102d\u1019\u103a\u1038\u101b\u1031\u102c\u1004\u103a \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u101e\u103d\u102c\u1038\u1019\u100a\u103a */\n"
"    color: white;\n"
"    border: 1px solid #388E3C;\n"
"}")
        self.embMetadataButton.setIcon(QIcon(":/images/images/metadata.svg"))
        self.embMetadataButton.setIconSize(QSize(25, 25))
        self.embMetadataButton.setCheckable(True)

        self.optionLayout.addWidget(self.embMetadataButton)

        self.useMTimeButton = QPushButton(self.centralwidget)
        self.useMTimeButton.setObjectName(u"useMTimeButton")
        self.useMTimeButton.setMinimumSize(QSize(28, 28))
        self.useMTimeButton.setMaximumSize(QSize(28, 28))
        font2 = QFont()
        font2.setFamilies([u"Pyidaungsu"])
        font2.setPointSize(12)
        font2.setBold(True)
        self.useMTimeButton.setFont(font2)
        self.useMTimeButton.setStyleSheet(u"/* \u1015\u102f\u1036\u1019\u103e\u1014\u103a Off \u1016\u103c\u1005\u103a\u1014\u1031\u1001\u103b\u102d\u1014\u103a (\u101e\u102d\u102f\u1037) \u1019\u1014\u103e\u102d\u1015\u103a\u101b\u101e\u1031\u1038\u1001\u1004\u103a \u1021\u1001\u103c\u1031\u1021\u1014\u1031 */\n"
"QPushButton {\n"
"    background-color: #E0E0E0;\n"
"    color: black;\n"
"    border: 1px solid #A0A0A0;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"/* \u1014\u103e\u102d\u1015\u103a\u101c\u102d\u102f\u1000\u103a\u101c\u102d\u102f\u1037 On (Toggle / Checked) \u1016\u103c\u1005\u103a\u101e\u103d\u102c\u1038\u1001\u103b\u102d\u1014\u103a Background \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u1019\u100a\u1037\u103a\u1015\u102f\u1036\u1005\u1036 */\n"
"QPushButton:checked {\n"
"    background-color: #00A2FF; /* \u1005\u102d\u1019\u103a\u1038\u101b\u1031\u102c\u1004\u103a \u1015\u103c\u1031\u102c\u1004\u103a\u1038\u101e\u103d\u102c\u1038\u1019\u100a\u103a */\n"
"    color: white;\n"
"    border: 1px solid #388E3C;\n"
"}")
        self.useMTimeButton.setIcon(QIcon(":/images/images/m_time.svg"))
        self.useMTimeButton.setIconSize(QSize(28, 28))
        self.useMTimeButton.setCheckable(True)
        self.useMTimeButton.setChecked(False)

        self.optionLayout.addWidget(self.useMTimeButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.optionLayout.addItem(self.horizontalSpacer)


        self.mainVerticalLayout.addLayout(self.optionLayout)

        self.txtInfoLog = QTextBrowser(self.centralwidget)
        # self.txtInfoLog = QTextEdit(self.centralwidget)
        self.txtInfoLog.setObjectName(u"txtInfoLog")
        font3 = QFont()
        font3.setFamilies([u"Pyidaungsu"])
        font3.setPointSize(10)
        font3.setBold(False)
        font3.setItalic(False)
        self.txtInfoLog.setFont(font3)
        self.txtInfoLog.setStyleSheet(u"font: 10pt \"Pyidaungsu\";")
        self.txtInfoLog.setReadOnly(True)
        # --- Link Click ပြဿနာ ဖြေရှင်းရန် ကုဒ်အပိုင်းအစ ---
        self.txtInfoLog.setTextInteractionFlags(
        Qt.TextInteractionFlag.LinksAccessibleByMouse | 
        Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.txtInfoLog.setOpenLinks(False) # လက်ရှိ widget ထဲမှာပဲ အလုပ်လုပ်တာကို override လုပ်ဖို့
        self.txtInfoLog.anchorClicked.connect(QDesktopServices.openUrl)
        # -----------------------------------------------

        self.mainVerticalLayout.addWidget(self.txtInfoLog)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(8)
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.getInfoButton = QPushButton(self.centralwidget)
        self.getInfoButton.setObjectName(u"getInfoButton")
        self.getInfoButton.setCheckable(True)
        self.getInfoButton.setStyleSheet(u"QPushButton{\n"
"font-size: 10pt;\n"
"font-weight: bold;\n"
"padding-top: 5px;\n"
"padding-bottom: 5px;\n"
"padding-left: 5px;\n"
"padding-right: 5px;\n"
"}")
        self.getInfoButton.setIcon(QIcon(":/images/images/fetch_Info.svg"))
        self.getInfoButton.setIconSize(QSize(20, 20))

        self.buttonLayout.addWidget(self.getInfoButton)

        self.selectFormatsButton = QPushButton(self.centralwidget)
        self.selectFormatsButton.setObjectName(u"selectFormatsButton")
        self.selectFormatsButton.setStyleSheet(u"QPushButton{\n"
"font-size: 10pt;\n"
"font-weight: bold;\n"
"padding-top: 5px;\n"
"padding-bottom: 5px;\n"
"padding-left: 5px;\n"
"padding-right: 5px;\n"
"}")
        self.selectFormatsButton.setIcon(QIcon(":/images/images/formats.svg"))
        self.selectFormatsButton.setIconSize(QSize(23, 23))

        self.buttonLayout.addWidget(self.selectFormatsButton)

        self.settingsButton = QPushButton(self.centralwidget)
        self.settingsButton.setObjectName(u"settingsButton")
        self.settingsButton.setStyleSheet(u"QPushButton{\n"
"font-size: 10pt;\n"
"font-weight: bold;\n"
"padding-top: 5px;\n"
"padding-bottom: 5px;\n"
"padding-left: 5px;\n"
"padding-right: 5px;\n"
"}")
        self.settingsButton.setIcon(QIcon(":/images/images/settings.svg"))
        self.settingsButton.setIconSize(QSize(23, 23))

        self.buttonLayout.addWidget(self.settingsButton)

        self.openFolderButton = QPushButton(self.centralwidget)
        self.openFolderButton.setObjectName(u"openFolderButton")
        self.openFolderButton.setStyleSheet(u"QPushButton{\n"
"font-size: 10pt;\n"
"font-weight: bold;\n"
"padding-top: 5px;\n"
"padding-bottom: 5px;\n"
"padding-left: 5px;\n"
"padding-right: 5px;\n"
"}")
        self.openFolderButton.setIcon(QIcon(":/images/images/open_folder.svg"))
        self.openFolderButton.setIconSize(QSize(23, 23))

        self.buttonLayout.addWidget(self.openFolderButton)

        self.downloadButton = QPushButton(self.centralwidget)
        self.downloadButton.setObjectName(u"downloadButton")
        self.downloadButton.setCheckable(True)
        self.downloadButton.setStyleSheet(u"QPushButton{\n"
"font-size: 10pt;\n"
"font-weight: bold;\n"
"padding-top: 5px;\n"
"padding-bottom: 5px;\n"
"padding-left: 5px;\n"
"padding-right: 5px;\n"
"}")
        self.downloadButton.setIcon(QIcon(":/images/images/download.svg"))
        self.downloadButton.setIconSize(QSize(23, 23))

        self.buttonLayout.addWidget(self.downloadButton)

        self.aboutButton = QPushButton(self.centralwidget)
        self.aboutButton.setObjectName(u"aboutButton")
        self.aboutButton.setStyleSheet(u"QPushButton{\n"
"font-size: 10pt;\n"
"font-weight: bold;\n"
"padding-top: 5px;\n"
"padding-bottom: 5px;\n"
"padding-left: 5px;\n"
"padding-right: 5px;\n"
"}")
        self.aboutButton.setIcon(QIcon(":/images/images/about.svg"))
        self.aboutButton.setIconSize(QSize(23, 23))

        self.buttonLayout.addWidget(self.aboutButton)


        self.mainVerticalLayout.addLayout(self.buttonLayout)

        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setEnabled(True)
        self.progressBar.setMinimumSize(QSize(0, 20))
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.mainVerticalLayout.addWidget(self.progressBar)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"YawStar U-Tube Dowloader - 1.0.0.8", None))
        self.lblThumbnail.setText(QCoreApplication.translate("MainWindow", u"[ Video Thumbnail ]", None))
        self.lblTitle.setText("")
        self.lineTop.setText("")
        self.lblDurationTag.setText(QCoreApplication.translate("MainWindow", u"Duration:", None))
        self.lblDurationVal.setText("")
        self.lblChaptersTag.setText(QCoreApplication.translate("MainWindow", u"Chapters:", None))
        self.lblChaptersVal.setText("")
        self.lblUploaderTag.setText(QCoreApplication.translate("MainWindow", u"Uploader:", None))
        self.lblUploaderVal.setText("")
        self.lblUploadDateTag.setText(QCoreApplication.translate("MainWindow", u"Upload date:", None))
        self.lblUploadDateVal.setText("")
        self.lineBottom.setText("")
        self.urlInput.setText("")
        self.urlInput.setStyleSheet(u"font: 10pt \"Segoe UI\";")
        # self.urlInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"https://www.youtube.com/watch?v=...", None))
        self.urlInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter video URL ...", None))
#if QT_CONFIG(tooltip)
        self.historyButton.setToolTip(QCoreApplication.translate("MainWindow", u"History", None))
#endif // QT_CONFIG(tooltip)
        self.historyButton.setText("")
        self.pasteButton.setText(QCoreApplication.translate("MainWindow", u"Paste", None))
#if QT_CONFIG(tooltip)
        self.embThumbnailButton.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:400; font-style:italic;\">Embedded Thumbnail</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.embThumbnailButton.setText("")
#if QT_CONFIG(tooltip)
        self.embSubtitlesButton.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:400; font-style:italic;\">Embedded Subtitle</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.embSubtitlesButton.setText("")
#if QT_CONFIG(tooltip)
        self.embChaptersButton.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:400; font-style:italic;\">Embedded Chapters</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.embChaptersButton.setText("")
#if QT_CONFIG(tooltip)
        self.embMetadataButton.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:400; font-style:italic;\">Embedded Metadata</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.embMetadataButton.setText("")
#if QT_CONFIG(tooltip)
        self.useMTimeButton.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:400; font-style:italic;\">Modification time</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.useMTimeButton.setText("")
        self.txtInfoLog.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Pyidaungsu'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Pyidaungsu'; font-size:12pt;\"><br /></p></body></html>", None))
        self.getInfoButton.setText(QCoreApplication.translate("MainWindow", u"Fetch Info", None))
        self.selectFormatsButton.setText(QCoreApplication.translate("MainWindow", u"Formats", None))
        self.settingsButton.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.openFolderButton.setText(QCoreApplication.translate("MainWindow", u"Open Folder", None))
        self.downloadButton.setText(QCoreApplication.translate("MainWindow", u"Download", None))
        self.aboutButton.setText(QCoreApplication.translate("MainWindow", u"About", None))
    # retranslateUi