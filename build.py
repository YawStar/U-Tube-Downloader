import platform
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
MAIN_SCRIPT = BASE_DIR / "main.py"
UI_FILE = BASE_DIR / "ui" / "settings_dialog.ui"

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
MACHINE = platform.machine().lower()

# Linux အတွက် Architecture အမည် သတ်မှတ်ခြင်း (amd64, arm64, x32)
if not IS_WINDOWS:
    if MACHINE in ("x86_64", "amd64"):
        arch_name = "amd64"
    elif MACHINE in ("aarch64", "arm64"):
        arch_name = "arm64"
    elif MACHINE in ("i386", "i686", "x86"):
        arch_name = "x32"
    else:
        arch_name = MACHINE

# OS ပေါ်မူတည်၍ Output Folder ခွဲခြားခြင်း (Windows အတွက် dist/Windows ၊ Linux အတွက် dist/Linux/{arch} ၊ macOS အတွက် dist/macOS/{arch})
RELEASED_DIR = (
    BASE_DIR / "dist" / "Windows"
    if IS_WINDOWS
    else BASE_DIR / "dist" / "macOS" / arch_name
    if IS_MACOS
    else BASE_DIR / "dist" / "Linux" / arch_name
)

# OS အပေါ်မူတည်ပြီး Path ခွဲခြားတဲ့ သင်္ကေတ သတ်မှတ်ခြင်း (Windows တွင် ';' ၊ Linux/macOS တွင် ':')
path_sep = ";" if IS_WINDOWS else ":"

args = [
    "pyinstaller",
    "--noconfirm",                      # Build ဖိုင်အဟောင်းရှိရင် မမေးဘဲ အလိုအလျောက် အစားထိုးပစ်ရန်
    "--clean",                          # Build မစခင် PyInstaller ရဲ့ cache ဖိုင်အဟောင်းများကို ရှင်းထုတ်ရန်
    "--noupx",                          # UPX (compress) ကို မသုံးရန်
    "--onedir",                         # Output ကို Folder တစ်ခုတည်းအဖြစ် (DLLs နဲ့ Assets တွဲလျက်) ထုတ်ပေးရန်
    "--windowed",                       # GUI Application ဖြစ်၍ App ปွင့်လာလျှင် Console/Terminal Window မပြရန်
    f"--distpath={RELEASED_DIR}",       # Output ထွက်မည့် Folder လမ်းကြောင်း သတ်မှတ်ရန်
    "--collect-all=desktop_notifier",   # desktop_notifier library ရဲ့ လိုအပ်သမျှ Module, Data, Binary အားလုံးကို တစ်ပါတည်း စုစည်းထည့်သွင်းရန်
    f"--add-data={UI_FILE}{path_sep}ui",# .ui ဖိုင်ကို output folder ထဲရှိ "ui" folder အတွင်းသို့ ထည့်သွင်းပေးရန်
    str(MAIN_SCRIPT),                   # Build လုပ်မည့် ပင်မ Python script ဖိုင်
]

# Windows အတွက် သီးသန့် Arguments များ
if IS_WINDOWS:
    ICON_PATH = BASE_DIR / "assets" / "icons" / "app_icon.ico"
    VERSION_FILE = BASE_DIR / "assets" / "version-file.txt"
    
    args.extend([
        f"--icon={ICON_PATH}",                # App ၏ Icon (.ico) လမ်းကြောင်း သတ်မှတ်ရန်
        f"--version-file={VERSION_FILE}",     # File Version နဲ့ Details အချက်အလက်ပါသည့် ဖိုင်လမ်းကြောင်း သတ်မှတ်ရန်
        "--name=YawStar U-Tube Downloader",   # Windows တွင် ထွက်လာမည့် EXE ဖိုင်၏ နာမည်
    ])

# macOS အတွက် သီးသန့် Arguments များ
elif IS_MACOS:
    ICNS_PATH = BASE_DIR / "assets" / "icons" / "app_icon.icns"
    
    args.extend([
        f"--icon={ICNS_PATH}",                          # App ၏ Icon (.icns) လမ်းကြောင်း သတ်မှတ်ရန်
        "--name=YawStar U-Tube Downloader",             # macOS တွင် ထွက်လာမည့် App ဖိုင်၏ နာမည်
        "--osx-bundle-identifier=com.yawstar.utube.downloader",  # macOS App Bundle Identifier သတ်မှတ်ရန်
    ])

else:
    # Linux အတွက် သီးသန့် Arguments များ
    args.extend([
        "--name=YawStar_U-Tube_Downloader",    # Linux တွင် ထွက်လာမည့် Executable ဖိုင်၏ နာမည်
    ])

if __name__ == "__main__":
    cmd = ["uv", "run", "--with", "pyinstaller"] + args
    subprocess.run(cmd, check=True)