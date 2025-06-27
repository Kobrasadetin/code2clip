from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QPushButton,
)
from PyQt5.QtCore import Qt

from utils import get_app_version
from extension_filters import EXTENSION_GROUPS

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

        # Extension filters
        ext_label = QLabel("File Type Filters:")
        inner_layout.addWidget(ext_label)
        self.allow_all_checkbox = QCheckBox("Allow all file types")
        self.allow_all_checkbox.setChecked(self.main_window.extension_allow_all)
        self.allow_all_checkbox.stateChanged.connect(self.on_allow_all_changed)
        inner_layout.addWidget(self.allow_all_checkbox)

        self.category_boxes = {}
        for name, exts in EXTENSION_GROUPS.items():
            box = QCheckBox(f"{name} ({', '.join(exts)})")
            box.setChecked(name in self.main_window.extension_categories)
            box.stateChanged.connect(self.on_categories_changed)
            inner_layout.addWidget(box)
            self.category_boxes[name] = box

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

    def on_categories_changed(self, _state):
        categories = [n for n, b in self.category_boxes.items() if b.isChecked()]
        self.main_window.set_extension_categories(categories)

    def reset_extensions(self):
        self.main_window.reset_extension_settings()
        self.allow_all_checkbox.setChecked(self.main_window.extension_allow_all)
        for name, box in self.category_boxes.items():
            box.setChecked(name in self.main_window.extension_categories)

    def redraw(self):
        """Redraw all dynamic UI elements if necessary."""
        # For now, if there are labels or other elements needing theme updates, do it here.
        pass

