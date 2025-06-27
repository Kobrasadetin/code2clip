from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel, QSpacerItem, QSizePolicy, QLineEdit
from PyQt5.QtCore import Qt

from utils import get_app_version

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
        ext_label = QLabel("Allowed Extensions (comma separated):")
        inner_layout.addWidget(ext_label)
        self.extensions_input = QLineEdit(
            ", ".join(self.main_window.extension_filters)
        )
        self.extensions_input.editingFinished.connect(self.update_extensions)
        inner_layout.addWidget(self.extensions_input)

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

    def update_extensions(self):
        text = self.extensions_input.text()
        self.main_window.set_extension_filters(text)

    def redraw(self):
        """Redraw all dynamic UI elements if necessary."""
        # For now, if there are labels or other elements needing theme updates, do it here.
        pass

