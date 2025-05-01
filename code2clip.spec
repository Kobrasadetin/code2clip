# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['code2clip.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('gui/icon_32.png', 'gui'),
        ('gui/icon_48.png', 'gui'),
        ('gui/icon_256.png', 'gui'),
        ('gui/splash.png')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='code2clip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    windowed=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='code2clip'
)
