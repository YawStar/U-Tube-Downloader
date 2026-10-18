# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'depDuqyQhO.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QHBoxLayout,
    QLabel, QMainWindow, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QStackedWidget, QVBoxLayout,
    QWidget)
# import resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(620, 449)
        MainWindow.setMinimumSize(QSize(620, 449))
        MainWindow.setMaximumSize(QSize(620, 449))
        MainWindow.setStyleSheet(u"\n"
"    QMainWindow {\n"
"        background-color: #0b0f19;\n"
"    }\n"
"    QWidget {\n"
"        color: #ffffff;\n"
"        font-family: 'Segoe UI', sans-serif;\n"
"    }\n"
"    /* Main Card / Container */\n"
"    #centralWidget {\n"
"        background-color: #121824;\n"
"        border: 1px solid #1e293b;\n"
"        border-radius: 8px;\n"
"    }\n"
"    /* Item Cards */\n"
"    QFrame.itemCard {\n"
"        background-color: #171f30;\n"
"        border: 1px solid #222e45;\n"
"        border-radius: 8px;\n"
"    }\n"
"    /* Labels */\n"
"    QLabel {\n"
"        color: #f8fafc;\n"
"        background: transparent;\n"
"    }\n"
"    .titleLabel {\n"
"        font-size: 16px;\n"
"        font-weight: bold;\n"
"    }\n"
"    .statusLabel {\n"
"        font-size: 13px;\n"
"        color: #94a3b8;\n"
"    }\n"
"    /* Default Buttons */\n"
"    QPushButton {\n"
"        background-color: #1e293b;\n"
"        border: 1px solid #334155;\n"
"        border-radius: 6px;\n"
"        padding: 6px 12px;\n"
"    "
                        "    color: #ffffff;\n"
"        font-weight: 500;\n"
"    }\n"
"    QPushButton:hover {\n"
"        background-color: #273548;\n"
"    }\n"
"    /* Primary / Download Buttons */\n"
"    QPushButton#btnFfmpegDownload, QPushButton#btnDenoDownload, QPushButton#btnYtDlpDownload, QPushButton#downloadAllButton {\n"
"        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1d4ed8, stop:1 #1e40af);\n"
"        border: 1px solid #3b82f6;\n"
"        border-radius: 6px;\n"
"        font-weight: bold;\n"
"    }\n"
"    QPushButton#btnFfmpegDownload:hover, QPushButton#btnDenoDownload:hover, QPushButton#btnYtDlpDownload:hover, QPushButton#downloadAllButton:hover {\n"
"        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);\n"
"    }\n"
"    /* Pause \u1014\u103e\u1004\u1037\u103a Cancel \u1001\u101c\u102f\u1010\u103a\u1019\u103b\u102c\u1038 */\n"
"    QPushButton[objectName*=\"Pause\"], QPushButton[objectName*=\"Cancel\"] {\n"
"        background-color: #1e293b;\n"
""
                        "        border: 1px solid #334155;\n"
"        border-radius: 6px;\n"
"        padding: 6px 12px;\n"
"        color: #f8fafc;\n"
"        font-weight: 500;\n"
"        min-height: 24px;\n"
"    }\n"
"    QPushButton[objectName*=\"Pause\"]:hover, QPushButton[objectName*=\"Cancel\"]:hover {\n"
"        background-color: #334155;\n"
"        border-color: #475569;\n"
"    }\n"
"    /* Progress Bar */\n"
"    QProgressBar {\n"
"        background-color: #0f172a;\n"
"        border: none;\n"
"        border-radius: 4px;\n"
"        height: 6px;\n"
"        text-align: center;\n"
"    }\n"
"    QProgressBar::chunk {\n"
"        background-color: #3b82f6;\n"
"        border-radius: 4px;\n"
"    }\n"
"   ")
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.mainLayout = QVBoxLayout(self.centralWidget)
        self.mainLayout.setSpacing(16)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.frameYtDlp = QFrame(self.centralWidget)
        self.frameYtDlp.setObjectName(u"frameYtDlp")
        self.verticalLayoutYtDlp = QVBoxLayout(self.frameYtDlp)
        self.verticalLayoutYtDlp.setSpacing(10)
        self.verticalLayoutYtDlp.setObjectName(u"verticalLayoutYtDlp")
        self.horizontalLayoutYtDlpTop = QHBoxLayout()
        self.horizontalLayoutYtDlpTop.setObjectName(u"horizontalLayoutYtDlpTop")
        self.layoutLeftYtDlp = QHBoxLayout()
        self.layoutLeftYtDlp.setSpacing(12)
        self.layoutLeftYtDlp.setObjectName(u"layoutLeftYtDlp")
        self.btnIconYtDlp = QPushButton(self.frameYtDlp)
        self.btnIconYtDlp.setObjectName(u"btnIconYtDlp")
        self.btnIconYtDlp.setMinimumSize(QSize(32, 32))
        self.btnIconYtDlp.setMaximumSize(QSize(32, 32))
        icon = QIcon()
        icon.addFile(u":/images/images/yt-dlp.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnIconYtDlp.setIcon(icon)
        self.btnIconYtDlp.setIconSize(QSize(25, 25))

        self.layoutLeftYtDlp.addWidget(self.btnIconYtDlp)

        self.layoutTextYtDlp = QVBoxLayout()
        self.layoutTextYtDlp.setObjectName(u"layoutTextYtDlp")
        self.labelYtDlpTitle = QLabel(self.frameYtDlp)
        self.labelYtDlpTitle.setObjectName(u"labelYtDlpTitle")

        self.layoutTextYtDlp.addWidget(self.labelYtDlpTitle)

        self.labelYtDlpStatus = QLabel(self.frameYtDlp)
        self.labelYtDlpStatus.setObjectName(u"labelYtDlpStatus")

        self.layoutTextYtDlp.addWidget(self.labelYtDlpStatus)


        self.layoutLeftYtDlp.addLayout(self.layoutTextYtDlp)


        self.horizontalLayoutYtDlpTop.addLayout(self.layoutLeftYtDlp)

        self.horizontalSpacer_3 = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutYtDlpTop.addItem(self.horizontalSpacer_3)

        self.stackedYtDlp = QStackedWidget(self.frameYtDlp)
        self.stackedYtDlp.setObjectName(u"stackedYtDlp")
        self.stackedYtDlp.setMinimumSize(QSize(0, 40))
        self.stackedYtDlp.setMaximumSize(QSize(120, 40))
        self.pageYtDlpReady = QWidget()
        self.pageYtDlpReady.setObjectName(u"pageYtDlpReady")
        self.layoutYtDlpReady = QHBoxLayout(self.pageYtDlpReady)
        self.layoutYtDlpReady.setObjectName(u"layoutYtDlpReady")
        self.layoutYtDlpReady.setContentsMargins(0, 0, 0, 0)
        self.btnYtDlpDownload = QPushButton(self.pageYtDlpReady)
        self.btnYtDlpDownload.setObjectName(u"btnYtDlpDownload")
        self.btnYtDlpDownload.setMinimumSize(QSize(110, 35))

        self.layoutYtDlpReady.addWidget(self.btnYtDlpDownload)

        self.stackedYtDlp.addWidget(self.pageYtDlpReady)
        self.pageYtDlpDownloading = QWidget()
        self.pageYtDlpDownloading.setObjectName(u"pageYtDlpDownloading")
        self.layoutYtDlpDownloading = QHBoxLayout(self.pageYtDlpDownloading)
        self.layoutYtDlpDownloading.setObjectName(u"layoutYtDlpDownloading")
        self.layoutYtDlpDownloading.setContentsMargins(0, 0, 0, 0)
        self.btnYtDlpCancel = QPushButton(self.pageYtDlpDownloading)
        self.btnYtDlpCancel.setObjectName(u"btnYtDlpCancel")
        self.btnYtDlpCancel.setMinimumSize(QSize(110, 38))
        self.btnYtDlpCancel.setMaximumSize(QSize(16777215, 16777215))

        self.layoutYtDlpDownloading.addWidget(self.btnYtDlpCancel)

        self.stackedYtDlp.addWidget(self.pageYtDlpDownloading)

        self.horizontalLayoutYtDlpTop.addWidget(self.stackedYtDlp)


        self.verticalLayoutYtDlp.addLayout(self.horizontalLayoutYtDlpTop)

        self.progressBarYtDlp = QProgressBar(self.frameYtDlp)
        self.progressBarYtDlp.setObjectName(u"progressBarYtDlp")
        self.progressBarYtDlp.setMaximumSize(QSize(16777215, 5))
        self.progressBarYtDlp.setValue(0)
        self.progressBarYtDlp.setTextVisible(False)

        self.verticalLayoutYtDlp.addWidget(self.progressBarYtDlp)


        self.mainLayout.addWidget(self.frameYtDlp)

        self.frameFfmpeg = QFrame(self.centralWidget)
        self.frameFfmpeg.setObjectName(u"frameFfmpeg")
        self.verticalLayoutFfmpeg = QVBoxLayout(self.frameFfmpeg)
        self.verticalLayoutFfmpeg.setSpacing(10)
        self.verticalLayoutFfmpeg.setObjectName(u"verticalLayoutFfmpeg")
        self.horizontalLayoutFfmpegTop = QHBoxLayout()
        self.horizontalLayoutFfmpegTop.setObjectName(u"horizontalLayoutFfmpegTop")
        self.layoutTitleFfmpeg = QHBoxLayout()
        self.layoutTitleFfmpeg.setSpacing(12)
        self.layoutTitleFfmpeg.setObjectName(u"layoutTitleFfmpeg")
        self.btnIconFfmpeg = QPushButton(self.frameFfmpeg)
        self.btnIconFfmpeg.setObjectName(u"btnIconFfmpeg")
        self.btnIconFfmpeg.setMinimumSize(QSize(32, 32))
        self.btnIconFfmpeg.setMaximumSize(QSize(32, 32))
        icon1 = QIcon()
        icon1.addFile(u":/images/images/ffmpeg.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnIconFfmpeg.setIcon(icon1)
        self.btnIconFfmpeg.setIconSize(QSize(32, 32))

        self.layoutTitleFfmpeg.addWidget(self.btnIconFfmpeg)

        self.layoutTextFfmpeg = QVBoxLayout()
        self.layoutTextFfmpeg.setObjectName(u"layoutTextFfmpeg")
        self.labelFfmpegTitle = QLabel(self.frameFfmpeg)
        self.labelFfmpegTitle.setObjectName(u"labelFfmpegTitle")

        self.layoutTextFfmpeg.addWidget(self.labelFfmpegTitle)

        self.labelFfmpegStatus = QLabel(self.frameFfmpeg)
        self.labelFfmpegStatus.setObjectName(u"labelFfmpegStatus")

        self.layoutTextFfmpeg.addWidget(self.labelFfmpegStatus)


        self.layoutTitleFfmpeg.addLayout(self.layoutTextFfmpeg)


        self.horizontalLayoutFfmpegTop.addLayout(self.layoutTitleFfmpeg)

        self.horizontalSpacer_4 = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutFfmpegTop.addItem(self.horizontalSpacer_4)

        self.stackedFfmpeg = QStackedWidget(self.frameFfmpeg)
        self.stackedFfmpeg.setObjectName(u"stackedFfmpeg")
        self.stackedFfmpeg.setMaximumSize(QSize(120, 40))
        self.pageFfmpegReady = QWidget()
        self.pageFfmpegReady.setObjectName(u"pageFfmpegReady")
        self.layoutFfmpegReady = QHBoxLayout(self.pageFfmpegReady)
        self.layoutFfmpegReady.setObjectName(u"layoutFfmpegReady")
        self.layoutFfmpegReady.setContentsMargins(0, 0, 0, 0)
        self.btnFfmpegDownload = QPushButton(self.pageFfmpegReady)
        self.btnFfmpegDownload.setObjectName(u"btnFfmpegDownload")
        self.btnFfmpegDownload.setMinimumSize(QSize(110, 35))
        self.btnFfmpegDownload.setMaximumSize(QSize(16777215, 16777215))

        self.layoutFfmpegReady.addWidget(self.btnFfmpegDownload)

        self.stackedFfmpeg.addWidget(self.pageFfmpegReady)
        self.pageFfmpegDownloading = QWidget()
        self.pageFfmpegDownloading.setObjectName(u"pageFfmpegDownloading")
        self.layoutFfmpegDownloading = QHBoxLayout(self.pageFfmpegDownloading)
        self.layoutFfmpegDownloading.setObjectName(u"layoutFfmpegDownloading")
        self.layoutFfmpegDownloading.setContentsMargins(0, 0, 0, 0)
        self.btnFfmpegCancel = QPushButton(self.pageFfmpegDownloading)
        self.btnFfmpegCancel.setObjectName(u"btnFfmpegCancel")
        self.btnFfmpegCancel.setMinimumSize(QSize(110, 38))
        self.btnFfmpegCancel.setMaximumSize(QSize(16777215, 16777215))

        self.layoutFfmpegDownloading.addWidget(self.btnFfmpegCancel)

        self.stackedFfmpeg.addWidget(self.pageFfmpegDownloading)

        self.horizontalLayoutFfmpegTop.addWidget(self.stackedFfmpeg)


        self.verticalLayoutFfmpeg.addLayout(self.horizontalLayoutFfmpegTop)

        self.progressBarFfmpeg = QProgressBar(self.frameFfmpeg)
        self.progressBarFfmpeg.setObjectName(u"progressBarFfmpeg")
        self.progressBarFfmpeg.setMaximumSize(QSize(16777215, 5))
        self.progressBarFfmpeg.setValue(0)
        self.progressBarFfmpeg.setTextVisible(False)

        self.verticalLayoutFfmpeg.addWidget(self.progressBarFfmpeg)


        self.mainLayout.addWidget(self.frameFfmpeg)

        self.frameDeno = QFrame(self.centralWidget)
        self.frameDeno.setObjectName(u"frameDeno")
        self.verticalLayoutDeno = QVBoxLayout(self.frameDeno)
        self.verticalLayoutDeno.setSpacing(10)
        self.verticalLayoutDeno.setObjectName(u"verticalLayoutDeno")
        self.horizontalLayoutDenoTop = QHBoxLayout()
        self.horizontalLayoutDenoTop.setObjectName(u"horizontalLayoutDenoTop")
        self.layoutLeftDeno = QHBoxLayout()
        self.layoutLeftDeno.setSpacing(12)
        self.layoutLeftDeno.setObjectName(u"layoutLeftDeno")
        self.btnIconDeno = QPushButton(self.frameDeno)
        self.btnIconDeno.setObjectName(u"btnIconDeno")
        self.btnIconDeno.setMinimumSize(QSize(32, 32))
        self.btnIconDeno.setMaximumSize(QSize(32, 32))
        icon2 = QIcon()
        icon2.addFile(u":/images/images/deno-light.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnIconDeno.setIcon(icon2)
        self.btnIconDeno.setIconSize(QSize(32, 32))

        self.layoutLeftDeno.addWidget(self.btnIconDeno)

        self.layoutTextDeno = QVBoxLayout()
        self.layoutTextDeno.setObjectName(u"layoutTextDeno")
        self.labelDenoTitle = QLabel(self.frameDeno)
        self.labelDenoTitle.setObjectName(u"labelDenoTitle")

        self.layoutTextDeno.addWidget(self.labelDenoTitle)

        self.labelDenoStatus = QLabel(self.frameDeno)
        self.labelDenoStatus.setObjectName(u"labelDenoStatus")

        self.layoutTextDeno.addWidget(self.labelDenoStatus)


        self.layoutLeftDeno.addLayout(self.layoutTextDeno)


        self.horizontalLayoutDenoTop.addLayout(self.layoutLeftDeno)

        self.horizontalSpacer_2 = QSpacerItem(100, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutDenoTop.addItem(self.horizontalSpacer_2)

        self.stackedDeno = QStackedWidget(self.frameDeno)
        self.stackedDeno.setObjectName(u"stackedDeno")
        self.stackedDeno.setMaximumSize(QSize(120, 40))
        self.pageDenoReady = QWidget()
        self.pageDenoReady.setObjectName(u"pageDenoReady")
        self.layoutDenoReady = QHBoxLayout(self.pageDenoReady)
        self.layoutDenoReady.setObjectName(u"layoutDenoReady")
        self.layoutDenoReady.setContentsMargins(0, 0, 0, 0)
        self.btnDenoDownload = QPushButton(self.pageDenoReady)
        self.btnDenoDownload.setObjectName(u"btnDenoDownload")
        self.btnDenoDownload.setMinimumSize(QSize(110, 34))

        self.layoutDenoReady.addWidget(self.btnDenoDownload)

        self.stackedDeno.addWidget(self.pageDenoReady)
        self.pageDenoDownloading = QWidget()
        self.pageDenoDownloading.setObjectName(u"pageDenoDownloading")
        self.layoutDenoDownloading = QHBoxLayout(self.pageDenoDownloading)
        self.layoutDenoDownloading.setObjectName(u"layoutDenoDownloading")
        self.layoutDenoDownloading.setContentsMargins(0, 0, 0, 0)
        self.btnDenoCancel = QPushButton(self.pageDenoDownloading)
        self.btnDenoCancel.setObjectName(u"btnDenoCancel")
        self.btnDenoCancel.setMinimumSize(QSize(110, 38))
        self.btnDenoCancel.setMaximumSize(QSize(16777215, 16777215))

        self.layoutDenoDownloading.addWidget(self.btnDenoCancel)

        self.stackedDeno.addWidget(self.pageDenoDownloading)

        self.horizontalLayoutDenoTop.addWidget(self.stackedDeno)


        self.verticalLayoutDeno.addLayout(self.horizontalLayoutDenoTop)

        self.progressBarDeno = QProgressBar(self.frameDeno)
        self.progressBarDeno.setObjectName(u"progressBarDeno")
        self.progressBarDeno.setMaximumSize(QSize(16777215, 5))
        self.progressBarDeno.setValue(0)
        self.progressBarDeno.setTextVisible(False)

        self.verticalLayoutDeno.addWidget(self.progressBarDeno)


        self.mainLayout.addWidget(self.frameDeno)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_5)

        self.downloadAllButton = QPushButton(self.centralWidget)
        self.downloadAllButton.setObjectName(u"downloadAllButton")
        self.downloadAllButton.setMinimumSize(QSize(180, 40))
        self.downloadAllButton.setMaximumSize(QSize(180, 40))
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setBold(True)
        self.downloadAllButton.setFont(font)

        self.horizontalLayout.addWidget(self.downloadAllButton)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_6)


        self.mainLayout.addLayout(self.horizontalLayout)

        self.verticalSpacerBottom = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.mainLayout.addItem(self.verticalSpacerBottom)

        self.footerLayout = QHBoxLayout()
        self.footerLayout.setObjectName(u"footerLayout")
        self.footerLeft = QHBoxLayout()
        self.footerLeft.setSpacing(6)
        self.footerLeft.setObjectName(u"footerLeft")
        self.chk_skip_existing = QCheckBox(self.centralWidget)
        self.chk_skip_existing.setObjectName(u"chk_skip_existing")
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        font1.setPointSize(10)
        self.chk_skip_existing.setFont(font1)

        self.footerLeft.addWidget(self.chk_skip_existing)


        self.footerLayout.addLayout(self.footerLeft)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footerLayout.addItem(self.horizontalSpacer)

        self.btnSettings = QPushButton(self.centralWidget)
        self.btnSettings.setObjectName(u"btnSettings")

        self.footerLayout.addWidget(self.btnSettings)


        self.mainLayout.addLayout(self.footerLayout)

        MainWindow.setCentralWidget(self.centralWidget)

        self.retranslateUi(MainWindow)

        self.stackedYtDlp.setCurrentIndex(0)
        self.stackedFfmpeg.setCurrentIndex(0)
        self.stackedDeno.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Dependencies Downloader", None))
        self.frameYtDlp.setProperty(u"class", QCoreApplication.translate("MainWindow", u"itemCard", None))
        self.btnIconYtDlp.setText("")
        self.labelYtDlpTitle.setText(QCoreApplication.translate("MainWindow", u"yt-dlp", None))
        self.labelYtDlpTitle.setProperty(u"class", QCoreApplication.translate("MainWindow", u"titleLabel", None))
        self.labelYtDlpStatus.setText(QCoreApplication.translate("MainWindow", u"Status: Ready to Download", None))
        self.labelYtDlpStatus.setProperty(u"class", QCoreApplication.translate("MainWindow", u"statusLabel", None))
        self.btnYtDlpDownload.setText(QCoreApplication.translate("MainWindow", u"Download", None))
        self.btnYtDlpCancel.setText(QCoreApplication.translate("MainWindow", u"\u274c Cancel", None))
        self.frameFfmpeg.setProperty(u"class", QCoreApplication.translate("MainWindow", u"itemCard", None))
        self.btnIconFfmpeg.setText("")
        self.labelFfmpegTitle.setText(QCoreApplication.translate("MainWindow", u"FFmpeg", None))
        self.labelFfmpegTitle.setProperty(u"class", QCoreApplication.translate("MainWindow", u"titleLabel", None))
        self.labelFfmpegStatus.setText(QCoreApplication.translate("MainWindow", u"Status: Ready to Download", None))
        self.labelFfmpegStatus.setProperty(u"class", QCoreApplication.translate("MainWindow", u"statusLabel", None))
        self.btnFfmpegDownload.setText(QCoreApplication.translate("MainWindow", u"Download", None))
        self.btnFfmpegCancel.setText(QCoreApplication.translate("MainWindow", u"\u274c Cancel", None))
        self.frameDeno.setProperty(u"class", QCoreApplication.translate("MainWindow", u"itemCard", None))
        self.btnIconDeno.setText("")
        self.labelDenoTitle.setText(QCoreApplication.translate("MainWindow", u"Deno", None))
        self.labelDenoTitle.setProperty(u"class", QCoreApplication.translate("MainWindow", u"titleLabel", None))
        self.labelDenoStatus.setText(QCoreApplication.translate("MainWindow", u"Status: Ready to Download", None))
        self.labelDenoStatus.setProperty(u"class", QCoreApplication.translate("MainWindow", u"statusLabel", None))
        self.btnDenoDownload.setText(QCoreApplication.translate("MainWindow", u"Download", None))
        self.btnDenoCancel.setText(QCoreApplication.translate("MainWindow", u"\u274c Cancel", None))
        self.downloadAllButton.setText(QCoreApplication.translate("MainWindow", u"Download All", None))
        self.chk_skip_existing.setText(QCoreApplication.translate("MainWindow", u"Skip already downloaded / existing files", None))
        self.btnSettings.setText(QCoreApplication.translate("MainWindow", u"\u2699 Settings", None))
    # retranslateUi

