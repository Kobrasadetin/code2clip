# -*- mode: python -*-
import os, sys
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

# ─── app metadata (readable + used in Win resources) ───────────────────────
APP_NAME = "Code2Clip"
COMPANY = "kobrasadetin"       # shown as "CompanyName" on Windows
COPYRIGHT = "© 2025 kobrasadetin. MIT License"
DESCRIPTION = "Concatenate files/snippets and copy to clipboard."

# Read version (tag or short SHA written by CI step into code2clip_version.txt)
version_str = "0.0.0"
version_file = Path("code2clip_version.txt")
if version_file.is_file():
    version_str = version_file.read_text(encoding="utf-8").strip()

def _parse_ver_tuple(s):
    # Be forgiving: handle "v1.2.3", "1.2.3", or "1.2"
    s = s.lstrip("vV")
    parts = [int(p) for p in s.split(".") if p.isdigit()]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])

filevers = prodvers = _parse_ver_tuple(version_str)

# ─── platform icons ────────────────────────────────────────────────────────
# Windows needs .ico, macOS bundling uses .icns via Info.plist (we still pass icon=None here),
# Linux: icon is not embedded; keep PNGs in gui/ for use at runtime.
icon_file = None
if sys.platform.startswith("win"):
    ico = Path("packaging/windows/code2clip.ico")
    if ico.is_file():
        icon_file = str(ico)

# ─── collect all files from gui/ + version file ────────────────────────────
datas = []
gui_dir = Path("gui")
if gui_dir.is_dir():
    for src in gui_dir.rglob("*"):
        if src.is_file():
            rel_parent = src.relative_to(gui_dir).parent
            dest_dir = os.path.join("gui", str(rel_parent))
            datas.append((str(src), dest_dir))

if version_file.is_file():
    datas.append((str(version_file), "."))

# ─── exclude obvious junk / unused stdlib / Qt parts ───────────────────────
# Keep this conservative; add/remove as you see fit.
excludes = [
    "tests",
    "unittest",
    "pytest",
    "pydoc",
    "tkinter",
    "PyQt5.QtWebEngine",
    "PyQt5.QtWebEngineCore",
    "PyQt5.QtWebEngineWidgets",
    "pip", "setuptools", "wheel", "pkg_resources", "distutils",
    "Crypto", "Cryptodome",
]

a = Analysis(
    ["code2clip.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─── Windows version resources (optional on non-Windows) ───────────────────
win_version = None
if sys.platform.startswith("win"):
    from PyInstaller.utils.win32.versioninfo import (
        VSVersionInfo, StringFileInfo, StringTable, StringStruct,
        VarFileInfo, VarStruct, FixedFileInfo
    )
    win_version = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=filevers,
            prodvers=prodvers,
            mask=0x3f,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,   # VFT_APP
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo([
                StringTable(
                    "040904B0",  # US English, Unicode
                    [
                        StringStruct("CompanyName", COMPANY),
                        StringStruct("FileDescription", DESCRIPTION),
                        StringStruct("FileVersion", ".".join(map(str, filevers))),
                        StringStruct("InternalName", APP_NAME),
                        StringStruct("LegalCopyright", COPYRIGHT),
                        StringStruct("OriginalFilename", f"{APP_NAME}.exe"),
                        StringStruct("ProductName", APP_NAME),
                        StringStruct("ProductVersion", ".".join(map(str, prodvers))),
                    ],
                )
            ]),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="code2clip",
    debug=False,
    strip=False,
    upx=False,                  # ← disable UPX
    console=False,
    windowed=True,
    icon=icon_file,             # ← add icon on Windows if present
    version=win_version,        # ← embed version/metadata on Windows
)

# ─── onedir output ─────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="code2clip",           # dist/code2clip/...
)
