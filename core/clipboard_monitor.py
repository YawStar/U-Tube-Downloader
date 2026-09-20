# -*- coding: utf-8 -*-
import re
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QGuiApplication

class ClipboardMonitor(QObject):
    """ Windows Clipboard ထဲတွင် စာသားပြောင်းလဲသွားမှုကို 
    Qt Native Signal စနစ်ဖြင့် အလိုအလျောက် စောင့်ကြည့်ပေးမည့် သီးသန့် Module ဖြစ်သည် """
    
    url_captured = Signal(str) # URL မိလာပါက ပင်မ Window သို့ ပို့ပေးမည့် Signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_clipboard_content = ""
        self.clipboard = QGuiApplication.clipboard()
        # Signal ချိတ်ဆက်ထားခြင်း ရှိ/မရှိ စောင့်ကြည့်မည့် Flag အသစ်
        self.is_connected = False
        
        # စောင့်ကြည့်လိုသော Domain စာရင်းများ
        self.supported_domains = [
            'youtube.com', 'youtu.be', 'facebook.com', 'fb.com', 'fb.watch',
            'instagram.com', 'tiktok.com', 'twitch.tv', 'x.com', 'soundcloud.com',
            'reddit.com', 'pinterest.com', 'tumblr.com', 'vimeo.com', 'dailymotion.com',
            'bilibili.com', 'rumble.com', 'kick.com', 'streamable.com', 'bandcamp.com',
            'podcasts.apple.com', 'open.spotify.com', 'mixcloud.com', 
            'bbc.com', 'edition.cnn.com', 'ted.com',
            'pornhub.com', 'xvideos.com', 'xnxx.com', 'xhamster.com',
            'eporner.com', 'youporn.com', 'redtube.com', 'tnaflix.com',
            'pornhat.com'
        ]

    def start(self):
        """ Clipboard စောင့်ကြည့်မှုစနစ်အား စတင်ချိတ်ဆက်ခြင်း """
        # ချိတ်ဆက်မှု မရှိသေးမှသာ အသစ်ချိတ်မည် (Duplicate ချိတ်ဆက်ခြင်းနှင့် Disconnect Warning ကို တားဆီးရန်)
        if not self.is_connected:
            self.clipboard.dataChanged.connect(self.on_clipboard_changed)
            self.is_connected = True
            # print(f"clipboard_connected : {self.is_connected}")

    def stop(self):
        """ Clipboard စောင့်ကြည့်မှုစနစ်အား ဖြတ်တောက်ရပ်နားခြင်း """
        # ချိတ်ဆက်ထားမှု ရှိမှသာ သန့်ရှင်းစွာ ဖြတ်တောက်မည်
        if self.is_connected:
            try:
                self.clipboard.dataChanged.disconnect(self.on_clipboard_changed)
            except Exception:
                pass
            self.is_connected = False
            # print(f"clipboard_connected : {self.is_connected}")

    def on_clipboard_changed1(self):
        """ Clipboard ပြောင်းလဲသွားသည့်အခါ စမတ်ကျကျ ဖတ်ရှုစစ်ဆေးခြင်း """
        try:
            current_content = self.clipboard.text().strip()
            print("clipboard_changed detected!")
            print(f"last clipboard content : {self.last_clipboard_content}")
            print(f"current content : {current_content}")
            
            if current_content and current_content != self.last_clipboard_content:
                self.last_clipboard_content = current_content

                
                # URL ဟုတ်မဟုတ် RegEx ဖြင့် စစ်ဆေးခြင်း
                # url_regex = re.compile(r'^https?://([^/\\s]+)(?:/\\S*)?$', re.IGNORECASE)
                url_regex = re.compile(r'https?://\S+', re.IGNORECASE)
                match = url_regex.match(current_content)
                
                if match:
                    print("url is matched")
                    extracted_domain = match.group(1).lower()
                    # မိမိတို့ ပံ့ပိုးထားသော Domain ဟုတ်မဟုတ် စစ်ဆေးခြင်း
                    is_supported = any(domain in extracted_domain for domain in self.supported_domains)
                    
                    if is_supported:
                        print(f"is_supported : {is_supported}")
                        # ကိုက်ညီပါက Signal သုံး၍ ပင်မ GUI ထံသို့ လှမ်းပို့ခြင်း
                        self.url_captured.emit(current_content)
                    else:
                        print(f"is_supported : {is_supported}")
        except Exception as e:
            # Error တက်ပါက ဘာကြောင့်တက်လဲဆိုတာ သိရှိနိုင်ရန် Print ထုတ်ကြည့်ခြင်း
            print(f"❌ An Error occurred in monitor: {e}")

    def on_clipboard_changed2(self):
        """ Clipboard ပြောင်းလဲသွားသည့်အခါ စမတ်ကျကျ ဖတ်ရှုစစ်ဆေးခြင်း """
        try:
            current_content = self.clipboard.text().strip()
            
            if current_content and current_content != self.last_clipboard_content:
                # Domain နာမည်ကိုပါ Group(1) အဖြစ် ကွက်တိထုတ်ပေးမည့် စိတ်ချရသော RegEx
                # url_regex = re.compile(r'^https?://([^/\\\s]+)(?:/\\\S*)?$', re.IGNORECASE)
                url_regex = re.compile(r'https?://\S+', re.IGNORECASE)
                match = url_regex.match(current_content)
                
                if match:
                    print("🎯 URL is matched successfully!")
                    # Group(1) မှတစ်ဆင့် domain ကို သန့်သန့်ရှင်းရှင်း ထုတ်ယူခြင်း
                    extracted_domain = match.group(1).lower()
                    print(f"🌐 Extracted Domain: {extracted_domain}")
                    
                    # မိမိတို့ ပံ့ပိုးထားသော Domain ဟုတ်မဟုတ် စစ်ဆေးခြင်း
                    is_supported = any(domain in extracted_domain for domain in self.supported_domains)
                    print(f"📊 Is Supported Domain? : {is_supported}")
                    
                    if is_supported:
                        # အရာအားလုံး ကိုက်ညီသဖြင့် ပင်မ Window ဆီသို့ Signal လွှတ်တင်လိုက်ခြင်း
                        print(f"📢 Emitting URL Captured Signal: {current_content}")
                        self.url_captured.emit(current_content)
                        
                        # emit လုပ်ပြီးမှ last_clipboard_content ကို မှတ်သားပါမည်
                        self.last_clipboard_content = current_content
                    else:
                        print("⚠️ Domain not in supported list.")
        except Exception as e:
            # Error တက်ပါက ဘာကြောင့်တက်လဲဆိုတာ သိရှိနိုင်ရန် Print ထုတ်ကြည့်ခြင်း
            print(f"❌ An Error occurred in monitor: {e}")    

    def on_clipboard_changed(self):
        """ Clipboard ပြောင်းလဲသွားသည့်အခါ စမတ်ကျကျ ဖတ်ရှုစစ်ဆေးခြင်း """
        try:
            current_content = self.clipboard.text().strip()
            
            if current_content and current_content != self.last_clipboard_content:
                # Group(1) ပါဝင်အောင် ပြင်ဆင်ထားသော စမတ်ကျသည့် RegEx
                # https:// သို့မဟုတ် http:// နောက်က Domain နာမည်ကို ( ) ဖြင့် ကွက်တိ ဖမ်းယူထားပါသည်
                url_regex = re.compile(r'https?://([^/\\\s]+)\S*', re.IGNORECASE)
                match = url_regex.match(current_content)
                
                if match:
                    # print("🎯 URL is matched successfully!")
                    
                    # () ပါဝင်သွားပြီဖြစ်၍ group(1) သည် youtube.com သို့မဟုတ် youtu.be ကို ကွက်တိ ထုတ်ပေးပါမည်
                    extracted_domain = match.group(1).lower()
                    # print(f"🌐 Extracted Domain: {extracted_domain}")
                    
                    # မိမိတို့ ပံ့ပိုးထားသော Domain ဟုတ်မဟုတ် စစ်ဆေးခြင်း
                    is_supported = any(domain in extracted_domain for domain in self.supported_domains)
                    # print(f"📊 Is Supported Domain? : {is_supported}")
                    
                    if is_supported:
                        # print(f"📢 Emitting URL Captured Signal: {current_content}")
                        self.url_captured.emit(current_content)
                        self.last_clipboard_content = current_content
                    else:
                        print("⚠️ Domain not in supported list.")
        except Exception as e:
            # Error တက်ပါက ဘာကြောင့်တက်လဲဆိုတာ သိရှိနိုင်ရန် Print ထုတ်ကြည့်ခြင်း
            print(f"❌ An Error occurred in monitor: {e}")