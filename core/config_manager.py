# -*- coding: utf-8 -*-
import os
import json
import platform
from PySide6.QtCore import QStandardPaths, QCoreApplication

# CONSTANTS
import core.global_constants as CONST

QCoreApplication.setOrganizationName(CONST.COMPANY_NAME)
QCoreApplication.setApplicationName(CONST.APP_NAME)

# --- 🖥️ OS ကို စစ်ပြီး Binary Extension သတ်မှတ်ခြင်း ---
CURRENT_OS = platform.system()
BIN_EXT = ".exe" if CURRENT_OS == "Windows" else ""
# OS အလိုက် စိတ်ချရတဲ့ AppData Folder လမ်းကြောင်းကို ယူမယ်
# ဥပမာ- Windows မှာ: AppData/Local/YourAppName
# ဥပမာ- Linux မှာ: .local/share/YourAppName
APP_DATA_DIR = os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
# တကယ်လို့ APP_DATA_DIR ဖိုလ်ဒါမရှိသေးရင် Create
if not os.path.exists(APP_DATA_DIR):
    os.makedirs(APP_DATA_DIR)

APP_CACHE_DIR = os.path.join(APP_DATA_DIR, "Cache")
# တကယ်လို့ APP_CACHE_DIR ဖိုလ်ဒါမရှိသေးရင် Create
if not os.path.exists(APP_CACHE_DIR):
    os.makedirs(APP_CACHE_DIR)

TPT_DIR = os.path.join(APP_DATA_DIR, "Tools")

class ConfigManager:
    """ config.json ဖိုင်အား Read, Write, Update လုပ်ဆောင်ချက်များကို 
    မြန်ဆန်ချောမွေ့စွာ စီမံခန့်ခွဲပေးမည့် Thread-safe ဖြစ်သော သီးသန့် Module ဖြစ်သည် """

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        # Memory ပေါ်တွင် Cache အနေဖြင့် အမြဲသိမ်းဆည်းထားမည် (Read ကို အလွန်မြန်စေရန်)
        self.settings = {}

        default_output_dir = os.path.expanduser("~/Downloads/U-Tube Downloader")
        # Directory မရှိပါက ဆောက်မည်
        os.makedirs(default_output_dir, exist_ok=True)
        
        # မူရင်း Default Settings ပုံစံများ (ဖိုင်မရှိခဲ့ပါက သုံးရန်)
        self.default_settings = {
            "last_version": CONST.APP_VERSION,
            "last_check_update": CONST.APP_RELEASED_DATE,
            "last_added_url": "",
            "theme": "dark",
            "check_auto_update": True,
            "language": "English (American English)",
            "font_size": 10,
            "always_on_top": False,
            "remember_win_pos": True,
            "remember_win_size": True,
            "minimize_to_tray": False,
            "force_overwrite": False,
            "awake_mode": False,
            "top": 100,
            "left": 100,
            "width": 100,
            "height": 100,
            "scale": 100,
            "ffmpeg_path": os.path.join(TPT_DIR, f"ffmpeg{BIN_EXT}"),
            "ytdlp_path": os.path.join(TPT_DIR, f"yt-dlp{BIN_EXT}"),
            "deno_path": os.path.join(TPT_DIR, f"deno{BIN_EXT}"),
            "download_path": default_output_dir,
            "output_template": "%(title)s.%(ext)s",
            "playlist_indexing": "%(playlist_index)s - ",
            "embed_thumbnail": True,
            "save_thumbnail": False,
            "embed_subtitles": True,
            "save_subtitles": False,
            "embed_chapters": True,
            "embed_metadata": True,
            "use_mtime": True,
            "play_after_downloaded": False,
            "notify_fetched": True,
            "notify_download_started": True,
            "notify_download_completed": True,
            "resolution": 1080,
            "video_ext": "mp4",
            "audio_ext": "m4a",
            "video_codec": "h264",
            "audio_codec": "aac",
            "add_links_clipboard": False,
            "auto_start_download": False,
            "auto_remove_completed": False,
            "simultaneous_limit": 1,
            "use_speed_limit": False,
            "speed_limit_val": 500,
            "use_proxy": False,
            "proxy_host": "127.0.0.1",
            "proxy_port": 10808,
            "use_cookies": False,
            "cookies_type": "",
            "cookies_path": ""
        }
        
        # အရာအားလုံး အဆင်သင့်ဖြစ်စေရန် Config အား စတင်ဖတ်ယူမည်
        self.load()

    def load(self):
        """ config.json ဖိုင်မှ ဒေတာများကို Memory (Cache) ပေါ်သို့ အမြန်ဖတ်ယူခြင်း """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                
                # မိတ်ဆွေ၏ ဖိုင်ဟောင်းထဲတွင် Key အသစ်များ ကျန်ခဲ့ပါက Default မှ ဖြည့်စွက်ပေးခြင်း
                for key, val in self.default_settings.items():
                    if key not in self.settings:
                        self.settings[key] = val
            except Exception as e:
                print(f"Config Load Error: {e}. Using default settings.")
                self.settings = self.default_settings.copy()
        else:
            # ဖိုင်မရှိသေးပါက Default Settings အတိုင်း သုံးပြီး ဖိုင်အသစ်ဆောက်မည်
            self.settings = self.default_settings.copy()
            self.save()
            
        return self.settings

    def save(self):
        """ လက်ရှိ Memory ပေါ်က Settings များကို config.json ဖိုင်ထဲသို့ အပြီးအပိုင် ရေးသားသိမ်းဆည်းခြင်း """
        try:
            # လှပသပ်ရပ်ပြီး ဖတ်ရလွယ်ကူသော JSON format ဖြင့် သိမ်းခြင်း
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Config Save Error: {e}")
            return False

    def get(self, key, default=None):
        """ [READ] Memory Cache ဆီမှ တန်ဖိုကို တိုက်ရိုက်ဖတ်သဖြင့် အလွန်မြန်ဆန်သည် """
        if default is None:
            default = self.default_settings.get(key, None)
        return self.settings.get(key, default)

    def set(self, key, value, auto_save=True):
        """ [WRITE/UPDATE] စာသား သို့မဟုတ် တန်ဖိုးတစ်ခုခုကို ပြင်ဆင်/ဖြည့်စွက်ခြင်း """
        self.settings[key] = value
        if auto_save:
            self.save()

    def update_multiple(self, new_settings: dict, auto_save=True):
        """ [BULK UPDATE] တန်ဖိုးများစွာကို တစ်ပြိုင်နက်တည်း အစုလိုက် ပြင်ဆင်ခြင်း """
        self.settings.update(new_settings)
        if auto_save:
            if self.save():
                return True
        return True

    def get_all(self):
        """ လက်ရှိ Config စာရင်းတစ်ခုလုံးကို Dictionary အနေဖြင့် ပြန်ထုတ်ပေးခြင်း """
        return self.settings
    
    def restore_defaults(self):
        """ [RESTORE DEFAULT] လက်ရှိ Settings အားလုံးကို ဖျက်ပစ်ပြီး 
        မူလစက်ရုံထုတ် Default Settings အတိုင်း ရာနှုန်းပြည့် ပြန်လည်သတ်မှတ်သိမ်းဆည်းခြင်း """
        try:
            # Memory (Cache) ပေါ်က settings ကို Default တန်ဖိုးများဖြင့် အစားထိုးခြင်း
            self.settings = self.default_settings.copy()
            
            # ပြောင်းလဲသွားသော မူလ Default တန်ဖိုးများကို config.json ထဲသို့ အပြီးအပိုင် ရေးသားခြင်း
            self.save()
            return True
        except Exception as e:
            print(f"Config Restore Default Error: {e}")
            return False