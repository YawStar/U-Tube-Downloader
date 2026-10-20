#!/usr/bin/env python3

"""
Build a Debian .deb package from an existing PyInstaller build.

Expected structure:

    Linux/
    ├── build_deb.py
    ├── app_icon.png
    └── YawStar_U-Tube_Downloader/
        ├── YawStar_U-Tube_Downloader
        └── _internal/
            ├── ...
            └── ...

The PyInstaller executable keeps its original name:

    YawStar_U-Tube_Downloader

The Debian package name uses a valid Debian package name:

    yawstar-u-tube-downloader

Output:

    ../Released/
        yawstar-u-tube-downloader_1.0.0.31_amd64.deb
"""

from __future__ import annotations

import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

# Actual PyInstaller executable name.
APP_EXECUTABLE = "YawStar_U-Tube_Downloader"

# Valid Debian package name.
PACKAGE_NAME = "yawstar-u-tube-downloader"

# Name shown in application menus.
DISPLAY_NAME = "YawStar U-Tube Downloader"

VERSION = "1.0.0.31"

RELEASE_DATE = "15.Oct.2026"

DEVELOPER = "Yawhackka"

EMAIL = "yawhackka@gmail.com"

ARCHITECTURE = "amd64"

SECTION = "utils"

PRIORITY = "optional"

MAINTAINER = f"{DEVELOPER} <{EMAIL}>"

HOMEPAGE = f"https://github.com/{DEVELOPER.lower()}/{PACKAGE_NAME}"

DESCRIPTION = "YouTube video downloader"


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DIST_DIR = PROJECT_DIR / "amd64" / "YawStar_U-Tube_Downloader"

# Existing PyInstaller executable.
EXECUTABLE = (
    DIST_DIR
    / APP_EXECUTABLE
)

# Existing PyInstaller dependencies.
INTERNAL_DIR = (
    DIST_DIR
    / "_internal"
)

# Application icon.
ICON = (
    PROJECT_DIR
    / "app_icon.png"
)


# ============================================================
# DEBIAN BUILD PATHS
# ============================================================

BUILD_DIR = (
    PROJECT_DIR
    / "deb-build"
)

DEB_ROOT = (
    BUILD_DIR
    / "package"
)

DEBIAN_DIR = (
    DEB_ROOT
    / "DEBIAN"
)

# Actual application files.
INSTALL_DIR = (
    DEB_ROOT
    / "opt"
    / APP_EXECUTABLE
)

# /usr/bin launcher.
BIN_DIR = (
    DEB_ROOT
    / "usr"
    / "bin"
)

# Desktop application entry.
APPLICATIONS_DIR = (
    DEB_ROOT
    / "usr"
    / "share"
    / "applications"
)

# Application icon.
ICON_DIR = (
    DEB_ROOT
    / "usr"
    / "share"
    / "icons"
    / "hicolor"
    / "256x256"
    / "apps"
)


# ============================================================
# FINAL PACKAGE
# ============================================================

OUTPUT_DEB = (
    PROJECT_DIR.parent
    / "Released"
    / (
        f"{PACKAGE_NAME}_"
        f"{VERSION}_"
        f"{ARCHITECTURE}.deb"
    )
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
    print(
        f"{CYAN}[INFO]{RESET} "
        f"{message}"
    )


def success(message: str):
    print(
        f"{GREEN}[OK]{RESET} "
        f"{message}"
    )


def warning(message: str):
    print(
        f"{YELLOW}[WARNING]{RESET} "
        f"{message}"
    )


def error(message: str):
    print(
        f"{RED}[ERROR]{RESET} "
        f"{message}"
    )


# ============================================================
# RUN COMMAND
# ============================================================

def run(command):
    """
    Execute an external command.
    """

    print()
    print(
        f"{BOLD}>>> "
        f"{' '.join(map(str, command))}"
        f"{RESET}"
    )
    print()

    subprocess.run(
        command,
        check=True,
    )


# ============================================================
# MAKE EXECUTABLE
# ============================================================

def make_executable(path: Path):
    """
    Add executable permissions to a file.
    """

    mode = path.stat().st_mode

    path.chmod(
        mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )


# ============================================================
# CHECK PACKAGE NAME
# ============================================================

def validate_package_name():
    """
    Validate the Debian package name.
    """

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789"
        "-+."
    )

    if not PACKAGE_NAME:

        raise RuntimeError(
            "Debian package name is empty."
        )

    invalid = [
        char
        for char in PACKAGE_NAME
        if char not in allowed
    ]

    if invalid:

        raise RuntimeError(
            "Invalid Debian package name:\n\n"
            f"    {PACKAGE_NAME}\n\n"
            f"Invalid characters: {invalid}\n\n"
            "Allowed characters are:\n"
            "    lowercase a-z\n"
            "    0-9\n"
            "    -\n"
            "    +\n"
            "    ."
        )

    if PACKAGE_NAME[0] in ".-":

        raise RuntimeError(
            "Debian package name cannot start "
            "with '.' or '-'."
        )

    success(
        f"Valid Debian package name: "
        f"{PACKAGE_NAME}"
    )


# ============================================================
# CHECK PLATFORM
# ============================================================

def check_platform():

    if sys.platform != "linux":

        raise RuntimeError(
            "This script must be run on Linux."
        )

    machine = (
        platform.machine()
        .lower()
    )

    if machine not in (
        "x86_64",
        "amd64",
    ):

        raise RuntimeError(
            f"Unsupported architecture: "
            f"{machine}\n\n"
            "This script currently creates "
            "amd64 Debian packages."
        )

    success(
        "Linux x86_64 detected."
    )


# ============================================================
# CHECK DPKG-DEB
# ============================================================

def check_dpkg_deb():

    if shutil.which("dpkg-deb") is None:

        raise RuntimeError(
            "dpkg-deb is not installed.\n\n"
            "Install it with:\n\n"
            "    sudo apt update\n"
            "    sudo apt install -y dpkg"
        )

    success(
        "dpkg-deb found."
    )


# ============================================================
# VALIDATE PYINSTALLER BUILD
# ============================================================

def validate_project():

    info(
        "Checking existing PyInstaller build..."
    )

    if not DIST_DIR.exists():

        raise RuntimeError(
            f"dist directory not found:\n"
            f"{DIST_DIR}"
        )

    if not EXECUTABLE.exists():

        raise RuntimeError(
            "PyInstaller executable not found:\n\n"
            f"    {EXECUTABLE}\n\n"
            "Expected:\n\n"
            "    dist/\n"
            f"    ├── {APP_EXECUTABLE}\n"
            "    └── _internal/"
        )

    if not INTERNAL_DIR.exists():

        raise RuntimeError(
            "PyInstaller _internal directory "
            "not found:\n\n"
            f"    {INTERNAL_DIR}"
        )

    if not INTERNAL_DIR.is_dir():

        raise RuntimeError(
            f"_internal is not a directory:\n"
            f"{INTERNAL_DIR}"
        )

    if not ICON.exists():

        raise RuntimeError(
            "Application icon not found:\n\n"
            f"    {ICON}\n\n"
            "Put app_icon.png beside build_deb.py."
        )

    success(
        "PyInstaller executable found."
    )

    success(
        "PyInstaller _internal found."
    )

    success(
        "Application icon found."
    )


# ============================================================
# CLEAN BUILD DIRECTORY
# ============================================================

def clean_build():

    info(
        "Cleaning previous Debian build..."
    )

    if DEB_ROOT.exists():

        shutil.rmtree(
            DEB_ROOT
        )

    DEBIAN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    INSTALL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    BIN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    APPLICATIONS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ICON_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    success(
        "Debian build directories created."
    )


# ============================================================
# COPY PYINSTALLER APPLICATION
# ============================================================

def copy_application():

    info(
        "Copying PyInstaller executable..."
    )

    target_executable = (
        INSTALL_DIR
        / APP_EXECUTABLE
    )

    shutil.copy2(
        EXECUTABLE,
        target_executable,
    )

    make_executable(
        target_executable
    )

    success(
        f"Copied {APP_EXECUTABLE}"
    )

    target_internal = (
        INSTALL_DIR
        / "_internal"
    )

    info(
        "Copying _internal directory..."
    )

    shutil.copytree(
        INTERNAL_DIR,
        target_internal,
        symlinks=True,
    )

    success(
        "Copied _internal directory."
    )


# ============================================================
# CREATE /USR/BIN LAUNCHER
# ============================================================

def create_launcher():

    info(
        "Creating /usr/bin launcher..."
    )

    launcher = (
        BIN_DIR
        / APP_EXECUTABLE
    )

    launcher.write_text(
        f"""#!/bin/sh

exec /opt/{APP_EXECUTABLE}/{APP_EXECUTABLE} "$@"
""",
        encoding="utf-8",
    )

    make_executable(
        launcher
    )

    success(
        f"Created /usr/bin/{APP_EXECUTABLE}"
    )


# ============================================================
# CREATE DESKTOP FILE
# ============================================================

def create_desktop_file():

    info(
        "Creating desktop entry..."
    )

    desktop_file = (
        APPLICATIONS_DIR
        / f"{PACKAGE_NAME}.desktop"
    )

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
""",
        encoding="utf-8",
    )

    success(
        "Desktop entry created."
    )


# ============================================================
# INSTALL ICON
# ============================================================

def install_icon():

    info(
        "Installing application icon..."
    )

    target_icon = (
        ICON_DIR
        / f"{PACKAGE_NAME}.png"
    )

    shutil.copy2(
        ICON,
        target_icon,
    )

    success(
        "Application icon installed."
    )


# ============================================================
# CREATE CONTROL FILE
# ============================================================

def create_control_file():

    info(
        "Creating Debian control file..."
    )

    control_file = (
        DEBIAN_DIR
        / "control"
    )

    control_file.write_text(
        f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Section: {SECTION}
Priority: {PRIORITY}
Architecture: {ARCHITECTURE}
Maintainer: {MAINTAINER}
Homepage: {HOMEPAGE}
Description: {DISPLAY_NAME}
 {DESCRIPTION}
 Built with PySide6 and packaged with PyInstaller.
 Released on {RELEASE_DATE}.
""",
        encoding="utf-8",
    )

    success(
        "Debian control file created."
    )


# ============================================================
# CREATE POSTINST
# ============================================================

def create_postinst():

    info(
        "Creating post-install script..."
    )

    postinst = (
        DEBIAN_DIR
        / "postinst"
    )

    postinst.write_text(
        """#!/bin/sh
set -e

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database \
        /usr/share/applications \
        >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache \
        -f \
        -t \
        /usr/share/icons/hicolor \
        >/dev/null 2>&1 || true
fi

exit 0
""",
        encoding="utf-8",
    )

    make_executable(
        postinst
    )

    success(
        "Post-install script created."
    )


# ============================================================
# CREATE PRERM
# ============================================================

def create_prerm():

    info(
        "Creating pre-removal script..."
    )

    prerm = (
        DEBIAN_DIR
        / "prerm"
    )

    prerm.write_text(
        """#!/bin/sh
set -e

exit 0
""",
        encoding="utf-8",
    )

    make_executable(
        prerm
    )

    success(
        "Pre-removal script created."
    )


# ============================================================
# BUILD DEB
# ============================================================

def build_deb():

    info(
        "Building Debian package..."
    )

    # Ensure parent Released directory exists
    OUTPUT_DEB.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_DEB.exists():

        info(
            "Removing previous .deb..."
        )

        OUTPUT_DEB.unlink()

    run([
        "dpkg-deb",
        "--build",
        "--root-owner-group",
        str(DEB_ROOT),
        str(OUTPUT_DEB),
    ])

    if not OUTPUT_DEB.exists():

        raise RuntimeError(
            "dpkg-deb completed but the .deb "
            "file was not created."
        )

    size = (
        OUTPUT_DEB.stat().st_size
        / 1024
        / 1024
    )

    print()
    print("=" * 60)

    print(
        f"{GREEN}{BOLD}"
        "DEB BUILD SUCCESSFUL"
        f"{RESET}"
    )

    print("=" * 60)
    print()

    print(
        "Package:"
    )

    print(
        f"  {OUTPUT_DEB}"
    )

    print()

    print(
        f"Size:"
    )

    print(
        f"  {size:.2f} MB"
    )

    print()

    print(
        "Install with:"
    )

    print(
        f"  sudo apt install "
        f"'{OUTPUT_DEB}'"
    )

    print()

    print(
        "Or:"
    )

    print(
        f"  sudo dpkg -i "
        f"'{OUTPUT_DEB}'"
    )

    print()


# ============================================================
# SHOW PACKAGE STRUCTURE
# ============================================================

def show_structure():

    print(
        "=" * 60
    )

    print(
        "PACKAGE STRUCTURE"
    )

    print(
        "=" * 60
    )

    print()

    print(
        f"/opt/{APP_EXECUTABLE}/"
    )

    print(
        f"├── {APP_EXECUTABLE}"
    )

    print(
        "└── _internal/"
    )

    print()

    print(
        "/usr/bin/"
    )

    print(
        f"└── {APP_EXECUTABLE}"
    )

    print()

    print(
        "/usr/share/applications/"
    )

    print(
        f"└── {PACKAGE_NAME}.desktop"
    )

    print()

    print(
        "/usr/share/icons/hicolor/"
    )

    print(
        "└── 256x256/apps/"
        f"{PACKAGE_NAME}.png"
    )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "=" * 60
    )

    print(
        f"{BOLD}"
        "YawStar U-Tube Downloader"
        f"{RESET}"
    )

    print(
        "PyInstaller → Debian Package Builder"
    )

    print(
        "=" * 60
    )

    print()

    try:

        check_platform()

        validate_package_name()

        check_dpkg_deb()

        validate_project()

        clean_build()

        copy_application()

        create_launcher()

        create_desktop_file()

        install_icon()

        create_control_file()

        create_postinst()

        create_prerm()

        build_deb()

        show_structure()

    except KeyboardInterrupt:

        print()

        warning(
            "Build cancelled by user."
        )

        sys.exit(130)

    except Exception as exc:

        print()

        print(
            "=" * 60
        )

        error(
            "DEB BUILD FAILED"
        )

        print(
            "=" * 60
        )

        print()

        error(
            str(exc)
        )

        print()

        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
