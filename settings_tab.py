from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox
from PyQt5.QtCore import Qt

class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Access MainWindow settings.
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Success message toggle.
        self.success_checkbox = QCheckBox("Show success message after concatenation")
        self.success_checkbox.setChecked(self.main_window.show_success_message)
        self.success_checkbox.stateChanged.connect(self.toggle_success_message)
        layout.addWidget(self.success_checkbox)

        # Escape sequence interpretation toggle.
        self.escape_checkbox = QCheckBox("Interpret escape sequences (\\n, \\t, etc.)")
        self.escape_checkbox.setChecked(self.main_window.interpret_escape_sequences)
        self.escape_checkbox.stateChanged.connect(self.toggle_escape_sequences)
        layout.addWidget(self.escape_checkbox)

        # Dark mode toggle.
        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(self.main_window.use_dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_checkbox)

        layout.addStretch()
        self.setLayout(layout)

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

    def redraw(self):
        """Redraw all dynamic UI elements if necessary."""
        # For now, if there are labels or other elements needing theme updates, do it here.
        pass
