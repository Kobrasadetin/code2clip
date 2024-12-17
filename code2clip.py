import sys
import os
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
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from file_list_widget import FileListWidget
from file_concatenator import concatenate_files

# OS-specific separator
separator = os.sep

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
        self.prefix_input = QLineEdit('<file filename="$path'+separator+'$filename">')
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
        if event.mimeData().hasText():
            # Process plain text (e.g., from VSCode)
            filepaths = event.mimeData().text().strip().splitlines()
            for filepath in filepaths:
                filepath = filepath.strip()
                if os.path.isfile(filepath):
                    self.list_widget.add_file(filepath)
                    had_file = True
            event.acceptProposedAction()
        if not had_file and event.mimeData().hasUrls():
            # Process URLs (standard drag-and-drop)
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if os.path.isfile(filepath):
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
        concatenate_files(self.list_widget.files, self.root_path, prefix, suffix)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
