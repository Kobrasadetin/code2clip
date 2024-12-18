import sys
import os
import platform
import subprocess
import re
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QLineEdit,
    QCheckBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon
from file_list_widget import FileListWidget
from file_concatenator import concatenate_files

# OS-specific separator
separator = os.sep

def get_default_wsl_distro():
    """Retrieve the default WSL2 distribution name and clean null bytes."""
    try:
        # Run 'wsl -l -q' to list distros
        result = subprocess.check_output(["wsl", "-l", "-q"], universal_newlines=False)
        # Decode as utf-16-le and strip whitespace
        decoded_result = result.decode("utf-16-le").strip()
        distros = decoded_result.splitlines()
        if distros:
            return distros[0]  # Return the first (default) distro
    except Exception as e:
        print(f"Encountered absolute Unix filepath in Windows. Error retrieving WSL distros: {e}", file=sys.stderr)
        return None
    return None

def convert_wsl_path(filepath):
    """
    Convert a WSL2 path to a Windows-compatible network path using \wsl.localhost\.
    """
    if platform.system() == "Windows" and filepath.startswith("/"):
        # Dynamically get the default WSL2 distro
        default_distro = get_default_wsl_distro()
        if default_distro:
            # Construct the network path
            windows_path = f"\\\\wsl.localhost\\{default_distro}" + filepath.replace("/", "\\")
            if os.path.isfile(windows_path):
                return windows_path
    return filepath

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Concatenator")
        self.setGeometry(100, 100, 600, 400)
        self.setAcceptDrops(True)  # Enable drag and drop on the main window

        # Set up the layout
        layout = QVBoxLayout()

        # Instruction label
        self.instruction_label = QPushButton("Drag and Drop Files Here")
        self.instruction_label.setStyleSheet("font-size: 16px;")
        self.instruction_label.setEnabled(False)  # Make it look like a label
        layout.addWidget(self.instruction_label)

        # List widget to display files
        self.list_widget = FileListWidget()
        layout.addWidget(self.list_widget)

        # Root path and options
        root_layout = QHBoxLayout()

        # Root Path Label
        self.root_label = QLabel("Root Path: None")
        root_layout.addWidget(self.root_label)

        # Enable Path Checkbox
        self.enable_root_checkbox = QCheckBox("Include path")
        self.enable_root_checkbox.stateChanged.connect(self.toggle_root_path)
        root_layout.addWidget(self.enable_root_checkbox)

        layout.addLayout(root_layout)

        # File prefix and suffix inputs
        prefix_suffix_layout = QHBoxLayout()

        # Prefix Input
        self.prefix_label = QLabel("Prefix:")
        prefix_suffix_layout.addWidget(self.prefix_label)
        self.prefix_input = QLineEdit('<file filename="$filepath">')
        prefix_suffix_layout.addWidget(self.prefix_input)

        # Suffix Input
        self.suffix_label = QLabel("Suffix:")
        prefix_suffix_layout.addWidget(self.suffix_label)
        self.suffix_input = QLineEdit('</file>')
        prefix_suffix_layout.addWidget(self.suffix_input)

        layout.addLayout(prefix_suffix_layout)

        # Concatenate button
        self.concat_button = QPushButton("Concatenate and Copy to Clipboard")
        self.concat_button.clicked.connect(self.concatenate_files_wrapper)
        layout.addWidget(self.concat_button)

        self.setLayout(layout)

        # Internal State
        self.root_path = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        had_file = False
        # Process plain text (e.g., from VSCode)
        if event.mimeData().hasText():
            filepaths = event.mimeData().text().strip().splitlines()
            for filepath in filepaths:
                filepath = filepath.strip()
                filepath = convert_wsl_path(filepath)  # Handle WSL2 path conversion
                if filepath and os.path.isfile(filepath):
                    self.list_widget.add_file(filepath)
                    had_file = True
            event.acceptProposedAction()

        # Process URLs (standard drag-and-drop)
        if not had_file and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                filepath = convert_wsl_path(filepath)  # Handle WSL2 path conversion
                if filepath and os.path.isfile(filepath):
                    self.list_widget.add_file(filepath)
            event.acceptProposedAction()
        else:
            event.ignore()

    def toggle_root_path(self):
        if self.enable_root_checkbox.isChecked():
            common_path = os.path.commonpath(self.list_widget.files) if self.list_widget.files else None
            folder = QFileDialog.getExistingDirectory(self, "Select Root Directory", common_path)
            if folder:
                self.root_path = folder
                self.list_widget.set_root_path(folder)
                self.root_label.setText(f"Root Path: {folder}")
            else:
                self.enable_root_checkbox.setChecked(False)
        else:
            self.root_path = None
            self.list_widget.disable_root_path()
            self.root_label.setText("Root Path: None")

    def concatenate_files_wrapper(self):
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        include_path = self.enable_root_checkbox.isChecked()  # Use checkbox state

        concatenate_files(self.list_widget.files, self.root_path, prefix, suffix)

def main():
    app = QApplication(sys.argv)
    app_icon = QIcon()
    app_icon.addFile('gui/icon_32.png', QSize(32,32))
    app_icon.addFile('gui/icon_48.png', QSize(48,48))
    app_icon.addFile('gui/icon_256.png', QSize(256,256))
    app.setWindowIcon(app_icon)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
