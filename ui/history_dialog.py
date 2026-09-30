# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'history_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from assets import resources_rc

class Ui_HistoryDialog(object):
    def setupUi(self, HistoryDialog):
        if not HistoryDialog.objectName():
            HistoryDialog.setObjectName(u"HistoryDialog")
        HistoryDialog.resize(500, 400)
        HistoryDialog.setMinimumSize(QSize(450, 350))
        icon = QIcon()
        icon.addFile(u":/icons/icons/history.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        HistoryDialog.setWindowIcon(icon)
        HistoryDialog.setStyleSheet(u"QDialog { background-color: #161616; }\n"
"QWidget { color: #ffffff; font-family: \"Pyidaungsu\"; font-size: 10pt; }\n"
"QLineEdit { background-color: #111111; border: 1px solid #444444; border-radius: 4px; padding: 6px; color: #ffffff; }\n"
"QLineEdit:focus { border: 1px solid #00A2FF; }\n"
"QListWidget { background-color: #111111; border: 1px solid #444444; border-radius: 4px; padding: 5px; color: #ffffff; }\n"
"QListWidget::item { padding: 6px; border-bottom: 1px solid #222222; }\n"
"QListWidget::item:hover { background-color: #222C36; }\n"
"QListWidget::item:selected { background-color: #00A2FF; color: #ffffff; }\n"
"QPushButton { background-color: #ffffff; color: #161616; border: 1px solid #ffffff; border-radius: 4px; padding: 6px 14px; font-weight: bold; }\n"
"QPushButton:hover { background-color: #00A2FF; color: #ffffff; border: 1px solid #00A2FF; }\n"
"QPushButton:pressed { background-color: #cccccc; }\n"
"QPushButton#btnClearHistory { background-color: #D34507; color: #ffffff; border: 1px solid #D3450"
                        "7; }\n"
"QPushButton#btnClearHistory:hover { background-color: #FF4E00; border: 1px solid #FF4E00; }")
        self.verticalLayout = QVBoxLayout(HistoryDialog)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(15, 15, 15, 15)
        self.searchLayout = QHBoxLayout()
        self.searchLayout.setObjectName(u"searchLayout")
        self.txtSearch = QLineEdit(HistoryDialog)
        self.txtSearch.setObjectName(u"txtSearch")
        self.txtSearch.setClearButtonEnabled(True)

        self.searchLayout.addWidget(self.txtSearch)


        self.verticalLayout.addLayout(self.searchLayout)

        self.listHistory = QListWidget(HistoryDialog)
        self.listHistory.setObjectName(u"listHistory")

        self.verticalLayout.addWidget(self.listHistory)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(8)
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.btnClearHistory = QPushButton(HistoryDialog)
        self.btnClearHistory.setObjectName(u"btnClearHistory")

        self.buttonLayout.addWidget(self.btnClearHistory)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.horizontalSpacer)

        self.btnSelect = QPushButton(HistoryDialog)
        self.btnSelect.setObjectName(u"btnSelect")

        self.buttonLayout.addWidget(self.btnSelect)

        self.btnCancel = QPushButton(HistoryDialog)
        self.btnCancel.setObjectName(u"btnCancel")

        self.buttonLayout.addWidget(self.btnCancel)


        self.verticalLayout.addLayout(self.buttonLayout)


        self.retranslateUi(HistoryDialog)

        QMetaObject.connectSlotsByName(HistoryDialog)
    # setupUi

    def retranslateUi(self, HistoryDialog):
        HistoryDialog.setWindowTitle(QCoreApplication.translate("HistoryDialog", u"URL History", None))
        self.txtSearch.setPlaceholderText(QCoreApplication.translate("HistoryDialog", u"Search history...", None))
        self.btnClearHistory.setText(QCoreApplication.translate("HistoryDialog", u"Clear History", None))
        self.btnSelect.setText(QCoreApplication.translate("HistoryDialog", u"Select", None))
        self.btnCancel.setText(QCoreApplication.translate("HistoryDialog", u"Cancel", None))
    # retranslateUi

