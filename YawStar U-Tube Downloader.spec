# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('F:/YawStar/PROJECTS/YawStar U-Tube Dowloader/Python/U-Tube-Downloader/ui/settings_dialog.ui', 'ui')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('desktop_notifier')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['F:/YawStar/PROJECTS/YawStar U-Tube Dowloader/Python/U-Tube-Downloader/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YawStar U-Tube Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='F:/YawStar/PROJECTS/YawStar U-Tube Dowloader/Python/U-Tube-Downloader/dist/version-file.txt',
    icon=['F:/YawStar/PROJECTS/YawStar U-Tube Dowloader/Python/U-Tube-Downloader/dist/app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='YawStar U-Tube Downloader',
)
