import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QFileDialog, QComboBox
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt
from file_list_widget import FileListWidget
from file_concatenator import concatenate_files
from utils import list_files
from wsl_utilities import convert_wsl_path

# Preset definitions for prefix and suffix.
PRESETS = {
    "XML": {"prefix": '<file filename="$filepath">', "suffix": '</file>'},
    "Markdown": {"prefix": '$filepath\\n```', "suffix": '```\\n'},
    "Custom": {"prefix": '', "suffix": ''}
}

class ConcatenatorTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # To access settings from the MainWindow.
        self.settings = main_window.settings
        self.root_path = None
        self.loading_preset = False
        self.init_ui()
        self.load_preset_settings()
        self.setAcceptDrops(True)  # Enable drag-and-drop on this widget.
        self.redraw()

    def init_ui(self):
        layout = QVBoxLayout()

        # Instruction label
        self.instruction_label = QLabel("Drag and Drop Files Here")
        self.instruction_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.instruction_label)

        # File list
        self.list_widget = FileListWidget(self.main_window)
        layout.addWidget(self.list_widget)

        # Root path section with clickable label
        root_layout = QHBoxLayout()
        self.root_button = QPushButton("Root Path: None")
        self.root_button.setFlat(True)
        self.root_button.setStyleSheet("text-align: left;")
        self.root_button.clicked.connect(self.select_root_path)
        root_layout.addWidget(self.root_button)

        self.enable_root_checkbox = QCheckBox("Include path")
        self.enable_root_checkbox.stateChanged.connect(self.toggle_root_path)
        root_layout.addWidget(self.enable_root_checkbox)
        layout.addLayout(root_layout)

        # Preset selection
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_layout.addWidget(preset_label)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["XML", "Markdown", "Custom"])
        self.preset_combo.currentTextChanged.connect(self.change_preset)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)

        # Prefix and suffix inputs
        prefix_suffix_layout = QHBoxLayout()
        self.prefix_label = QLabel("Prefix:")
        prefix_suffix_layout.addWidget(self.prefix_label)
        self.prefix_input = QLineEdit()
        self.prefix_input.textChanged.connect(self.on_prefix_suffix_changed)
        prefix_suffix_layout.addWidget(self.prefix_input)
        self.suffix_label = QLabel("Suffix:")
        prefix_suffix_layout.addWidget(self.suffix_label)
        self.suffix_input = QLineEdit()
        self.suffix_input.textChanged.connect(self.on_prefix_suffix_changed)
        prefix_suffix_layout.addWidget(self.suffix_input)
        layout.addLayout(prefix_suffix_layout)

        # Concatenate button
        self.concat_button = QPushButton("Concatenate and Copy to Clipboard")
        self.concat_button.clicked.connect(self.concatenate_files_wrapper)
        layout.addWidget(self.concat_button)

        self.setLayout(layout)

    def load_preset_settings(self):
        # Suppress change handling during load
        self.loading_preset = True
        # Load last used preset or default to Markdown
        last = self.settings.value("last_preset", "Markdown")
        if last not in PRESETS:
            last = "Markdown"
        # Load custom values if any
        custom_prefix = self.settings.value("custom_prefix", PRESETS["Custom"]["prefix"])
        custom_suffix = self.settings.value("custom_suffix", PRESETS["Custom"]["suffix"])
        PRESETS["Custom"]["prefix"] = custom_prefix
        PRESETS["Custom"]["suffix"] = custom_suffix
        # Set combo and fields
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentText(last)
        self.preset_combo.blockSignals(False)
        self.apply_preset(last)
        self.loading_preset = False

    def apply_preset(self, preset_name):
        # Suppress change handling
        self.loading_preset = True
        # Apply preset values to inputs
        vals = PRESETS.get(preset_name, PRESETS["Custom"])
        self.prefix_input.setText(vals["prefix"])
        self.suffix_input.setText(vals["suffix"])
        self.loading_preset = False

    def save_preset_settings(self, preset_name):
        # Persist preset and custom values
        self.settings.setValue("last_preset", preset_name)
        if preset_name == "Custom":
            self.settings.setValue("custom_prefix", self.prefix_input.text())
            self.settings.setValue("custom_suffix", self.suffix_input.text())

    def redraw(self):
        """Redraw dynamic UI elements based on theme."""
        self.update_label_color()

    def update_label_color(self):
        """Update instruction label color based on theme."""
        text_color = "white" if self.main_window.use_dark_mode else "black"
        self.instruction_label.setStyleSheet(f"color: {text_color}; font-size: 16px;")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle drag and drop of files or text paths."""
        print("Drop event triggered")
        added = False
        # Text drops
        if event.mimeData().hasText():
            lines = event.mimeData().text().strip().splitlines()
            for line in lines:
                path = convert_wsl_path(line.strip())
                if path:
                    if os.path.isfile(path):
                        self.list_widget.add_file(path)
                        added = True
                    elif os.path.isdir(path):
                        self.list_widget.add_folder(path)
                        added = True
        # URL drops (some platforms provide both text and url data)
        if not added and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = convert_wsl_path(url.toLocalFile())
                if path:
                    if os.path.isfile(path):
                        self.list_widget.add_file(path)
                        added = True
                    elif os.path.isdir(path):
                        self.list_widget.add_folder(path)
                        added = True

        if added:
            event.acceptProposedAction()
        else:
            event.ignore()

    def select_root_path(self):
        """Open folder dialog for selecting root path."""
        common_path = os.path.commonpath(self.list_widget.files) if self.list_widget.files else None
        folder = QFileDialog.getExistingDirectory(self, "Select Root Directory", common_path or "")
        if folder:
            self.root_path = folder
            self.enable_root_checkbox.setChecked(True)
            self.list_widget.set_root_path(folder)
            self.root_button.setText(f"Root Path: {folder}")

    def toggle_root_path(self):
        """Enable or disable root path display based on checkbox."""
        if self.enable_root_checkbox.isChecked():
            # If no root selected yet, prompt
            if not self.root_path:
                self.select_root_path()
            else:
                self.list_widget.set_root_path(self.root_path)
        else:
            self.root_path = None
            self.list_widget.disable_root_path()
            self.root_button.setText("Root Path: None")

    def change_preset(self, preset_name):
        if self.loading_preset:
            return
        # Apply new preset
        if preset_name in PRESETS:
            self.apply_preset(preset_name)
            self.save_preset_settings(preset_name)

    def on_prefix_suffix_changed(self):
        # Ignore changes during preset load
        if self.loading_preset:
            return
        # If user edits, switch to Custom and save custom
        xml, md = PRESETS["XML"], PRESETS["Markdown"]
        pre, suf = self.prefix_input.text(), self.suffix_input.text()
        custom_changed = pre not in (xml["prefix"], md["prefix"]) or suf not in (xml["suffix"], md["suffix"])
        if custom_changed and self.preset_combo.currentText() != "Custom":
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText("Custom")
            self.preset_combo.blockSignals(False)
        if self.preset_combo.currentText() == "Custom":
            self.save_preset_settings("Custom")

    def concatenate_files_wrapper(self):
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        concatenate_files(
            self.list_widget.files,
            self.root_path,
            prefix,
            suffix,
            show_success_message=self.main_window.show_success_message,
            interpret_escape_sequences=self.main_window.interpret_escape_sequences
        )
