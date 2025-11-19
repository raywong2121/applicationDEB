# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from branding_assets import write_dr_r_icon

project_dir = Path(__file__).resolve().parent
icon_path = project_dir / 'dr-r-icon.png'
write_dr_r_icon(icon_path)

datas = [
    ('/usr/lib/x86_64-linux-gnu/qt5/plugins', 'PyQt5/Qt/plugins'),
    ('/usr/share/qt5/translations', 'PyQt5/Qt/translations'),
    (str(icon_path), '.'),
]

binaries = []


a = Analysis(
    ['clinical-research-platform.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=['PyQt5.QtWebEngineWidgets'],
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
    a.binaries,
    a.datas,
    [],
    name='dr-r',
    icon=str(icon_path),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
