# Code2Clip File Concatenator

![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Code2Clip** is a simple desktop application that allows you to:

- Drag and drop multiple files onto the application window.
- Reorder the files to change the concatenation order.
- Wrap each file's contents with tags based on their filenames.
- Copy the final concatenated output directly to the clipboard.
- Inspect file encodings and metadata via a right-click context menu.

---

## Features

- **Drag and Drop**: Add files easily by dragging them into the window.
- **Concatenate & Copy**: Combines all file contents into XML-like tags and copies the result to the clipboard.
- **WSL2 Support in Windows**

## Why?

Easy way to paste file contents to your favourite large language model.

---

## Installation

### **Prerequisites**

- **Python 3.6 or higher**: Install Python from [python.org](https://www.python.org/downloads/).
- **Pip**: Python's package manager (comes pre-installed with Python).

### **Clone the Repository**

```bash
git clone https://github.com/yourusername/file-concatenator.git
cd file-concatenator
```

### **Install Dependencies**

It's recommended to use a virtual environment to manage dependencies.

```bash
# For example, in an anaconda env
conda install -c conda-forge --yes --file requirements.txt
```

---

## Usage

Run the application using Python:

```bash
python code2clip.py
```

### **How to Use the Application**
1. **Drag and drop files** into the main window.
2. **Reorder files** by dragging them in the list.
3. **Right-click** on any file in the list to:
   - Remove the file.
   - Check its encoding.
   - View file metadata.
4. Click the **"Concatenate and Copy to Clipboard"** button.
5. Paste the concatenated text wherever you need it!

### **Example Output**
For files `file1.txt` and `file2.txt` with content:

**file1.txt**:
```
Hello World
```
**file2.txt**:
```
Goodbye World
```

The output will look like this:

```xml
<file filename="file1.txt">
Hello World
</file>
<file filename="file2.txt">
Goodbye World
</file>
```

This output is copied directly to your clipboard.

---

## Packaging as an Executable

To distribute the application without requiring Python, create a standalone executable using **PyInstaller**:

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Create Executable**
   ```bash
   pyinstaller --onefile --windowed file_concatenator.py
   ```

3. The executable will be located in the `dist` folder.

---

## Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting bugs, suggesting features, and submitting pull requests.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro/)
- [chardet](https://github.com/chardet/chardet)
