# Code2Clip File Concatenator

![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Code2Clip** is a simple desktop application for quickly concatenating file contents and copying the result to the clipboard.

### Key Features:
- **Drag and Drop**: Add files by dragging them into the application window.
- **Reordering**: Change the order of concatenation by dragging files in the list.
- **Custom Wrapping**: Wrap file contents with **XML**, **Markdown**, or **custom** tags based on their filenames.
- **Clipboard Output**: Instantly copies the concatenated result to your clipboard.
- **File Encoding & Metadata**: Inspect file encodings and metadata via a right-click context menu.
- **WSL2 Path Support**: Automatically converts WSL2 paths to Windows-compatible paths.

---

## Why Use Code2Clip?

Code2Clip provides a fast way to **combine multiple files** and **paste their contents** into AI models like ChatGPT, DeepSeek, and Claude without manually copying and formatting each file.

---

## Installation

### **Prerequisites**
- **Python 3.7+** – Download from [python.org](https://www.python.org/downloads/)
- **Pip** (comes with Python)
- **PyQt5** (GUI framework)

### **Clone and Install Dependencies**
It's recommended to use a virtual environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/code2clip.git
cd code2clip

# Install dependencies in a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

---

## Usage

Run the application using:

```bash
python code2clip.py
```

### **How to Use:**
1. **Drag and drop files** into the main window.
2. **Reorder files** by dragging them in the list.
3. **Right-click** on a file for options:
   - Remove the file
   - Check its encoding
   - View metadata (size, modification date)
4. **Select a preset** (XML, Markdown, or Custom) to define how files are wrapped.
5. **Click "Concatenate and Copy to Clipboard"**.
6. **Paste the result** into your desired application.

---

## Example Output

For files `file1.txt` and `file2.txt`:

**file1.txt**:
```
Hello World
```

**file2.txt**:
```
Goodbye World
```

With **XML Preset**, the output will be:

```xml
<file filename="file1.txt">
Hello World
</file>
<file filename="file2.txt">
Goodbye World
</file>
```

This text is **automatically copied** to your clipboard.

---

## Packaging as an Executable

To distribute the app **without requiring Python**, create a standalone executable using **PyInstaller**:

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Build the Executable**:
   ```bash
   pyinstaller --onefile --windowed code2clip.py
   ```

3. The executable will be located in the `dist` folder.

---

## Contributing

Contributions are welcome! To report bugs, suggest features, or submit pull requests, please check out the [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro/) – GUI framework
- [chardet](https://github.com/chardet/chardet) – Encoding detection library

---
