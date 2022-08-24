# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = pyi_crypto.PyiBlockCipher(key='9EEE0694C7A3922E')



additional_data_files = [
    ("Libs/UI/Raw/*.*", "Libs/UI/Raw/"),
    ("Libs/Storage/DEFAULT_VALUES.json", "Libs/Storage/"),
    ("Libs/UI/icons/*.*", "Libs/UI/icons"),
    ("Libs/Files/DataFiles/*", "Libs/Files/DataFiles/"),
    ("config.ini", "."),
    ("app.ico", ".")
]

hidden_imports = ["talib", "talib.stream"]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=additional_data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tk", "tcl"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TradeXCB-OMS',
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
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='TradeXCB-OMS',
)