# -*- mode: python -*-
import sys
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

# ─── Collect all files under gui/ ──────────────────────────────────────────────
datas = []
gui_dir = Path(__file__).parent / 'gui'
for src in gui_dir.rglob('*'):
    if src.is_file():
        # dest_dir inside the bundle will be 'gui/' plus any subfolder
        rel = src.relative_to(gui_dir)
        dest = Path('gui') / rel.parent
        datas.append(( str(src), str(dest) ))
# ────────────────────────────────────────────────────────────────────────────────

a = Analysis(
    ['code2clip.py'],
    pathex=[str(Path(__file__).parent)],
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
    console=False,      # GUI app
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
