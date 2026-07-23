# Code2Clip — File Concatenator

![License](https://img.shields.io/badge/license-MIT-blue.svg)

A small desktop tool to concatenate files and copy the result to the clipboard.

## Features

* Drag & drop files; reorder by dragging.
* Optional wrapping (XML, Markdown, or custom prefix/suffix).
* File type filters (Text, Code, Data) or allow all.
* Right-click: remove, view encoding, show metadata.
* SSH/WSL2 support: pull remote files (SFTP) and normalize paths.
* Copies output directly to the clipboard.

![Code2Clip Main Window](assets/screenshot.png)

## New in 1.5

Tabs & undo.

---

## Install / Run (prebuilt binaries)

### Windows (ZIP, portable)

1. Download **`Code2Clip-windows.zip`** from Releases.
2. Right-click → **Extract All…**
3. Open the extracted `code2clip` folder and run `code2clip.exe`.

> Note: The app is unsigned. If SmartScreen warns you, choose **More info → Run anyway**.

### macOS (unsigned `.app`)

1. Download **`Code2Clip-macos.zip`** (or `-macos-intel.zip`) from Releases.
2. Unzip, then move `Code2Clip.app` to `/Applications`.
3. First run may be blocked by Gatekeeper. You can either right-click → **Open** or clear quarantine and run:

```bash
xattr -d com.apple.quarantine /Applications/Code2Clip.app
open /Applications/Code2Clip.app
# If needed:
chmod +x /Applications/Code2Clip.app/Contents/MacOS/code2clip
/Applications/Code2Clip.app/Contents/MacOS/code2clip
```

### Linux (ZIP, portable)

1. Download **`code2clip-linux.zip`** from Releases.
2. Unzip, then run:

```bash
cd code2clip
chmod +x ./code2clip
./code2clip
```

---

## Quick Start (from source)

```bash
python code2clip.py
```

1. Drag files into the window
2. (Optional) Configure filters / SSH in **Settings**
3. Choose wrap preset or custom prefix/suffix
4. Click **Concatenate and Copy** and paste anywhere

### Example (XML preset)

```xml
<file filename="file1.txt">
Hello World
</file>
<file filename="file2.txt">
Goodbye World
</file>
```

---

## Crostini / Wayland notes

ChromeOS Crostini sessions default to Wayland. Code2Clip works best when every app interacting with it (e.g., VS Code) uses the same windowing backend.

- Launch Code2Clip normally (Wayland) and start VS Code with Wayland enabled, e.g. `ELECTRON_OZONE_PLATFORM_HINT=wayland code` or `code --ozone-platform-hint=auto`.
- If you need to fall back to X11 for compatibility, run Code2Clip with `QT_QPA_PLATFORM=xcb python code2clip.py` (or set `QT_QPA_PLATFORM=xcb` before launching the packaged binary). Drag and drop then expects other apps to use X11 as well.
- To silence noisy compositor warnings from Qt on Crostini, you can set `QT_LOGGING_RULES="qt.qpa.wayland.warning=false"` when launching.

---

## Installation (from source)

* Requires Python 3.8+ and pip.

```bash
git clone https://github.com/kobrasadetin/code2clip.git
cd code2clip
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
python code2clip.py
```

---

## Packaging (developers)

This repo uses a PyInstaller for a **onedir** build (no UPX). CI writes a `code2clip_version.txt` and then runs the spec.

Build locally:

```bash
pip install pyinstaller
pyinstaller --clean --noconfirm code2clip.spec
# Output: dist/code2clip/...
# Windows: dist/code2clip/code2clip.exe
# macOS:   dist/code2clip/code2clip (wrapped into .app in packaging step)
# Linux:   dist/code2clip/code2clip
```

## Contributing

Contributions are welcome! To report bugs, suggest features, or submit pull requests, please see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro/) – GUI framework
* [chardet](https://github.com/chardet/chardet) – Encoding detection library
* [paramiko](https://www.paramiko.org/) – SSH/SFTP library
