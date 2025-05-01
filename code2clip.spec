# -*- mode: python -*-
import os
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE

block_cipher = None

# ─── collect all files ────────────────────────────────────────────────────
datas = []
gui_dir = Path('gui')
if gui_dir.is_dir():
    for src in gui_dir.rglob('*'):
        if src.is_file():
            # put each file under the same gui/... path inside the bundle
            rel_parent = src.relative_to(gui_dir).parent
            dest_dir = os.path.join('gui', str(rel_parent))
            datas.append((str(src), dest_dir))
version_file = Path('code2clip_version.txt')
if version_file.is_file():
    datas.append((str(version_file), '.'))
# ──────────────────────────────────────────────────────────────────────────

a = Analysis(
    ['code2clip.py'],
    pathex=['.'],
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
    a.binaries,       # <-- include all binary dependencies
    a.zipfiles,
    a.datas,          # <-- include our gui/ images in the one‐file
    name='code2clip',
    debug=False,
    strip=False,
    upx=True,
    console=False,    # <-- GUI app
    windowed=True,
)
