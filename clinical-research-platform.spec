# -*- mode: python ; coding: utf-8 -*-
datas = [
    ('/usr/lib/x86_64-linux-gnu/qt5/plugins', 'PyQt5/Qt/plugins'),
    ('/usr/share/qt5/translations', 'PyQt5/Qt/translations')  # 如果找到翻译文件路径
]

binaries = []


a = Analysis(
    ['clinical-research-platform.py'],
    pathex=[],
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
    name='clinical-research-platform',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
