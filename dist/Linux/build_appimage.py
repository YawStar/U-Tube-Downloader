#!/usr/bin/env python3

"""
Build an AppImage package using Type-2 Runtime (No FUSE required to run).

Expected structure:

    my_proj/
    ├── build_appimage.py
    ├── app_icon.png
    └── YawStar_U-Tube_Downloader/
        ├── YawStar_U-Tube_Downloader
        └── _internal/
            ├── ...
            └── ...

Output:

    dist/
        YawStar_U-Tube_Downloader-1.0.0.31-x86_64.AppImage
"""

from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_EXECUTABLE = "YawStar_U-Tube_Downloader"

PACKAGE_NAME = "yawstar-u-tube-downloader"

DISPLAY_NAME = "YawStar U-Tube Downloader"

VERSION = "1.0.0.31"

RELEASE_DATE = "15.Oct.2026"

DEVELOPER = "Yawhackka"

EMAIL = "yawhackka@gmail.com"

ARCHITECTURE = "x86_64"

DESCRIPTION = "YouTube video downloader"

# AppImageTool Download URL
APPIMAGETOOL_URL = (
    "https://github.com/AppImage/AppImageKit/releases/download/"
    "continuous/appimagetool-x86_64.AppImage"
)

# AppImage Type-2 Standalone Runtime (FUSE မလိုဘဲ run နိုင်သော Runtime)
RUNTIME_URL = (
    "https://github.com/AppImage/type2-runtime/releases/download/"
    "continuous/runtime-x86_64"
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DIST_DIR = PROJECT_DIR / "YawStar_U-Tube_Downloader"

EXECUTABLE = DIST_DIR / APP_EXECUTABLE

INTERNAL_DIR = DIST_DIR / "_internal"

ICON = PROJECT_DIR / "app_icon.png"

APPIMAGETOOL_PATH = PROJECT_DIR / "appimagetool-x86_64.AppImage"

RUNTIME_PATH = PROJECT_DIR / "runtime-x86_64"


# ============================================================
# APPIMAGE BUILD PATHS
# ============================================================

BUILD_DIR = PROJECT_DIR / "appimage-build"

APP_DIR = BUILD_DIR / f"{PACKAGE_NAME}.AppDir"

# AppDir / usr / bin
USR_BIN_DIR = APP_DIR / "usr" / "bin"


# ============================================================
# FINAL PACKAGE
# ============================================================

OUTPUT_APPIMAGE = (
    DIST_DIR / f"{APP_EXECUTABLE}-{VERSION}-{ARCHITECTURE}.AppImage"
)


# ============================================================
# TERMINAL COLORS
# ============================================================

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"


def info(message: str):
    print(f"{CYAN}[INFO]{RESET} {message}")


def success(message: str):
    print(f"{GREEN}[OK]{RESET} {message}")


def warning(message: str):
    print(f"{YELLOW}[WARNING]{RESET} {message}")


def error(message: str):
    print(f"{RED}[ERROR]{RESET} {message}")


def run(command, env=None):
    """Execute an external command."""
    print()
    print(f"{BOLD}>>> {' '.join(map(str, command))}{RESET}")
    print()

    subprocess.run(
        command,
        check=True,
        env=env,
    )


def make_executable(path: Path):
    """Add executable permissions to a file."""
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# ============================================================
# CHECK PLATFORM
# ============================================================

def check_platform():
    if sys.platform != "linux":
        raise RuntimeError("This script must be run on Linux.")

    machine = platform.machine().lower()
    if machine not in ("x86_64", "amd64"):
        raise RuntimeError(f"Unsupported architecture: {machine}")

    success("Linux x86_64 detected.")


# ============================================================
# DOWNLOAD APPIMAGETOOL & TYPE-2 RUNTIME
# ============================================================

def ensure_tools():
    """Download appimagetool and type-2 runtime if they don't exist."""

    # 1. appimagetool
    if not APPIMAGETOOL_PATH.exists():
        info("Downloading appimagetool-x86_64.AppImage from GitHub...")
        try:
            urllib.request.urlretrieve(APPIMAGETOOL_URL, APPIMAGETOOL_PATH)
            make_executable(APPIMAGETOOL_PATH)
            success("Downloaded appimagetool-x86_64.AppImage successfully.")
        except Exception as exc:
            if APPIMAGETOOL_PATH.exists():
                APPIMAGETOOL_PATH.unlink()
            raise RuntimeError(f"Failed to download appimagetool: {exc}")
    else:
        success("appimagetool-x86_64.AppImage found.")
        make_executable(APPIMAGETOOL_PATH)

    # 2. runtime-x86_64 (Type 2 Standalone Runtime)
    info("Checking AppImage Type-2 runtime...")

    # ဖိုင်အဟောင်း/ဆွဲလက်စအမှားရှိရင် ဖျက်ပစ်ပြီး အသစ်ဆွဲမည်
    if RUNTIME_PATH.exists():
        RUNTIME_PATH.unlink()

    info("Downloading Type-2 runtime-x86_64 (No FUSE required)...")
    try:
        urllib.request.urlretrieve(RUNTIME_URL, RUNTIME_PATH)
        make_executable(RUNTIME_PATH)
        success("Downloaded Type-2 runtime-x86_64 successfully.")
    except Exception as exc:
        if RUNTIME_PATH.exists():
            RUNTIME_PATH.unlink()
        raise RuntimeError(f"Failed to download runtime-x86_64: {exc}")


# ============================================================
# VALIDATE PYINSTALLER BUILD
# ============================================================

def validate_project():
    info("Checking existing PyInstaller build...")

    if not DIST_DIR.exists():
        raise RuntimeError(f"dist directory not found: {DIST_DIR}")

    if not EXECUTABLE.exists():
        raise RuntimeError(f"PyInstaller executable not found: {EXECUTABLE}")

    if not INTERNAL_DIR.exists() or not INTERNAL_DIR.is_dir():
        raise RuntimeError(f"PyInstaller _internal directory invalid: {INTERNAL_DIR}")

    if not ICON.exists():
        raise RuntimeError(f"Application icon not found: {ICON}")

    success("PyInstaller executable found.")
    success("PyInstaller _internal found.")
    success("Application icon found.")


# ============================================================
# CLEAN BUILD DIRECTORY
# ============================================================

def clean_build():
    info("Cleaning previous AppImage build...")

    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)

    USR_BIN_DIR.mkdir(parents=True, exist_ok=True)
    success("AppDir structure created.")


# ============================================================
# COPY APPLICATION FILES
# ============================================================

def copy_application():
    info("Copying PyInstaller files to AppDir...")

    target_executable = USR_BIN_DIR / APP_EXECUTABLE
    shutil.copy2(EXECUTABLE, target_executable)
    make_executable(target_executable)

    target_internal = USR_BIN_DIR / "_internal"
    shutil.copytree(INTERNAL_DIR, target_internal, symlinks=True)

    success("Copied binary and _internal dependencies.")


# ============================================================
# CREATE DESKTOP FILE & ICON
# ============================================================

def create_desktop_and_icon():
    info("Creating .desktop file and copying icon...")

    desktop_file = APP_DIR / f"{PACKAGE_NAME}.desktop"
    desktop_file.write_text(
        f"""[Desktop Entry]
Type=Application
Name={DISPLAY_NAME}
Comment={DESCRIPTION}
Exec={APP_EXECUTABLE}
Icon={PACKAGE_NAME}
Terminal=false
Categories=Utility;
StartupNotify=true
X-AppImage-Version={VERSION}
""",
        encoding="utf-8",
    )

    shutil.copy2(ICON, APP_DIR / f"{PACKAGE_NAME}.png")

    dir_icon = APP_DIR / ".DirIcon"
    if dir_icon.exists() or dir_icon.is_symlink():
        dir_icon.unlink()
    dir_icon.symlink_to(f"{PACKAGE_NAME}.png")

    success("Created .desktop file and icons.")


# ============================================================
# CREATE APPRUN LAUNCHER
# ============================================================

def create_apprun():
    info("Creating AppRun script...")

    apprun = APP_DIR / "AppRun"
    apprun.write_text(
        f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${{0}}")")"
export PATH="${{HERE}}/usr/bin:${{PATH}}"
export LD_LIBRARY_PATH="${{HERE}}/usr/bin/_internal:${{LD_LIBRARY_PATH}}"
exec "${{HERE}}/usr/bin/{APP_EXECUTABLE}" "$@"
""",
        encoding="utf-8",
    )

    make_executable(apprun)
    success("AppRun script created.")


# ============================================================
# BUILD APPIMAGE
# ============================================================

def build_appimage():
    info("Building AppImage package with Type-2 Runtime...")

    if OUTPUT_APPIMAGE.exists():
        OUTPUT_APPIMAGE.unlink()

    env = os.environ.copy()
    env["ARCH"] = "x86_64"
    env["APPIMAGE_EXTRACT_AND_RUN"] = "1"

    # appimagetool command referencing Type-2 runtime
    cmd = [
        str(APPIMAGETOOL_PATH),
        "--appimage-extract-and-run",
        "--runtime-file",
        str(RUNTIME_PATH),
        str(APP_DIR),
        str(OUTPUT_APPIMAGE),
    ]

    run(cmd, env=env)

    if not OUTPUT_APPIMAGE.exists():
        raise RuntimeError("appimagetool completed but .AppImage file was not created.")

    size = OUTPUT_APPIMAGE.stat().st_size / 1024 / 1024

    print()
    print("=" * 60)
    print(f"{GREEN}{BOLD}APPIMAGE BUILD SUCCESSFUL{RESET}")
    print("=" * 60)
    print()
    print("Package:")
    print(f"  {OUTPUT_APPIMAGE}")
    print()
    print("Size:")
    print(f"  {size:.2f} MB")
    print()
    print("Run with:")
    print(f"  chmod +x '{OUTPUT_APPIMAGE}'")
    print(f"  ./'{OUTPUT_APPIMAGE.name}'")
    print()


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 60)
    print(f"{BOLD}YawStar U-Tube Downloader{RESET}")
    print("PyInstaller → Standalone AppImage Builder (No-FUSE)")
    print("=" * 60)
    print()

    try:
        check_platform()
        ensure_tools()
        validate_project()
        clean_build()
        copy_application()
        create_desktop_and_icon()
        create_apprun()
        build_appimage()

    except KeyboardInterrupt:
        print()
        warning("Build cancelled by user.")
        sys.exit(130)

    except Exception as exc:
        print()
        print("=" * 60)
        error("APPIMAGE BUILD FAILED")
        print("=" * 60)
        print()
        error(str(exc))
        print()
        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()