# -*- mode: python -*-
import os
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

# ─── collect all files under gui/ ─────────────────────────────────────────────
datas = []
gui_dir = Path('gui')
if gui_dir.is_dir():
    for src in gui_dir.rglob('*'):
        if src.is_file():
            # place each file under the same gui/... path inside the bundle
            rel_parent = src.relative_to(gui_dir).parent
            dest_dir = os.path.join('gui', str(rel_parent))
            datas.append((str(src), dest_dir))
# ────────────────────────────────────────────────────────────────────────────────

a = Analysis(
    ['code2clip.py'],
    pathex=['.'],       # look in repo root
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
    console=False,   # windowed GUI
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
