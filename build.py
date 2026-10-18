import platform
import subprocess
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
MAIN_SCRIPT = BASE_DIR / "main.py"
UI_FILE = BASE_DIR / "ui" / "settings_dialog.ui"

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"
MACHINE = platform.machine().lower()

# App အမည် (OS အားလုံးအတွက် တစ်နေရာတည်း သတ်မှတ်)
APP_NAME = "YawStar U-Tube Downloader"
APP_NAME_SAFE = "YawStar-U-Tube-Downloader"  # ဖိုင်အမည်အတွက် space မပါသော version
BUNDLE_ID = "com.yawstar.utube.downloader"

# OS အလိုက် Architecture အမည် သတ်မှတ်ခြင်း
if IS_WINDOWS:
    # Windows convention: x86, amd64, ARM64
    if MACHINE in ("amd64", "x86_64"):
        arch_name = "amd64"
    elif MACHINE in ("arm64", "aarch64"):
        arch_name = "arm64"
    elif MACHINE in ("x86", "i386", "i686"):
        arch_name = "x86"      # ← Windows မှာ x86 လို့သတ်မှတ်
    else:
        arch_name = MACHINE
else:
    # Linux/macOS convention: x32, amd64, arm64
    if MACHINE in ("x86_64", "amd64"):
        arch_name = "amd64"
    elif MACHINE in ("aarch64", "arm64"):
        arch_name = "arm64"
    elif MACHINE in ("i386", "i686", "x86"):
        arch_name = "x32"      # ← Linux မှာ x32 လို့သတ်မှတ်
    else:
        arch_name = MACHINE

# OS ပေါ်မူတည်၍ Output Folder ခွဲခြားခြင်း
# (Windows အတွက် dist/Windows ၊ Linux အတွက် dist/Linux/{arch} ၊ macOS အတွက် dist/macOS/{arch})
RELEASED_DIR = (
    BASE_DIR / "dist" / "Windows" / arch_name
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
    "--windowed",                       # GUI Application ဖြစ်၍ App ပွင့်လာလျှင် Console/Terminal Window မပြရန်
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
        f"--name={APP_NAME}",                 # Windows တွင် ထွက်လာမည့် EXE ဖိုင်၏ နာမည်
    ])

# macOS အတွက် သီးသန့် Arguments များ
elif IS_MACOS:
    ICNS_PATH = BASE_DIR / "assets" / "icons" / "app_icon.icns"

    # Apple Silicon (arm64) နဲ့ Intel (x86_64) နှစ်မျိုးလုံးအတွက်
    # universal2 binary ထုတ်နိုင်ရင် "universal2" ကို သုံးပါ။
    # မဟုတ်ရင် လက်ရှိ runner ရဲ့ architecture အတိုင်း ထုတ်ပါ။
    if arch_name == "arm64":
        target_arch = "arm64"
    elif arch_name in ("amd64", "x86_64"):
        target_arch = "x86_64"
    else:
        target_arch = arch_name

    args.extend([
        f"--icon={ICNS_PATH}",                          # App ၏ Icon (.icns) လမ်းကြောင်း သတ်မှတ်ရန်
        f"--name={APP_NAME}",                           # macOS တွင် ထွက်လာမည့် App ဖိုင်၏ နာမည်
        f"--osx-bundle-identifier={BUNDLE_ID}",         # macOS App Bundle Identifier သတ်မှတ်ရန်
        f"--target-architecture={target_arch}",         # Target CPU architecture သတ်မှတ်ရန်
        # PySide6 modules တွေကို explicit ထည့်ထားခြင်း (dynamic import ပြဿနာ မဖြစ်ရန်)
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtNetwork",
        "--hidden-import=PySide6.QtSvg",
        # macOS မှာ တခြား OS တွေအတွက် မလိုတဲ့ modules တွေကို ဖယ်ထုတ်ခြင်း
        "--exclude-module=PySide6.QtWebEngineCore",
        "--exclude-module=PySide6.QtWebEngineWidgets",
        "--exclude-module=PySide6.QtQuick",
        "--exclude-module=PySide6.QtQml",
    ])

else:
    # Linux အတွက် သီးသန့် Arguments များ
    args.extend([
        f"--name={APP_NAME.replace(' ', '_')}",    # Linux တွင် ထွက်လာမည့် Executable ဖိုင်၏ နာမည်
    ])


def build_app():
    """PyInstaller ဖြင့် App ကို build လုပ်ခြင်း"""
    cmd = ["uv", "run", "--python", "3.13", "--with", "pyinstaller"] + args
    print("Running:", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)

def copy_files():
    """Windows build ပြီးနောက် လိုအပ်သော ဖိုင်များကို App folder ထဲ ကူးခြင်း"""
    app_folder = RELEASED_DIR / APP_NAME
    
    if not app_folder.exists():
        print(f"⚠️  App folder မတွေ့ပါ: {app_folder}")
        return
    
    # (source_folder, filename) အတွဲလိုက်
    files_to_copy = [
        (BASE_DIR,               "Changelog.txt"),
        (BASE_DIR,               "LICENSE"),
        (BASE_DIR / "dist" / "Windows",  "YawStar.URL"),
        (BASE_DIR / "dist" / "Windows",  "License Agreement.txt"),
    ]
    
    for source_folder, filename in files_to_copy:
        src = source_folder / filename
        dst = app_folder / filename
        
        if not src.exists():
            print(f"⚠️  Source ဖိုင် မတွေ့ပါ: {src}")
            continue
        
        shutil.copy2(src, dst)
        print(f"✅ Copy ကူးပြီး: {filename} → {app_folder}")

def create_dmg_macos():
    """macOS အတွက် .dmg ဖိုင် ဖန်တီးခြင်း (create-dmg လိုအပ်သည်)"""
    if not IS_MACOS:
        return

    # create-dmg ရှိမရှိ စစ်ဆေးခြင်း
    if shutil.which("create-dmg") is None:
        print("⚠️  'create-dmg' မတွေ့ပါ။ 'brew install create-dmg' ဖြင့် install လုပ်ပါ။")
        print("   .app bundle ကို ဒီအတိုင်း သုံးနိုင်ပါတယ်:", RELEASED_DIR / f"{APP_NAME}.app")
        return

    app_path = RELEASED_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        print(f"⚠️  .app bundle မတွေ့ပါ: {app_path}")
        return

    # Version ကို version-file.txt ကနေ ရယူနိုင်ရင် ရယူပါ၊ မရရင် default သုံးပါ
    version = "1.0.0"
    version_file = BASE_DIR / "assets" / "version-file.txt"
    if version_file.exists():
        try:
            for line in version_file.read_text(encoding="utf-8").splitlines():
                if "FileVersion" in line or "ProductVersion" in line:
                    # ဥပမာ: "  FileVersion: 1.2.3" ကနေ နံပါတ်ကို ဆွဲထုတ်
                    parts = line.split()
                    if parts:
                        version = parts[-1].strip().rstrip(",")
                        break
        except Exception:
            pass

    dmg_path = RELEASED_DIR / f"{APP_NAME_SAFE}-{version}-{arch_name}.dmg"
    if dmg_path.exists():
        dmg_path.unlink()

    dmg_cmd = [
        "create-dmg",
        "--volname", APP_NAME,
        "--window-pos", "200", "120",
        "--window-size", "600", "400",
        "--icon-size", "100",
        "--icon", f"{APP_NAME}.app", "150", "190",
        "--app-drop-link", "450", "190",
        "--no-internet-enable",
        str(dmg_path),
        str(app_path),
    ]
    print("Creating DMG:", " ".join(str(c) for c in dmg_cmd))
    # create-dmg က exit code 2 (AppleScript warning) ပြန်ပေးတတ်လို့ check=False
    result = subprocess.run(dmg_cmd, check=False)

    if dmg_path.exists():
        print(f"✅ DMG ဖန်တီးပြီးပါပြီ: {dmg_path}")
    else:
        print(f"⚠️  DMG ဖန်တီးမှု မအောင်မြင်ပါ (exit code: {result.returncode})")
        print(f"   .app bundle ကို ဒီအတိုင်း သုံးနိုင်ပါတယ်: {app_path}")


if __name__ == "__main__":
    build_app()

    # Windows ဆိုရင် လိုတဲ့ ဖိုင်တွေကူး
    if IS_WINDOWS:
        copy_files()

    # macOS ဆိုရင် .app ပြီးတာနဲ့ .dmg ကို ဆက်ထုတ်
    if IS_MACOS:
        create_dmg_macos()