import platform
import subprocess
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()          # ← resolve() ထည့်
MAIN_SCRIPT = (BASE_DIR / "main.py").resolve()
UI_FILE = (BASE_DIR / "ui" / "settings_dialog.ui").resolve()

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
    if MACHINE in ("amd64", "x86_64"):
        arch_name = "amd64"
    elif MACHINE in ("arm64", "aarch64"):
        arch_name = "arm64"
    elif MACHINE in ("x86", "i386", "i686"):
        arch_name = "x86"
    else:
        arch_name = MACHINE
else:
    if MACHINE in ("x86_64", "amd64"):
        arch_name = "amd64"
    elif MACHINE in ("aarch64", "arm64"):
        arch_name = "arm64"
    elif MACHINE in ("i386", "i686", "x86"):
        arch_name = "x32"
    else:
        arch_name = MACHINE

# OS ပေါ်မူတည်၍ Output Folder ခွဲခြားခြင်း
RELEASED_DIR = (
    BASE_DIR / "dist" / "Windows" / arch_name
    if IS_WINDOWS
    else BASE_DIR / "dist" / "macOS" / arch_name
    if IS_MACOS
    else BASE_DIR / "dist" / "Linux" / arch_name
)

# CI အတွက် အလယ်အလတ် ဖိုင်များ ထားရှိမည့်နေရာ (repo root ကို မညစ်စေရန်)
BUILD_DIR = BASE_DIR / "build"
SPEC_DIR = BUILD_DIR / "spec"

# OS အပေါ်မူတည်ပြီး Path ခွဲခြားတဲ့ သင်္ကေတ သတ်မှတ်ခြင်း
path_sep = ";" if IS_WINDOWS else ":"

args = [
    "pyinstaller",
    "--noconfirm",
    "--clean",
    "--noupx",
    "--onedir",
    "--windowed",
    f"--distpath={RELEASED_DIR}",
    f"--workpath={BUILD_DIR / 'work'}",              # ← CI အတွက် ထည့်
    f"--specpath={SPEC_DIR}",                         # ← CI အတွက် ထည့်
    "--collect-all=desktop_notifier",
    f"--add-data={UI_FILE}{path_sep}ui",
    str(MAIN_SCRIPT),
]

# Windows အတွက် သီးသန့် Arguments များ
if IS_WINDOWS:
    ICON_PATH = (BASE_DIR / "assets" / "icons" / "app_icon.ico").resolve()
    VERSION_FILE = (BASE_DIR / "assets" / "version-file.txt").resolve()

    args.extend([
        f"--icon={ICON_PATH}",
        f"--version-file={VERSION_FILE}",
        f"--name={APP_NAME}",
    ])

# macOS အတွက် သီးသန့် Arguments များ
elif IS_MACOS:
    ICNS_PATH = (BASE_DIR / "assets" / "icons" / "app_icon.icns").resolve()

    if arch_name == "arm64":
        target_arch = "arm64"
    elif arch_name in ("amd64", "x86_64"):
        target_arch = "x86_64"
    else:
        target_arch = arch_name

    args.extend([
        f"--icon={ICNS_PATH}",
        f"--name={APP_NAME}",
        f"--osx-bundle-identifier={BUNDLE_ID}",
        f"--target-architecture={target_arch}",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtNetwork",
        "--hidden-import=PySide6.QtSvg",
        "--exclude-module=PySide6.QtWebEngineCore",
        "--exclude-module=PySide6.QtWebEngineWidgets",
        "--exclude-module=PySide6.QtQuick",
        "--exclude-module=PySide6.QtQml",
    ])

else:
    # Linux အတွက် သီးသန့် Arguments များ
    args.extend([
        f"--name={APP_NAME.replace(' ', '_')}",
    ])


def clean_old_build():
    """Build မလုပ်ခင် build folder နဲ့ ကိုယ့် app ရဲ့ spec ဖိုင်အဟောင်းများကို ရှင်းခြင်း"""
    # build/ folder ရှင်းခြင်း
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        print(f"🧹 ရှင်းပြီး: {BUILD_DIR}")

    # ကိုယ့် app နာမည်နဲ့ ကိုက်တဲ့ spec ဖိုင်ကိုပဲ ရှင်းရန် (တခြား project spec မထိ)
    # App name က OS အလိုက် ကွာခြားနိုင်လို့ ဖြစ်နိုင်တဲ့ နာမည်အားလုံး စစ်
    possible_spec_names = {
        f"{APP_NAME}.spec",                       # Windows / macOS
        f"{APP_NAME.replace(' ', '_')}.spec",     # Linux
        "main.spec",                              # PyInstaller default
    }
    for name in possible_spec_names:
        spec_file = BASE_DIR / name
        if spec_file.exists():
            spec_file.unlink()
            print(f"🧹 ရှင်းပြီး: {spec_file.name}")


def build_app():
    """PyInstaller ဖြင့် App ကို build လုပ်ခြင်း"""
    # uv ရှိမရှိ စစ်ဆေး — CI မှာ uv setup မလုပ်ထားရင် ပြဿနာ မဖြစ်စေရန်
    if shutil.which("uv") is None:
        print("❌ 'uv' မတွေ့ပါ။ 'pip install uv' သို့မဟုတ် CI setup step ထည့်ပါ။")
        sys.exit(1)

    cmd = ["uv", "run", "--python", "3.13", "--with", "pyinstaller"] + args
    print("Running:", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)


def copy_files():
    """Windows build ပြီးနောက် လိုအပ်သော ဖိုင်များကို App folder ထဲ ကူးခြင်း"""
    app_folder = RELEASED_DIR / APP_NAME

    if not app_folder.exists():
        print(f"⚠️  App folder မတွေ့ပါ: {app_folder}")
        return

    files_to_copy = [
        (BASE_DIR,                        "Changelog.txt"),
        (BASE_DIR,                        "LICENSE"),
        (BASE_DIR / "dist" / "Windows",   "YawStar.URL"),
        (BASE_DIR / "dist" / "Windows",   "License Agreement.txt"),
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

    if shutil.which("create-dmg") is None:
        print("⚠️  'create-dmg' မတွေ့ပါ။ 'brew install create-dmg' ဖြင့် install လုပ်ပါ။")
        print("   .app bundle ကို ဒီအတိုင်း သုံးနိုင်ပါတယ်:", RELEASED_DIR / f"{APP_NAME}.app")
        return

    app_path = RELEASED_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        print(f"⚠️  .app bundle မတွေ့ပါ: {app_path}")
        return

    version = "1.0.0"
    version_file = BASE_DIR / "assets" / "version-file.txt"
    if version_file.exists():
        try:
            for line in version_file.read_text(encoding="utf-8").splitlines():
                if "FileVersion" in line or "ProductVersion" in line:
                    parts = line.split()
                    if parts:
                        version = parts[-1].strip().rstrip(",")
                        break
        except Exception:
            pass

    dmg_path = RELEASED_DIR / f"{APP_NAME_SAFE}-{version}-{arch_name}.dmg"
    if dmg_path.exists():
        dmg_path.unlink()

    # create-dmg version အလိုက် flag ကွာခြားနိုင်လို့ base command ကို ရေးပြီး
    # --no-internet-enable ကို version စစ်ပြီးမှ ထည့်ပါ
    dmg_cmd = [
        "create-dmg",
        "--volname", APP_NAME,
        "--window-pos", "200", "120",
        "--window-size", "600", "400",
        "--icon-size", "100",
        "--icon", f"{APP_NAME}.app", "150", "190",
        "--app-drop-link", "450", "190",
    ]

    # create-dmg ရဲ့ help မှာ --no-internet-enable ပါမပါ စစ်
    try:
        help_out = subprocess.run(
            ["create-dmg", "--help"],
            capture_output=True, text=True, check=False
        ).stdout
        if "--no-internet-enable" in help_out:
            dmg_cmd.append("--no-internet-enable")
    except Exception:
        pass

    dmg_cmd.extend([str(dmg_path), str(app_path)])

    print("Creating DMG:", " ".join(str(c) for c in dmg_cmd))
    result = subprocess.run(dmg_cmd, check=False)

    if dmg_path.exists():
        print(f"✅ DMG ဖန်တီးပြီးပါပြီ: {dmg_path}")
    else:
        print(f"⚠️  DMG ဖန်တီးမှု မအောင်မြင်ပါ (exit code: {result.returncode})")
        print(f"   .app bundle ကို ဒီအတိုင်း သုံးနိုင်ပါတယ်: {app_path}")


if __name__ == "__main__":
    clean_old_build()       # ← Build မတိုင်ခင် အရင်ရှင်း
    build_app()

    if IS_WINDOWS:
        copy_files()

    if IS_MACOS:
        create_dmg_macos()