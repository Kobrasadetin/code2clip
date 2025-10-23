import os
import posixpath
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtWidgets import (
    QFileDialog,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QShortcut,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QKeySequence
from PyQt5.QtCore import Qt

from file_list_widget import FileListWidget
from file_concatenator import concatenate_files
from wsl_utilities import convert_wsl_path

# Preset definitions for prefix and suffix.
PRESETS = {
    "XML": {"prefix": '<file filename="$filepath">', "suffix": '</file>'},
    "Markdown": {"prefix": '$filepath\\n```', "suffix": '```\\n'},
    "Custom": {"prefix": '', "suffix": ''}
}


@dataclass(frozen=True)
class TabState:
    files: tuple[str, ...]
    root_path: Optional[str]
    include_root: bool
    prefix: str
    suffix: str
    preset: str

class ConcatenatorTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # To access settings from the MainWindow.
        self.settings = main_window.settings
        self.root_path = None
        self.loading_preset = False
        self._restoring_state = False
        self._history: list[TabState] = []
        self._history_index = -1
        self.init_ui()
        self.load_preset_settings()
        self.setAcceptDrops(True)  # Enable drag-and-drop on this widget.
        self._install_shortcuts()
        self.redraw()
        self._initialize_history()

    def init_ui(self):
        layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self.undo)
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self.redo)
        controls_layout.addWidget(self.undo_button)
        controls_layout.addWidget(self.redo_button)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Instruction label
        self.instruction_label = QLabel("Drag and Drop Files Here")
        self.instruction_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.instruction_label)

        # File list
        self.list_widget = FileListWidget(self.main_window, change_callback=self.on_file_list_changed)
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
        self.undo_button.setEnabled(False)
        self.redo_button.setEnabled(False)
    
       # --- helpers ---------------------------------------------------------
    def _is_remote(self) -> bool:
        ssh = getattr(self.main_window, "ssh_manager", None)
        return bool(ssh and ssh.is_connected())

    def _to_posix(self, path: str) -> str:
        # Ensure forward slashes for remote paths
        return path.replace("\\", "/") if path else path

    def _install_shortcuts(self) -> None:
        self.undo_shortcut = QShortcut(QKeySequence.Undo, self)
        self.undo_shortcut.activated.connect(self.undo)
        self.redo_shortcut = QShortcut(QKeySequence.Redo, self)
        self.redo_shortcut.activated.connect(self.redo)

    def _update_root_button(self) -> None:
        path_text = self.root_path if self.root_path else "None"
        self.root_button.setText(f"Root Path: {path_text}")

    def _capture_state(self) -> TabState:
        return TabState(
            files=tuple(self.list_widget.files),
            root_path=self.root_path,
            include_root=self.enable_root_checkbox.isChecked(),
            prefix=self.prefix_input.text(),
            suffix=self.suffix_input.text(),
            preset=self.preset_combo.currentText(),
        )

    def _initialize_history(self) -> None:
        self._history = [self._capture_state()]
        self._history_index = 0
        self._update_history_buttons()

    def _push_history_state(self) -> None:
        state = self._capture_state()
        if self._history and 0 <= self._history_index < len(self._history):
            if self._history[self._history_index] == state:
                return
            self._history = self._history[: self._history_index + 1]
        self._history.append(state)
        self._history_index = len(self._history) - 1
        self._update_history_buttons()

    def _update_history_buttons(self) -> None:
        can_undo = self._history_index > 0
        can_redo = self._history_index < len(self._history) - 1
        self.undo_button.setEnabled(can_undo)
        self.redo_button.setEnabled(can_redo)

    def _restore_state(self, state: TabState) -> None:
        self._restoring_state = True
        try:
            self.list_widget.set_files(state.files, notify=False)
            self.root_path = state.root_path
            self.enable_root_checkbox.blockSignals(True)
            self.enable_root_checkbox.setChecked(state.include_root)
            self.enable_root_checkbox.blockSignals(False)
            if state.include_root and state.root_path:
                self.list_widget.set_root_path(state.root_path)
            elif state.include_root:
                self.list_widget.set_root_path(None)
            else:
                self.list_widget.disable_root_path()
            self._update_root_button()

            self.loading_preset = True
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText(state.preset)
            self.preset_combo.blockSignals(False)
            self.prefix_input.blockSignals(True)
            self.prefix_input.setText(state.prefix)
            self.prefix_input.blockSignals(False)
            self.suffix_input.blockSignals(True)
            self.suffix_input.setText(state.suffix)
            self.suffix_input.blockSignals(False)
        finally:
            self.loading_preset = False
            self._restoring_state = False

    def _record_change(self) -> None:
        if self._restoring_state or self.loading_preset:
            return
        self._push_history_state()

    def on_file_list_changed(self) -> None:
        self._record_change()

    def undo(self) -> None:
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._restore_state(self._history[self._history_index])
        self._update_history_buttons()

    def redo(self) -> None:
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self._restore_state(self._history[self._history_index])
        self._update_history_buttons()

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
                ssh = self.main_window.ssh_manager
                host = ssh.host if (ssh and ssh.is_connected()) else None
                path = convert_wsl_path(line.strip(), host)
                if self._is_remote():
                    path = self._to_posix(path)
                if path:
                    if ssh and ssh.is_connected() and path.startswith("/"):
                        if ssh.path_exists(path):
                            self.list_widget.add_file(path, enforce_filter=False)
                            added = True
                    elif os.path.isfile(path):
                        self.list_widget.add_file(path, enforce_filter=False)
                        added = True
                    elif os.path.isdir(path):
                        self.list_widget.add_folder(path)
                        added = True
        # URL drops (some platforms provide both text and url data)
        if not added and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ssh = self.main_window.ssh_manager
                host = ssh.host if (ssh and ssh.is_connected()) else None
                path = convert_wsl_path(url.toLocalFile(), host)
                if self._is_remote():
                    path = self._to_posix(path)
                if path:
                    if ssh and ssh.is_connected() and path.startswith("/"):
                        if ssh.path_exists(path):
                            self.list_widget.add_file(path, enforce_filter=False)
                            added = True
                    elif os.path.isfile(path):
                        self.list_widget.add_file(path, enforce_filter=False)
                        added = True
                    elif os.path.isdir(path):
                        self.list_widget.add_folder(path)
                        added = True

        if added:
            event.acceptProposedAction()
        else:
            event.ignore()

    def select_root_path(self):
        """Select a root path depending on SSH configuration."""
        if self._is_remote():
            if self.list_widget.files:
                only_posix = [self._to_posix(p) for p in self.list_widget.files if p.startswith("/")]
                base = posixpath.commonpath(only_posix) if only_posix else "/"
            else:
                base = "/"
            path, ok = QInputDialog.getText(
                 self, "Insert Host Path", "Enter remote root path:", text=base
            )
            if ok and path:
                self.root_path = self._to_posix(path)
                self.enable_root_checkbox.blockSignals(True)
                self.enable_root_checkbox.setChecked(True)
                self.enable_root_checkbox.blockSignals(False)
                self.list_widget.set_root_path(self.root_path)
                self._update_root_button()
                self._record_change()
            return

        # local: Windows/UNIX native commonpath
        common_path = os.path.commonpath(self.list_widget.files) if self.list_widget.files else None

        folder = QFileDialog.getExistingDirectory(
            self, "Select Root Directory", common_path or ""
        )
        if folder:
            self.root_path = folder
            self.enable_root_checkbox.blockSignals(True)
            self.enable_root_checkbox.setChecked(True)
            self.enable_root_checkbox.blockSignals(False)
            self.list_widget.set_root_path(folder)
            self._update_root_button()
            self._record_change()

    def toggle_root_path(self):
        """Enable or disable root path display based on checkbox."""
        if self.enable_root_checkbox.isChecked():
            # If no root selected yet, prompt
            if not self.root_path:
                self.select_root_path()
            else:
                rp = self._to_posix(self.root_path) if self._is_remote() else self.root_path
                self.list_widget.set_root_path(rp)
                self._update_root_button()
                self._record_change()
                return
        else:
            self.root_path = None
            self.list_widget.disable_root_path()
            self._update_root_button()
            self._record_change()
            return

        self._update_root_button()
        self._record_change()

    def change_preset(self, preset_name):
        if self.loading_preset:
            return
        # Apply new preset
        if preset_name in PRESETS:
            self.apply_preset(preset_name)
            self.save_preset_settings(preset_name)
            self._record_change()

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
        self._record_change()

    def concatenate_files_wrapper(self):
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        concatenate_files(
            self.list_widget.files,
            self.root_path,
            prefix,
            suffix,
            show_success_message=self.main_window.show_success_message,
            interpret_escape_sequences=self.main_window.interpret_escape_sequences,
            ssh_manager=self.main_window.ssh_manager,
        )
