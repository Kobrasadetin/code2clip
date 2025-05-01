# -*- mode: python -*-
import sys
from PyInstaller.utils.hooks import Tree
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

# Collect everything under gui/ into a gui/ directory in the bundle
datas = Tree('gui', prefix='gui')

a = Analysis(
    ['code2clip.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='code2clip',
    debug=False,
    strip=False,
    upx=True,
    console=False,    # windowed GUI
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
