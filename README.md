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

## Quick Start

```bash
python code2clip.py
```

1. Drag files into the window
2. (Optional) Set filter / SSH in **Settings**
3. Choose wrap preset or custom prefix/suffix
4. Click **Concatenate and Copy** and paste anywhere

## Example (XML preset)

```xml
<file filename="file1.txt">
Hello World
</file>
<file filename="file2.txt">
Goodbye World
</file>
```

## Installation (from source)

* Requires Python 3.8+, pip

```bash
git clone https://github.com/yourusername/code2clip.git
cd code2clip
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
python code2clip.py
```

## macOS App (unsigned)

Download the `.app` from Releases, then:

```bash
xattr -d com.apple.quarantine /Applications/Code2Clip.app   # remove quarantine
open /Applications/Code2Clip.app                            # run
# If Gatekeeper complains, run the binary directly:
chmod +x /Applications/Code2Clip.app/Contents/MacOS/code2clip
/Applications/Code2Clip.app/Contents/MacOS/code2clip
```

## Packaging (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed code2clip.py
# binary in dist/
```

## Contributing

Contributions are welcome! To report bugs, suggest features, or submit pull requests, please check out the [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro/) – GUI framework
- [chardet](https://github.com/chardet/chardet) – Encoding detection library
- [paramiko](https://www.paramiko.org/) - pure-Python implementation of the SSHv2 protocol

---
