from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtCore import Qt

from utils import get_app_version
from functools import partial
from extension_filters import EXTENSION_GROUP_DEFAULTS

class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Access MainWindow settings.
        self.init_ui()

    def init_ui(self):
        outer_layout = QVBoxLayout()
        inner_layout = QVBoxLayout()

        # Toggles
        self.success_checkbox = QCheckBox("Show success message after concatenation")
        self.success_checkbox.setChecked(self.main_window.show_success_message)
        self.success_checkbox.stateChanged.connect(self.toggle_success_message)
        inner_layout.addWidget(self.success_checkbox)

        self.escape_checkbox = QCheckBox("Interpret escape sequences (\\n, \\t, etc.)")
        self.escape_checkbox.setChecked(self.main_window.interpret_escape_sequences)
        self.escape_checkbox.stateChanged.connect(self.toggle_escape_sequences)
        inner_layout.addWidget(self.escape_checkbox)

        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(self.main_window.use_dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        inner_layout.addWidget(self.dark_mode_checkbox)

        # SSH settings
        ssh_host_label = QLabel("SSH Host:")
        inner_layout.addWidget(ssh_host_label)
        self.ssh_host_input = QLineEdit(self.main_window.ssh_host)
        self.ssh_host_input.textChanged.connect(self.on_ssh_host_changed)
        inner_layout.addWidget(self.ssh_host_input)

        ssh_user_label = QLabel("SSH Username:")
        inner_layout.addWidget(ssh_user_label)
        self.ssh_user_input = QLineEdit(self.main_window.ssh_user)
        self.ssh_user_input.textChanged.connect(self.on_ssh_user_changed)
        inner_layout.addWidget(self.ssh_user_input)

        # Extension filters
        ext_label = QLabel("File Type Filters:")
        inner_layout.addWidget(ext_label)
        self.allow_all_checkbox = QCheckBox("Allow all file types")
        self.allow_all_checkbox.setChecked(self.main_window.extension_allow_all)
        self.allow_all_checkbox.stateChanged.connect(self.on_allow_all_changed)
        inner_layout.addWidget(self.allow_all_checkbox)

        self.category_boxes: dict[str, QCheckBox] = {}
        self.extension_fields: dict[str, QLineEdit] = {}
        for name in EXTENSION_GROUP_DEFAULTS:
            row = QHBoxLayout()
            box = QCheckBox(name)
            box.setChecked(name in self.main_window.extension_categories)
            box.stateChanged.connect(self.on_categories_changed)
            field = QLineEdit(self.main_window.extension_group_texts[name])
            field.textChanged.connect(partial(self.on_extensions_changed, name))
            row.addWidget(box)
            row.addWidget(field)
            inner_layout.addLayout(row)
            self.category_boxes[name] = box
            self.extension_fields[name] = field

        reset_btn = QPushButton("Reset File Extensions")
        reset_btn.clicked.connect(self.reset_extensions)
        inner_layout.addWidget(reset_btn)

        # Add inner layout to a widget to control expansion
        content_widget = QWidget()
        content_widget.setLayout(inner_layout)
        outer_layout.addWidget(content_widget)

        # Stretch fills all available space
        outer_layout.addStretch()

        # Version label pinned to the very bottom
        version_label = QLabel(f"Version: {get_app_version()}")
        version_label.setStyleSheet("font-size: 14px; color: gray;")
        version_label.setAlignment(Qt.AlignRight)
        outer_layout.addWidget(version_label)

        self.setLayout(outer_layout)

    def toggle_success_message(self, state):
        self.main_window.show_success_message = (state == Qt.Checked)
        self.main_window.save_settings()

    def toggle_escape_sequences(self, state):
        self.main_window.interpret_escape_sequences = (state == Qt.Checked)
        self.main_window.save_settings()

    def toggle_dark_mode(self, state):
        self.main_window.use_dark_mode = (state == Qt.Checked)
        self.main_window.save_settings()
        self.main_window.apply_dark_mode()
        self.main_window.redraw()

    def on_allow_all_changed(self, state):
        allow = state == Qt.Checked
        self.main_window.set_extension_allow_all(allow)
        for box in self.category_boxes.values():
            box.setEnabled(not allow)
            box.setHidden(allow)
        for field in self.extension_fields.values():
            field.setEnabled(not allow)
            field.setHidden(allow)

    def on_categories_changed(self, _state):
        categories = [n for n, b in self.category_boxes.items() if b.isChecked()]
        self.main_window.set_extension_categories(categories)

    def on_extensions_changed(self, name: str, text: str):
        self.main_window.set_extension_group_text(name, text)

    def reset_extensions(self):
        self.main_window.reset_extension_settings()
        self.allow_all_checkbox.setChecked(self.main_window.extension_allow_all)
        for name, box in self.category_boxes.items():
            box.setChecked(name in self.main_window.extension_categories)
        for name, field in self.extension_fields.items():
            field.setText(self.main_window.extension_group_texts[name])

    def on_ssh_host_changed(self, text: str):
        self.main_window.set_ssh_host(text)

    def on_ssh_user_changed(self, text: str):
        self.main_window.set_ssh_user(text)

    def redraw(self):
        """Redraw all dynamic UI elements if necessary."""
        # For now, if there are labels or other elements needing theme updates, do it here.
        pass

