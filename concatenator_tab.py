import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QFileDialog, QComboBox
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt
from file_list_widget import FileListWidget
from file_concatenator import concatenate_files
from wsl_utilities import convert_wsl_path

# Preset definitions for prefix and suffix.
PRESETS = {
    "XML": {"prefix": '<file filename="$filepath">', "suffix": '</file>'},
    "Markdown": {"prefix": '$filepath\\n```', "suffix": '```'},
    "Custom": {"prefix": '', "suffix": ''}
}

class ConcatenatorTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # To access settings from the MainWindow.
        self.init_ui()
        self.setAcceptDrops(True)  # Enable drag-and-drop on this widget.
        self.redraw()

    def init_ui(self):
        layout = QVBoxLayout()

        # Instruction label (used instead of a button).
        self.instruction_label = QLabel("Drag and Drop Files Here")
        self.instruction_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.instruction_label)

        # List widget to display added files.
        self.list_widget = FileListWidget()
        layout.addWidget(self.list_widget)

        # Root path section.
        root_layout = QHBoxLayout()
        self.root_label = QLabel("Root Path: None")
        root_layout.addWidget(self.root_label)
        self.enable_root_checkbox = QCheckBox("Include path")
        self.enable_root_checkbox.stateChanged.connect(self.toggle_root_path)
        root_layout.addWidget(self.enable_root_checkbox)
        layout.addLayout(root_layout)

        # Preset selection for prefix/suffix.
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_layout.addWidget(preset_label)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["XML", "Markdown", "Custom"])
        self.preset_combo.currentTextChanged.connect(self.change_preset)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)

        # Prefix and Suffix input fields.
        prefix_suffix_layout = QHBoxLayout()
        self.prefix_label = QLabel("Prefix:")
        prefix_suffix_layout.addWidget(self.prefix_label)
        self.prefix_input = QLineEdit(PRESETS["XML"]["prefix"])
        self.prefix_input.textChanged.connect(self.on_custom_edit)
        prefix_suffix_layout.addWidget(self.prefix_input)
        self.suffix_label = QLabel("Suffix:")
        prefix_suffix_layout.addWidget(self.suffix_label)
        self.suffix_input = QLineEdit(PRESETS["XML"]["suffix"])
        self.suffix_input.textChanged.connect(self.on_custom_edit)
        prefix_suffix_layout.addWidget(self.suffix_input)
        layout.addLayout(prefix_suffix_layout)

        # Concatenate button.
        self.concat_button = QPushButton("Concatenate and Copy to Clipboard")
        self.concat_button.clicked.connect(self.concatenate_files_wrapper)
        layout.addWidget(self.concat_button)

        self.setLayout(layout)
        self.root_path = None

    def redraw(self):
        """Redraw all dynamic UI elements based on the current theme."""
        self.update_label_color()

    def update_label_color(self):
        """Update label color based on the current theme."""
        text_color = "white" if self.main_window.use_dark_mode else "black"
        self.instruction_label.setStyleSheet(f"color: {text_color}; font-size: 16px;")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        had_file = False
        # Handle plain text drops.
        if event.mimeData().hasText():
            filepaths = event.mimeData().text().strip().splitlines()
            for filepath in filepaths:
                filepath = filepath.strip()
                filepath = convert_wsl_path(filepath)
                if filepath and os.path.isfile(filepath):
                    self.list_widget.add_file(filepath)
                    had_file = True
            event.acceptProposedAction()
        # Handle URL drops.
        if not had_file and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                filepath = convert_wsl_path(filepath)
                if filepath and os.path.isfile(filepath):
                    self.list_widget.add_file(filepath)
            event.acceptProposedAction()
        else:
            event.ignore()

    def toggle_root_path(self):
        from PyQt5.QtWidgets import QFileDialog
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

    def change_preset(self, preset_name):
        if preset_name in PRESETS and preset_name != "Custom":
            self.prefix_input.setText(PRESETS[preset_name]["prefix"])
            self.suffix_input.setText(PRESETS[preset_name]["suffix"])

    def on_custom_edit(self):
        # If the user edits prefix/suffix, automatically set preset to "Custom" if they differ.
        current_preset = self.preset_combo.currentText()
        if current_preset != "Custom":
            xml = PRESETS["XML"]
            md = PRESETS["Markdown"]
            current_prefix = self.prefix_input.text()
            current_suffix = self.suffix_input.text()
            if current_prefix not in (xml["prefix"], md["prefix"]) or current_suffix not in (xml["suffix"], md["suffix"]):
                self.preset_combo.blockSignals(True)
                self.preset_combo.setCurrentText("Custom")
                self.preset_combo.blockSignals(False)

    def concatenate_files_wrapper(self):
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        # Pass along the persistent settings from MainWindow.
        concatenate_files(
            self.list_widget.files,
            self.root_path,
            prefix,
            suffix,
            show_success_message=self.main_window.show_success_message,
            interpret_escape_sequences=self.main_window.interpret_escape_sequences
        )
