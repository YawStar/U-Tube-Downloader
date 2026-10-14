#!/usr/bin/env python3

"""
Build an RPM package (.rpm) from an existing PyInstaller build using rpmbuild (Native).
Auto-detects and installs missing system dependency (rpmbuild).

Expected structure:

    my_proj/
    ├── build_rpm.py
    ├── app_icon.png
    └── YawStar_U-Tube_Downloader/
        ├── YawStar_U-Tube_Downloader
        └── _internal/
            ├── ...
            └── ...

Output:

    YawStar_U-Tube_Downloader/
        yawstar-u-tube-downloader-1.0.0.31.x86_64.rpm
"""

from __future__ import annotations

import os
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
RELEASE = "1"
ARCHITECTURE = "x86_64"
DESCRIPTION = "YouTube video downloader"
LICENSE = "MIT"
URL = "https://github.com/Yawhackka"

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / "YawStar_U-Tube_Downloader"
EXECUTABLE = DIST_DIR / APP_EXECUTABLE
INTERNAL_DIR = DIST_DIR / "_internal"
ICON = PROJECT_DIR / "app_icon.png"

# ============================================================
# RPM BUILD PATHS (rpmbuild standard directories)
# ============================================================

BUILD_DIR = PROJECT_DIR / "rpm-build"
STAGE_DIR = BUILD_DIR / "stage"

# ============================================================
# FINAL OUTPUT
# ============================================================

OUTPUT_RPM = DIST_DIR / f"{PACKAGE_NAME}-{VERSION}-{RELEASE}.{ARCHITECTURE}.rpm"

# ============================================================
# TERMINAL COLORS
# ============================================================

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"


def info(msg: str):
    print(f"{CYAN}[INFO]{RESET} {msg}")


def success(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")


def warning(msg: str):
    print(f"{YELLOW}[WARNING]{RESET} {msg}")


def error(msg: str):
    print(f"{RED}[ERROR]{RESET} {msg}")


def make_executable(path: Path):
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_dependencies():
    """Detect package manager and auto-install rpmbuild."""
    info("Checking and installing required dependencies (rpmbuild)...")

    has_apt = shutil.which("apt") is not None
    has_dnf = shutil.which("dnf") is not None
    has_yum = shutil.which("yum") is not None

    if has_apt:
        info("Debian/Ubuntu/Kali environment detected.")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "rpm", "build-essential"], check=True)
    elif has_dnf:
        info("Fedora/RHEL/CentOS environment detected (dnf).")
        subprocess.run(["sudo", "dnf", "install", "-y", "rpm-build", "gcc", "make"], check=True)
    elif has_yum:
        info("CentOS/RHEL environment detected (yum).")
        subprocess.run(["sudo", "yum", "install", "-y", "rpm-build", "gcc", "make"], check=True)
    else:
        raise RuntimeError("Unsupported Linux distribution. Package manager not found.")


def check_env():
    if sys.platform != "linux":
        raise RuntimeError("RPM building must be run on Linux.")

    if not shutil.which("rpmbuild"):
        warning("Missing dependency detected (rpmbuild). Starting auto-install...")
        install_dependencies()

    if not shutil.which("rpmbuild"):
        raise RuntimeError("Failed to set up environment dependencies (rpmbuild missing).")

    success("Environment check passed (rpmbuild ready).")


def validate_sources():
    info("Checking PyInstaller build outputs...")
    if not EXECUTABLE.exists():
        raise RuntimeError(f"Executable not found: {EXECUTABLE}")
    if not INTERNAL_DIR.exists():
        raise RuntimeError(f"_internal directory not found: {INTERNAL_DIR}")
    if not ICON.exists():
        raise RuntimeError(f"Icon file not found: {ICON}")
    success("All required build assets found.")


def prepare_staging():
    info("Preparing staging filesystem...")

    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)

    usr_bin = STAGE_DIR / "usr" / "bin"
    opt_app = STAGE_DIR / "opt" / PACKAGE_NAME
    desktop_dir = STAGE_DIR / "usr" / "share" / "applications"
    icon_dir = STAGE_DIR / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"

    usr_bin.mkdir(parents=True, exist_ok=True)
    opt_app.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)
    icon_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy Executable and _internal to /opt/package-name
    target_exec = opt_app / APP_EXECUTABLE
    shutil.copy2(EXECUTABLE, target_exec)
    make_executable(target_exec)

    shutil.copytree(INTERNAL_DIR, opt_app / "_internal", symlinks=True)

    # 2. Create wrapper in /usr/bin/
    wrapper = usr_bin / PACKAGE_NAME
    wrapper.write_text(
        f"""#!/bin/sh
exec /opt/{PACKAGE_NAME}/{APP_EXECUTABLE} "$@"
""",
        encoding="utf-8",
    )
    make_executable(wrapper)

    # 3. Create .desktop file
    desktop_file = desktop_dir / f"{PACKAGE_NAME}.desktop"
    desktop_file.write_text(
        f"""[Desktop Entry]
Type=Application
Name={DISPLAY_NAME}
Comment={DESCRIPTION}
Exec=/usr/bin/{PACKAGE_NAME}
Icon={PACKAGE_NAME}
Terminal=false
Categories=Utility;
StartupNotify=true
""",
        encoding="utf-8",
    )

    # 4. Copy Icon
    shutil.copy2(ICON, icon_dir / f"{PACKAGE_NAME}.png")

    success("Filesystem structure staged.")


def build_rpm():
    info("Building RPM package with native rpmbuild...")

    if OUTPUT_RPM.exists():
        OUTPUT_RPM.unlink()

    # Create RPM build workspace folders
    rpmbuild_top = BUILD_DIR / "rpmbuild_workspace"
    for d in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
        (rpmbuild_top / d).mkdir(parents=True, exist_ok=True)

    # Create exact tar.gz of staged files using tarfile module
    archive_name = f"{PACKAGE_NAME}-{VERSION}"
    archive_path = rpmbuild_top / "SOURCES" / f"{archive_name}.tar.gz"
    
    info("Compressing staged files into tar.gz...")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(STAGE_DIR, arcname=archive_name)

    # Create .spec file using template replacement
    spec_template = """
Name:           __PACKAGE_NAME__
Version:        __VERSION__
Release:        __RELEASE__%{?dist}
Summary:        __DESCRIPTION__
License:        __LICENSE__
URL:            __URL__
BuildArch:      __ARCHITECTURE__

Source0:        %{name}-%{version}.tar.gz

%description
__DESCRIPTION__

%prep
%setup -q

%build
# Nothing to build, binaries are pre-compiled

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/__PACKAGE_NAME__
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

# Copy files from extracted source directory
cp -r usr/* %{buildroot}/usr/
cp -r opt/* %{buildroot}/opt/

%files
/opt/__PACKAGE_NAME__
/usr/bin/__PACKAGE_NAME__
/usr/share/applications/__PACKAGE_NAME__.desktop
/usr/share/icons/hicolor/256x256/apps/__PACKAGE_NAME__.png

%changelog
* Wed Oct 14 2026 Yawhackka <support@yawstar> - __VERSION__-__RELEASE__
- Automated RPM package build
"""

    spec_content = (spec_template
        .replace("__PACKAGE_NAME__", PACKAGE_NAME)
        .replace("__VERSION__", VERSION)
        .replace("__RELEASE__", RELEASE)
        .replace("__DESCRIPTION__", DESCRIPTION)
        .replace("__LICENSE__", LICENSE)
        .replace("__URL__", URL)
        .replace("__ARCHITECTURE__", ARCHITECTURE)
    )

    spec_file = rpmbuild_top / "SPECS" / f"{PACKAGE_NAME}.spec"
    spec_file.write_text(spec_content, encoding="utf-8")

    # Run rpmbuild
    cmd = [
        "rpmbuild",
        "-bb",
        "--define", f"_topdir {rpmbuild_top}",
        str(spec_file)
    ]

    print(f"\n{BOLD}>>> {' '.join(cmd)}{RESET}\n")
    subprocess.run(cmd, check=True)

    # Find generated rpm and move to DIST_DIR
    generated_rpms = list(rpmbuild_top.glob(f"RPMS/**/*.rpm"))
    if not generated_rpms:
        raise RuntimeError("rpmbuild completed but .rpm file was not generated.")

    shutil.copy2(generated_rpms[0], OUTPUT_RPM)

    if not OUTPUT_RPM.exists():
        raise RuntimeError("Failed to copy generated RPM to dist directory.")

    size = OUTPUT_RPM.stat().st_size / 1024 / 1024

    print()
    print("=" * 60)
    print(f"{GREEN}{BOLD}RPM PACKAGE BUILD SUCCESSFUL{RESET}")
    print("=" * 60)
    print()
    print("Package:")
    print(f"  {OUTPUT_RPM}")
    print()
    print("Size:")
    print(f"  {size:.2f} MB")
    print()


def main():
    print()
    print("=" * 60)
    print(f"{BOLD}{DISPLAY_NAME}{RESET}")
    print("PyInstaller → Native RPM Package Builder")
    print("=" * 60)
    print()

    try:
        check_env()
        validate_sources()
        prepare_staging()
        build_rpm()
    except KeyboardInterrupt:
        print()
        warning("Build cancelled by user.")
        sys.exit(130)
    except Exception as exc:
        print()
        print("=" * 60)
        error("RPM BUILD FAILED")
        print("=" * 60)
        print()
        error(str(exc))
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
