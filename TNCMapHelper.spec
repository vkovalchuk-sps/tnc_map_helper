# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules


bs4_hidden_imports = collect_submodules('bs4')
openpyxl_hidden_imports = collect_submodules('openpyxl')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('application/templates/*.xml', 'application/templates'),
        ('application/templates/*.xtl', 'application/templates'),
        ('application/icon.png', 'application'),
        ('application/database/database.db', 'application/database'),
        ('application/.config', 'application/.config'),
    ],
    hiddenimports=bs4_hidden_imports + openpyxl_hidden_imports,
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
    name='TnCMapHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='application/icon.png',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TnCMapHelper',
)
