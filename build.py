import platform
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
RELEASED_DIR = BASE_DIR / "dist"
MAIN_SCRIPT = BASE_DIR / "main.py"
UI_FILE = BASE_DIR / "ui" / "settings_dialog.ui"

IS_WINDOWS = platform.system() == "Windows"

# OS အပေါ်မူတည်ပြီး Path ခွဲခြားတဲ့ သင်္ကေတ သတ်မှတ်ခြင်း (Windows တွင် ';' ၊ Linux တွင် ':')
path_sep = ";" if IS_WINDOWS else ":"

args = [
    "pyinstaller",
    "--noconfirm",                      # Build ဖိုင်အဟောင်းရှိရင် မမေးဘဲ အလိုအလျောက် အစားထိုးပစ်ရန်
    "--clean",                          # Build မစခင် PyInstaller ရဲ့ cache ဖိုင်အဟောင်းများကို ရှင်းထုတ်ရန်
    "--noupx",                          # UPX (compress) ကို မသုံးရန်
    "--onedir",                         # Output ကို Folder တစ်ခုတည်းအဖြစ် (DLLs နဲ့ Assets တွဲလျက်) ထုတ်ပေးရန်
    "--windowed",                       # GUI Application ဖြစ်၍ App ပွင့်လာလျှင် Console/Terminal Window မပြရန်
    "--collect-all=desktop_notifier",   # desktop_notifier library ရဲ့ လိုအပ်သမျှ Module, Data, Binary အားလုံးကို တစ်ပါတည်း စုစည်းထည့်သွင်းရန်
    f"--add-data={UI_FILE}{path_sep}ui",# .ui ဖိုင်ကို output folder ထဲရှိ "ui" folder အတွင်းသို့ ထည့်သွင်းပေးရန်
    str(MAIN_SCRIPT),                   # Build လုပ်မည့် ပင်မ Python script ဖိုင်
]

# Windows အတွက် သီးသန့် Arguments များ
if IS_WINDOWS:
    ICON_PATH = RELEASED_DIR / "app_icon.ico"
    VERSION_FILE = RELEASED_DIR / "version-file.txt"
    
    args.extend([
        f"--icon={ICON_PATH}",                # App ၏ Icon (.ico) လမ်းကြောင်း သတ်မှတ်ရန်
        f"--version-file={VERSION_FILE}",     # File Version နဲ့ Details အချက်အလက်ပါသည့် ဖိုင်လမ်းကြောင်း သတ်မှတ်ရန်
        "--name=YawStar U-Tube Downloader",   # Windows တွင် ထွက်လာမည့် EXE ဖိုင်၏ နာမည်
    ])
else:
    # Linux အတွက် သီးသန့် Arguments များ
    args.extend([
        "--name=YawStar_U-Tube_Downloader",    # Linux တွင် ထွက်လာမည့် Executable ဖိုင်၏ နာမည်
    ])

if __name__ == "__main__":
    cmd = ["uv", "run", "--with", "pyinstaller"] + args
    subprocess.run(cmd, check=True)