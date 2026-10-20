#!/usr/bin/env python3

"""
Build a portable .tar.gz distributable package from an existing PyInstaller build.

Expected structure:

    my_proj/
    ├── build_tar_gz.py
    └── amd64/
        └── YawStar_U-Tube_Downloader/
            ├── YawStar_U-Tube_Downloader
            └── _internal/
                ├── ...
                └── ...

Output:

    ../Released/
        YawStar_U-Tube_Downloader-1.0.0.31-x86_64.tar.gz
"""

from __future__ import annotations

import platform
import shutil
import stat
import subprocess
import sys
import tarfile
from pathlib import Path


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_EXECUTABLE = "YawStar_U-Tube_Downloader"

PACKAGE_NAME = "yawstar-u-tube-downloader"

DISPLAY_NAME = "YawStar U-Tube Downloader"

VERSION = "1.0.0.31"

RELEASE_DATE = "17.Oct.2026"

DEVELOPER = "Yawhackka"

EMAIL = "yawhackka@gmail.com"

ARCHITECTURE = "x86_64"

DESCRIPTION = "YouTube video downloader"


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DIST_DIR = PROJECT_DIR / "amd64" / "YawStar_U-Tube_Downloader"

EXECUTABLE = DIST_DIR / APP_EXECUTABLE

INTERNAL_DIR = DIST_DIR / "_internal"


# ============================================================
# FINAL PACKAGE
# ============================================================

OUTPUT_TAR = (
    PROJECT_DIR.parent
    / "Released"
    / f"{APP_EXECUTABLE}-{VERSION}-{ARCHITECTURE}.tar.gz"
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

    success("PyInstaller executable found.")
    success("PyInstaller _internal found.")


# ============================================================
# BUILD TAR.GZ ARCHIVE
# ============================================================

def build_tarball():
    info("Building portable .tar.gz archive...")

    # Ensure parent Released directory exists
    OUTPUT_TAR.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_TAR.exists():
        OUTPUT_TAR.unlink()

    # Ensure binary has correct executable permissions
    make_executable(EXECUTABLE)
    success(f"Executable permissions applied to {APP_EXECUTABLE}.")

    info("Compressing directory into .tar.gz...")
    
    # Create tar.gz archive preserving internal folder structure cleanly
    with tarfile.open(OUTPUT_TAR, "w:gz") as tar:
        # Add DIST_DIR contents under a root folder name matching APP_EXECUTABLE
        tar.add(DIST_DIR, arcname=APP_EXECUTABLE)

    if not OUTPUT_TAR.exists():
        raise RuntimeError("Tar archive creation completed but .tar.gz file was not created.")

    size = OUTPUT_TAR.stat().st_size / 1024 / 1024

    print()
    print("=" * 60)
    print(f"{GREEN}{BOLD}TAR.GZ PACKAGE BUILD SUCCESSFUL{RESET}")
    print("=" * 60)
    print()
    print("Package:")
    print(f"  {OUTPUT_TAR}")
    print()
    print("Size:")
    print(f"  {size:.2f} MB")
    print()
    print("Extract with:")
    print(f"  tar -xzf '{OUTPUT_TAR.name}'")
    print()


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 60)
    print(f"{BOLD}{DISPLAY_NAME}{RESET}")
    print("PyInstaller → Portable Tarball (.tar.gz) Builder")
    print("=" * 60)
    print()

    try:
        check_platform()
        validate_project()
        build_tarball()

    except KeyboardInterrupt:
        print()
        warning("Build cancelled by user.")
        sys.exit(130)

    except Exception as exc:
        print()
        print("=" * 60)
        error("TAR.GZ BUILD FAILED")
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
