import os
import posixpath
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QCheckBox,
    QFileDialog,
    QComboBox,
    QInputDialog,
)
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


@dataclass(eq=True)
class WorkspaceState:
    files: Tuple[str, ...]
    root_path: Optional[str]
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
        self._state_lock = 0
        self._undo_stack: List[WorkspaceState] = []
        self._undo_index = -1
        self.init_ui()
        self.load_preset_settings()
        self.setAcceptDrops(True)  # Enable drag-and-drop on this widget.
        self.redraw()
        self._push_state(force=True)
        self._update_undo_buttons()

    def init_ui(self):
        layout = QVBoxLayout()

        # Instruction label
        self.instruction_label = QLabel("Drag and Drop Files Here")
        self.instruction_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.instruction_label)

        controls_layout = QHBoxLayout()
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self.undo)
        controls_layout.addWidget(self.undo_button)
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self.redo)
        controls_layout.addWidget(self.redo_button)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # File list
        self.list_widget = FileListWidget(
            self.main_window, state_changed=self._on_list_state_changed
        )
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
    
        # --- helpers ---------------------------------------------------------
    def _is_remote(self) -> bool:
        ssh = getattr(self.main_window, "ssh_manager", None)
        return bool(ssh and ssh.is_connected())

    def _to_posix(self, path: str) -> str:
        # Ensure forward slashes for remote paths
        return path.replace("\\", "/") if path else path

    def _is_state_locked(self) -> bool:
        return self._state_lock > 0

    @contextmanager
    def _state_guard(self, block_list_widget: bool = True):
        self._state_lock += 1
        if (
            block_list_widget
            and hasattr(self.list_widget, "block_state_notifications")
        ):
            try:
                with self.list_widget.block_state_notifications():
                    yield
            finally:
                self._state_lock -= 1
            return
        try:
            yield
        finally:
            self._state_lock -= 1

    def _capture_state(self) -> WorkspaceState:
        return WorkspaceState(
            tuple(self.list_widget.files),
            self.root_path,
            self.prefix_input.text(),
            self.suffix_input.text(),
            self.preset_combo.currentText(),
        )

    def _apply_root_path(self, new_root: Optional[str]):
        stored_root = self._to_posix(new_root) if (new_root and self._is_remote()) else new_root
        with self._state_guard():
            self.root_path = stored_root
            if stored_root:
                self.list_widget.set_root_path(stored_root)
                self.enable_root_checkbox.setChecked(True)
            else:
                self.list_widget.disable_root_path()
                self.enable_root_checkbox.setChecked(False)
        if stored_root:
            self.root_button.setText(f"Root Path: {stored_root}")
        else:
            self.root_button.setText("Root Path: None")

    def _apply_state(self, state: WorkspaceState):
        with self._state_guard():
            self.list_widget.files = list(state.files)
            self.list_widget.update_list_display()
        self._apply_root_path(state.root_path)
        with self._state_guard(block_list_widget=False):
            self.loading_preset = True
            self.prefix_input.setText(state.prefix)
            self.suffix_input.setText(state.suffix)
            self.loading_preset = False
            self.preset_combo.blockSignals(True)
            preset = state.preset if state.preset in PRESETS else "Custom"
            self.preset_combo.setCurrentText(preset)
            self.preset_combo.blockSignals(False)

    def _push_state(self, force: bool = False):
        if self._is_state_locked():
            return
        state = self._capture_state()
        if not force and self._undo_index >= 0 and self._undo_stack[self._undo_index] == state:
            return
        del self._undo_stack[self._undo_index + 1 :]
        self._undo_stack.append(state)
        self._undo_index = len(self._undo_stack) - 1
        self._update_undo_buttons()

    def _on_list_state_changed(self):
        if self._is_state_locked():
            return
        self._push_state()

    def _update_undo_buttons(self):
        can_undo = self._undo_index > 0
        can_redo = self._undo_index < len(self._undo_stack) - 1
        self.undo_button.setEnabled(can_undo)
        self.redo_button.setEnabled(can_redo)

    def undo(self):
        if self._undo_index <= 0:
            return
        self._undo_index -= 1
        self._apply_state(self._undo_stack[self._undo_index])
        self._update_undo_buttons()

    def redo(self):
        if self._undo_index >= len(self._undo_stack) - 1:
            return
        self._undo_index += 1
        self._apply_state(self._undo_stack[self._undo_index])
        self._update_undo_buttons()

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
                self._apply_root_path(path)
                self._push_state()
            return

        # local: Windows/UNIX native commonpath
        common_path = os.path.commonpath(self.list_widget.files) if self.list_widget.files else None

        folder = QFileDialog.getExistingDirectory(
            self, "Select Root Directory", common_path or ""
        )
        if folder:
            self._apply_root_path(folder)
            self._push_state()

    def toggle_root_path(self):
        """Enable or disable root path display based on checkbox."""
        if self._is_state_locked():
            return
        if self.enable_root_checkbox.isChecked():
            if not self.root_path:
                self.select_root_path()
                return
            self._apply_root_path(self.root_path)
            self._push_state()
        else:
            self._apply_root_path(None)
            self._push_state()

    def change_preset(self, preset_name):
        if self.loading_preset or self._is_state_locked():
            return
        # Apply new preset
        if preset_name in PRESETS:
            self.apply_preset(preset_name)
            self.save_preset_settings(preset_name)
            self._push_state()

    def on_prefix_suffix_changed(self):
        # Ignore changes during preset load
        if self.loading_preset or self._is_state_locked():
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
        self._push_state()

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
