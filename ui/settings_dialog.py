# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QButtonGroup, QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QStandardPaths


class SettingsDialog(QDialog):
    """ ConfigManager ကို အသုံးပြု၍ App ဆက်တင်များအားလုံးကို RAM ပေါ်မှတစ်ဆင့် 
    မြန်ဆန်ချောမွေ့စွာ ဖတ်ခြင်း၊ ရေးခြင်း၊ Default ချခြင်းများ ပြုလုပ်ပေးမည့် Dialog Class """
    
    def __init__(self, config_mgr, parent=None, initial_tab=0):
        super().__init__(parent)
        self.config_mgr = config_mgr

        # App Data Dir ကို သတ်မှတ်
        APP_DATA_DIR = os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))

        # Application CACH Dir ကို သတ်မှတ်
        APP_CACHE_DIR = os.path.join(APP_DATA_DIR, "Cache")

        # Manual Cookies Path ကို self နဲ့ သတ်မှတ်ပါ (instance variable)
        self.manual_cookies_path = os.path.join(APP_CACHE_DIR, "manual_cookies.txt")
        
        # 1. Dynamic UI Loading
        loader = QUiLoader()
        ui_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings_dialog.ui")
        ui_file = QFile(ui_file_path)
        
        if not ui_file.open(QFile.ReadOnly):
            self.show_custom_message("critical", "Error", f"Cannot open {ui_file_path}")
            return
            
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        # သတ်မှတ်ထားသော Tab သို့ တိုက်ရိုက် ရောက်ရှိစေခြင်း
        if hasattr(self.ui, 'tabWidget'):
            if isinstance(initial_tab, int):
                self.ui.tabWidget.setCurrentIndex(initial_tab)
            elif isinstance(initial_tab, str):
                for i in range(self.ui.tabWidget.count()):
                    if self.ui.tabWidget.tabText(i).lower() == initial_tab.lower():
                        self.ui.tabWidget.setCurrentIndex(i)
                        break
        
        self.setWindowTitle("Settings")
        # self.setFixedSize(680, 520)
        self.setFixedSize(680, 680)
        
        if self.ui.layout():
            self.setLayout(self.ui.layout())
        
        # UI ထဲမှ Loaded ဖြစ်ပြီးသား Bottom Buttons များကို Object Name သတ်မှတ်ခြင်း
        if hasattr(self.ui, 'btn_save'):
            self.ui.btn_save.setObjectName("btn_pref_action")
        if hasattr(self.ui, 'btn_cancel'):
            self.ui.btn_cancel.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_restore'):
            self.ui.btn_restore.setObjectName("btn_pref_def_restore")

        # Inner Buttons များကို Object Name သတ်မှတ်ခြင်း
        if hasattr(self.ui, 'btn_check_update'):
            self.ui.btn_check_update.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_get_cookie_ext'):
            self.ui.btn_get_cookie_ext.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_clear_cookies'):
            self.ui.btn_clear_cookies.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_reset_output_template'):
            self.ui.btn_reset_output_template.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_reset_playlist_indexing'):
            self.ui.btn_reset_playlist_indexing.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_BrowsePath'):
            self.ui.btn_BrowsePath.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_browse_cookies'):
            self.ui.btn_browse_cookies.setObjectName("btn_pref_browse")
        if hasattr(self.ui, 'btn_paste_clipboard'):
            self.ui.btn_paste_clipboard.setObjectName("btn_pref_secondary")
        if hasattr(self.ui, 'btn_save_manual'):
            self.ui.btn_save_manual.setObjectName("btn_pref_secondary") #btn_pref_accent

        # 2. Dynamic Style Sheet Override
        self.setStyleSheet("""
            QDialog {
                background-color: #161616;
                color: #ffffff;
            }
            
            /* Primary Action Button (Save Changes) */
            QPushButton#btn_pref_action {
                background-color: #2563eb !important;
                color: #ffffff !important;
                border: 1px solid #3b82f6 !important;
                border-radius: 6px !important;
                padding: 5px 15px !important;
                font-weight: bold !important;
            }
            QPushButton#btn_pref_action:hover {
                background-color: #1d4ed8 !important;
            }
            QPushButton#btn_pref_action:pressed {
                background-color: #1e40af !important;
            }
            QPushButton#btn_pref_action:disabled {
                background-color: #334155 !important;
                color: #64748b !important;
                border: 1px solid #475569 !important;
            }

            /* Secondary Dark Buttons (Cancel & Restore Defaults) */
            QPushButton#btn_pref_secondary {
                background-color: #1e293b !important;
                color: #f8fafc !important;
                border: 1px solid #475569 !important;
                border-radius: 6px !important;
                padding: 5px 15px !important;
                font-weight: normal !important;
            }
            QPushButton#btn_pref_secondary:hover {
                background-color: #334155 !important;
                border-color: #64748b !important;
            }
            QPushButton#btn_pref_secondary:pressed {
                background-color: #0f172a !important;
            }

            /* Inner Auxiliary & Browse Buttons */
            QPushButton#btn_pref_browse {
                background-color: #1e293b !important;
                color: #ffffff !important;
                border: 1px solid #475569 !important;
                border-radius: 6px !important;
                padding: 4px 12px !important;
                font-size: 9pt !important;
            }
            QPushButton#btn_pref_browse:hover {
                background-color: #334155 !important;
                border-color: #64748b !important;
            }
            QPushButton#btn_pref_browse:pressed {
                background-color: #0f172a !important;
            }

            /* Restore Defaults Buttons */
            QPushButton#btn_pref_def_restore {
                background-color: #2c1517 !important;
                color: #f87171 !important;
                border: 1px solid #7f1d1d !important;
                border-radius: 6px !important;
                padding: 4px 12px !important;
                font-size: normal !important;
            }
            QPushButton#btn_pref_def_restore:hover {
            background-color: #450a0a !important;
            color: #fca5a5 !important;
            border-color: #991b1b !important;
            }
            QPushButton#btn_pref_def_restore:pressed {
                background-color: #0f172a !important;
            }

            /* Cookie Manual Save Button */
            QPushButton#btn_pref_accent {
                background-color: #16a34a !important;
                color: #ffffff !important;
                border: 1px solid #22c55e !important;
                border-radius: 6px !important;
                padding: 4px 12px !important;
                font-weight: bold !important;
            }
            QPushButton#btn_pref_accent:hover {
                background-color: #15803d !important;
            }
            QPushButton#btn_pref_accent:pressed {
                background-color: #166534 !important;
            }

            /* Cookie Segmented Toggle Buttons */
            QPushButton#btnNone, QPushButton#btnManual, QPushButton#btnCookieFile, QPushButton#btnFromBrowser {
                background-color: #1e1e24 !important;
                color: #ffffff !important;
                border: 1px solid #333333 !important;
                padding: 6px 12px !important;
                font-size: 9.5pt !important;
            }
            QPushButton#btnNone {
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                border-right: none !important;
            }
            QPushButton#btnFromBrowser {
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QPushButton#btnNone:checked, QPushButton#btnManual:checked, QPushButton#btnCookieFile:checked, QPushButton#btnFromBrowser:checked {
                background-color: #4ade80 !important;
                color: #111111 !important;
                border: 1px solid #4ade80 !important;
                font-weight: bold;
            }
            QPushButton#btnNone:hover:not(:checked), QPushButton#btnManual:hover:not(:checked), QPushButton#btnCookieFile:hover:not(:checked), QPushButton#btnFromBrowser:hover:not(:checked) {
                background-color: #2d2d35 !important;
            }
        """)

        # Cookie Button Group Setup & Signals Connection
        self.cookie_button_group = QButtonGroup(self)
        self.cookie_button_group.addButton(self.ui.btnNone, 0)
        self.cookie_button_group.addButton(self.ui.btnManual, 1)
        self.cookie_button_group.addButton(self.ui.btnCookieFile, 2)
        self.cookie_button_group.addButton(self.ui.btnFromBrowser, 3)
        self.cookie_button_group.setExclusive(True)
        self.cookie_button_group.idClicked.connect(self.on_cookie_mode_changed)

        # Combo Box ထဲသို့ Browser စာရင်းများ ထည့်သွင်း
        if hasattr(self.ui, 'combo_browser'):
            self.ui.combo_browser.clear()
            self.ui.combo_browser.addItems([
                "Chrome", "Edge", "Firefox", "Brave", "Opera", "Vivaldi", "Chromium", "Whale"
            ])

        # Signals & Slots connections
        self.ui.btn_BrowsePath.clicked.connect(self.on_browse_clicked)
        self.ui.btn_save.clicked.connect(self.on_save_clicked)
        self.ui.btn_cancel.clicked.connect(self.reject)
        self.ui.btn_restore.clicked.connect(self.on_restore_defaults_clicked)
        
        if hasattr(self.ui, 'btn_browse_cookies'):
            self.ui.btn_browse_cookies.clicked.connect(self.on_browse_cookies_clicked)
        if hasattr(self.ui, 'btn_paste_clipboard'):
            self.ui.btn_paste_clipboard.clicked.connect(self.on_paste_clipboard_clicked)
        if hasattr(self.ui, 'btn_save_manual'):
            self.ui.btn_save_manual.clicked.connect(self.on_save_cookies_data_clicked)
        
        # Load Settings Into UI
        self.load_settings_into_ui()

    def apply_msgbox_style(self, msg_box):
        """ QMessageBox ၏ Dark Theme Style နှင့် Buttons စတိုင်လ်များကို သတ်မှတ်ပေးခြင်း """
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #161616;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 9.5pt;
            }
            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 18px;
                min-width: 70px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #64748b;
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
        """)

    def show_custom_message(self, msg_type, title, text):
        """ Styled QMessageBox ဖန်တီး၍ ပြသပေးသော Helper Function """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        if msg_type == "info":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif msg_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif msg_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)
            
        self.apply_msgbox_style(msg_box)
        msg_box.exec()

    def on_cookie_mode_changed(self, button_id):
        """ ခလုတ်နှိပ်လိုက်သည့် မုဒ် (None, Manual, File, Browser) အလိုက် Container များကို အပိတ်အဖွင့် လုပ်ပေးခြင်း """
        if hasattr(self.ui, 'container_manual'):
            self.ui.container_manual.setVisible(button_id == 1)
        if hasattr(self.ui, 'container_cookie_file'):
            self.ui.container_cookie_file.setVisible(button_id == 2)
        if hasattr(self.ui, 'container_browser'):
            self.ui.container_browser.setVisible(button_id == 3)

    def on_paste_clipboard_clicked(self):
        """ Clipboard ထဲမှ စာများကို TextEdit ထဲ သို့ Paste လုပ်ပေးခြင်း """
        clipboard = QApplication.clipboard()
        if hasattr(self.ui, 'txt_manual_cookie'):
            self.ui.txt_manual_cookie.setText(clipboard.text())

    def on_save_cookies_data_clicked(self):
        """Cookies အချက်အလက်များကို manual_cookies.txt ထဲသို့သိမ်း"""
        try:
            cache_dir = os.path.dirname(self.manual_cookies_path)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            
            # UI ထဲက data ကို ယူခြင်း
            cookie_data = self.ui.txt_manual_cookie.toPlainText()
            
            # အကယ်၍ txt_manual_cookie ထဲမှာ data မရှိရင် config_mgr ကနေ ယူခြင်း
            if not cookie_data.strip():
                cookie_data = self.config_mgr.get("cookies_manual_text", "")
                self.ui.txt_manual_cookie.setText(cookie_data)
            
            # File ထဲကို ရေးခြင်း
            with open(self.manual_cookies_path, "w", encoding="utf-8") as f:
                f.write(cookie_data)
            
            # UI မှာ success message ပြခြင်း
            # self.show_custom_message("info", "Success", f"Cookies data saved successfully to:\n{self.manual_cookies_path}")
            
        except Exception as e:
            print(f"❌ Cookies သိမ်းတဲ့အခါ အမှားဖြစ်သွားပါတယ်: {e}")
            self.show_custom_message("critical", "Error", f"Failed to save cookies data:\n{str(e)}")

    def load_settings_into_ui(self):
        """ 🔍 Memory (RAM) ပေါ်ရှိ ဆက်တင်များအား UI Controls များထဲသို့ ဖြည့်စွက်ပေးခြင်း """
        mgr = self.config_mgr
        
        # General Settings
        self.ui.combo_Language.clear()
        self.ui.combo_Language.addItems(["English (American English)", "Burma (မြန်မာဘာသာ)"])
        self.ui.combo_Language.setCurrentText(mgr.get("language", "English (American English)"))

        self.ui.chk_add_clipboard_auto.setChecked(mgr.get("add_links_clipboard", False))
        self.ui.chk_start_download_auto.setChecked(mgr.get("auto_start_download", False))
        self.ui.chk_remove_completed_auto.setChecked(mgr.get("auto_remove_completed", False))
        self.ui.chk_play_after_downloaded_auto.setChecked(mgr.get("play_after_downloaded", False))
        self.ui.chk_minimize_to_tray.setChecked(mgr.get("minimize_to_tray", False))
        self.ui.chk_notify_fetched.setChecked(mgr.get("notify_fetched", True))
        self.ui.chk_notify_download_started.setChecked(mgr.get("notify_download_started", True))
        self.ui.chk_notify_download_completed.setChecked(mgr.get("notify_download_completed", True))
        self.ui.chk_auto_update.setChecked(mgr.get("check_auto_update", True))
            
        # Download Settings
        res_val = str(mgr.get("resolution", 1080))
        res_index = self.ui.combo_pref_res.findText(res_val)

        if res_index != -1:
            self.ui.combo_pref_res.setCurrentIndex(res_index)
        else:
            self.ui.combo_pref_res.setCurrentIndex(0)  # ရှာမတွေ့ပါက 'none' သို့ သတ်မှတ်မည်

        vcon_val = str(mgr.get("video_ext", "mp4"))
        vcon_index = self.ui.combo_pref_vcontainer.findText(vcon_val)

        if vcon_index != -1:
            self.ui.combo_pref_vcontainer.setCurrentIndex(vcon_index)
        else:
            self.ui.combo_pref_vcontainer.setCurrentIndex(0)  # ရှာမတွေ့ပါက 'none' သို့ သတ်မှတ်မည်

        vcodec_val = str(mgr.get("video_codec", "h264"))
        vcodec_index = self.ui.combo_pref_vcodec.findText(vcodec_val)

        if vcodec_index != -1:
            self.ui.combo_pref_vcodec.setCurrentIndex(vcodec_index)
        else:
            self.ui.combo_pref_vcodec.setCurrentIndex(0)  # ရှာမတွေ့ပါက 'none' သို့ သတ်မှတ်မည်

        acon_val = str(mgr.get("audio_ext", "m4a"))
        acon_index = self.ui.combo_pref_acontainer.findText(acon_val)

        if acon_index != -1:
            self.ui.combo_pref_acontainer.setCurrentIndex(acon_index)
        else:
            self.ui.combo_pref_acontainer.setCurrentIndex(0)  # ရှာမတွေ့ပါက 'none' သို့ သတ်မှတ်မည်

        acodec_val = str(mgr.get("audio_codec", "m4a"))
        acodec_index = self.ui.combo_pref_acodec.findText(acodec_val)

        if acodec_index != -1:
            self.ui.combo_pref_acodec.setCurrentIndex(acodec_index)
        else:
            self.ui.combo_pref_acodec.setCurrentIndex(0)  # ရှာမတွေ့ပါက 'none' သို့ သတ်မှတ်မည်

        self.ui.spin_Simultaneous.setValue(mgr.get("simultaneous_limit", 1))
        self.ui.chk_speed_limit.setChecked(mgr.get("use_speed_limit", False))
        self.ui.spin_speed_limit.setValue(mgr.get("speed_limit_val", 500))
        self.ui.inp_dowload_path.setText(mgr.get("download_path", ""))
        self.ui.chk_forceOverwrite.setChecked(mgr.get("force_overwrite", False))
        self.ui.chk_awakeMode.setChecked(mgr.get("awake_mode", False))
        
        # Network Settings
        self.ui.chk_use_proxy.setChecked(mgr.get("use_proxy", False))
        self.ui.inp_proxy_host.setText(mgr.get("proxy_host", ""))
        self.ui.spin_proxy_port.setValue(mgr.get("proxy_port", 8080))

        # Cookie Settings
        cookies_type = str(mgr.get("cookies_type", "none")).lower()
        if cookies_type == "manual":
            self.ui.btnManual.setChecked(True)
            self.on_cookie_mode_changed(1)
        elif cookies_type == "file":
            self.ui.btnCookieFile.setChecked(True)
            self.on_cookie_mode_changed(2)
        elif cookies_type == "browser":
            self.ui.btnFromBrowser.setChecked(True)
            self.on_cookie_mode_changed(3)
        else:
            self.ui.btnNone.setChecked(True)
            self.on_cookie_mode_changed(0)

        if hasattr(self.ui, 'inp_cookies_path'):
            self.ui.inp_cookies_path.setText(mgr.get("cookies_path", ""))
        if hasattr(self.ui, 'txt_manual_cookie'):
            self.ui.txt_manual_cookie.setText(mgr.get("cookies_manual_text", ""))
        if hasattr(self.ui, 'combo_browser'):
            self.ui.combo_browser.setCurrentText(mgr.get("cookies_browser_name", "Chrome"))

    def on_browse_clicked(self):
        current_path = self.ui.inp_dowload_path.text()
        dir_path = QFileDialog.getExistingDirectory(self, "Select Download Directory", current_path)
        if dir_path:
            self.ui.inp_dowload_path.setText(os.path.normpath(dir_path))

    def on_browse_cookies_clicked(self):
        current_path = self.ui.inp_cookies_path.text() if hasattr(self.ui, 'inp_cookies_path') else ""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Cookies File", current_path, "Text Files (*.txt);;All Files (*)")
        if file_path and hasattr(self.ui, 'inp_cookies_path'):
            self.ui.inp_cookies_path.setText(os.path.normpath(file_path))

    def get_selected_cookies_type(self):
        if self.ui.btnManual.isChecked():
            return "manual"
        elif self.ui.btnCookieFile.isChecked():
            return "file"
        elif self.ui.btnFromBrowser.isChecked():
            return "browser"
        return "none"

    def on_save_clicked(self):
        """ GUI ထဲက ဒေတာများကို Config ထဲသို့ သိမ်းဆည်းခြင်း """
        use_Cookies = False
        if self.get_selected_cookies_type() != "none":
            use_Cookies = True
        else:
            use_Cookies = False
            
        updated_data = {
            "language": self.ui.combo_Language.currentText(),
            "add_links_clipboard": self.ui.chk_add_clipboard_auto.isChecked(),
            "auto_start_download": self.ui.chk_start_download_auto.isChecked(),
            "auto_remove_completed": self.ui.chk_remove_completed_auto.isChecked(),
            "play_after_downloaded": self.ui.chk_play_after_downloaded_auto.isChecked(),
            "minimize_to_tray": self.ui.chk_minimize_to_tray.isChecked(),
            "notify_fetched": self.ui.chk_notify_fetched.isChecked(),
            "notify_download_started": self.ui.chk_notify_download_started.isChecked(),
            "notify_download_completed": self.ui.chk_notify_download_completed.isChecked(),
            "check_auto_update": self.ui.chk_auto_update.isChecked(),
            "video_ext": self.ui.combo_pref_vcontainer.currentText(),
            "resolution": self.ui.combo_pref_res.currentText(),
            "video_codec": self.ui.combo_pref_vcodec.currentText(),
            "audio_ext": self.ui.combo_pref_acontainer.currentText(),
            "audio_codec": self.ui.combo_pref_acodec.currentText(),
            "use_speed_limit": self.ui.chk_speed_limit.isChecked(),
            "simultaneous_limit": self.ui.spin_Simultaneous.value(),
            "speed_limit_val": self.ui.spin_speed_limit.value(),
            "download_path": self.ui.inp_dowload_path.text(),
            "force_overwrite": self.ui.chk_forceOverwrite.isChecked(),
            "awake_mode": self.ui.chk_awakeMode.isChecked(),
            "use_proxy": self.ui.chk_use_proxy.isChecked(),
            "proxy_host": self.ui.inp_proxy_host.text(),
            "proxy_port": self.ui.spin_proxy_port.value(),
            # Cookies ဆက်တင်များ
            "use_cookies": use_Cookies,
            "cookies_type": self.get_selected_cookies_type(),
            "cookies_path": self.ui.inp_cookies_path.text() if hasattr(self.ui, 'inp_cookies_path') else "",
            "cookies_manual_text": self.ui.txt_manual_cookie.toPlainText() if hasattr(self.ui, 'txt_manual_cookie') else "",
            "cookies_browser_name": self.ui.combo_browser.currentText() if hasattr(self.ui, 'combo_browser') else "Chrome"
        }

        try:
            if self.config_mgr.update_multiple(updated_data):
                self.accept()
            else:
                self.show_custom_message("warning", "Save Error", "Failed to save configuration settings.")
        except Exception as e:
            self.show_custom_message("critical", "Error", f"An unexpected error occurred while saving: {e}")

    def on_restore_defaults_clicked(self):
        """ Dark Theme Style ဖြင့် Restore Confirmation Dialog ပြသခြင်း """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Confirm Reset')
        msg_box.setText('Are you sure you want to restore all settings to default?')
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        btn_yes = msg_box.addButton(QMessageBox.StandardButton.Yes)
        btn_no = msg_box.addButton(QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(btn_no)
        
        self.apply_msgbox_style(msg_box)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_yes:
            if os.path.exists(self.manual_cookies_path):
                try:
                    os.remove(self.manual_cookies_path)
                except Exception as e:
                    print(f"❌ Failed to delete manual cookies file: {e}")
            else:
                print("ℹ️ Manual cookies file does not exist.")

            if self.config_mgr.restore_defaults():
                self.load_settings_into_ui()
                self.show_custom_message("info", "Success", "All settings have been restored to default.")
                self.accept()
            else:
                self.show_custom_message("warning", "Error", "Failed to restore default settings.")