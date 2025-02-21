import sys
import os
import platform
import subprocess
import re
import ctypes
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QTabWidget
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPalette, QColor
from file_list_widget import FileListWidget
from file_concatenator import concatenate_files
from wsl_utilities import convert_wsl_path, get_default_wsl_distro

# OS-specific separator
separator = os.sep

# Preset definitions
PRESETS = {
    "XML": {
        "prefix": '<file filename="$filepath">',
        "suffix": '</file>'
    },
    "Markdown": {
        "prefix": '$filepath\n```',
        "suffix": '```'
    },
    "Custom": {
        "prefix": '',
        "suffix": ''
    }
}

class ConcatenatorTab(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings  # Reference to the global settings dictionary
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        layout = QVBoxLayout()

        # Instruction label (acts as drop area indicator)
        self.instruction_label = QLabel("Drag and Drop Files Here")
        self.instruction_label.setStyleSheet("font-size: 16px;")
        self.instruction_label.setEnabled(False)  # Looks like a label
        layout.addWidget(self.instruction_label)

        # List widget to display files
        self.list_widget = FileListWidget()
        layout.addWidget(self.list_widget)

        # Root path and options
        root_layout = QHBoxLayout()
        self.root_label = QLabel("Root Path: None")
        root_layout.addWidget(self.root_label)
        self.enable_root_checkbox = QCheckBox("Include path")
        self.enable_root_checkbox.stateChanged.connect(self.toggle_root_path)
        root_layout.addWidget(self.enable_root_checkbox)
        layout.addLayout(root_layout)

        # Preset selection for prefix/suffix
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_layout.addWidget(preset_label)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["XML", "Markdown", "Custom"])
        self.preset_combo.currentTextChanged.connect(self.change_preset)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)

        # File prefix and suffix inputs
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

        # Concatenate button
        self.concat_button = QPushButton("Concatenate and Copy to Clipboard")
        self.concat_button.clicked.connect(self.concatenate_files_wrapper)
        layout.addWidget(self.concat_button)

        self.setLayout(layout)
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
                filepath = convert_wsl_path(filepath)
                if filepath and os.path.isfile(filepath):
                    self.list_widget.add_file(filepath)
                    had_file = True
            event.acceptProposedAction()

        # Process URLs (standard drag-and-drop)
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
        # If the user manually edits prefix/suffix such that they no longer match a preset,
        # automatically set preset to "Custom"
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
        concatenate_files(
            self.list_widget.files,
            self.root_path,
            prefix,
            suffix,
            show_success_message=self.settings["show_success_message"],
            interpret_escape_sequences=self.settings["interpret_escape_sequences"]
        )

class SettingsTab(QWidget):
    def __init__(self, settings, apply_dark_mode_callback):
        super().__init__()
        self.settings = settings
        self.apply_dark_mode_callback = apply_dark_mode_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Toggle for success message
        self.success_checkbox = QCheckBox("Show success message after concatenation")
        self.success_checkbox.setChecked(self.settings["show_success_message"])
        self.success_checkbox.stateChanged.connect(self.toggle_success_message)
        layout.addWidget(self.success_checkbox)

        # Toggle for escape sequence interpretation
        self.escape_checkbox = QCheckBox("Interpret escape sequences (\\n, \\t, etc.)")
        self.escape_checkbox.setChecked(self.settings["interpret_escape_sequences"])
        self.escape_checkbox.stateChanged.connect(self.toggle_escape_sequences)
        layout.addWidget(self.escape_checkbox)

        # Toggle for dark mode
        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(self.settings["use_dark_mode"])
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_checkbox)

        layout.addStretch()
        self.setLayout(layout)

    def toggle_success_message(self, state):
        self.settings["show_success_message"] = state == Qt.Checked

    def toggle_escape_sequences(self, state):
        self.settings["interpret_escape_sequences"] = state == Qt.Checked

    def toggle_dark_mode(self, state):
        self.settings["use_dark_mode"] = state == Qt.Checked
        self.apply_dark_mode_callback()

def enable_dark_title_bar(hwnd):
    """Forces dark mode title bar if Windows 10+ is in dark mode."""
    if platform.system() == "Windows":
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # Windows 10 version 1809+
            is_dark_mode = ctypes.c_int(1)  # 1 = Dark Mode ON
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(is_dark_mode), ctypes.sizeof(is_dark_mode)
            )
        except Exception as e:
            print(f"Could not enable dark title bar: {e}", file=sys.stderr)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Concatenator")
        self.setGeometry(100, 100, 600, 400)
        self.settings = {
            "show_success_message": True,
            "interpret_escape_sequences": False,
            "use_dark_mode": False
        }
        self.init_ui()
        # Apply dark title bar on Windows
        if platform.system() == "Windows":
            hwnd = self.winId().__int__()
            enable_dark_title_bar(hwnd)

    def init_ui(self):
        layout = QVBoxLayout()

        # Create a tab widget for Concatenator and Settings
        self.tabs = QTabWidget()
        self.concat_tab = ConcatenatorTab(self.settings)
        self.settings_tab = SettingsTab(self.settings, self.apply_dark_mode)
        self.tabs.addTab(self.concat_tab, "Concatenator")
        self.tabs.addTab(self.settings_tab, "Settings")
        layout.addWidget(self.tabs)

        self.setLayout(layout)

    def apply_dark_mode(self):
        app = QApplication.instance()
        if self.settings["use_dark_mode"]:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.black)
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)

            app.setPalette(dark_palette)
        else:
            app.setPalette(app.style().standardPalette())

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()

    # Apply dark mode if enabled in settings at startup
    window.apply_dark_mode()

    app_icon = QIcon()
    app_icon.addFile('gui/icon_32.png', QSize(32,32))
    app_icon.addFile('gui/icon_48.png', QSize(48,48))
    app_icon.addFile('gui/icon_256.png', QSize(256,256))
    app.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
