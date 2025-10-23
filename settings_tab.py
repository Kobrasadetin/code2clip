# settings_tab.py (excerpt – key changes)
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt
from functools import partial
from extension_filters import EXTENSION_GROUP_DEFAULTS
from app_context import AppContext

def default_password_prompt(parent=None, user="", host=""):
    from PyQt5.QtWidgets import QInputDialog, QLineEdit
    pwd, ok = QInputDialog.getText(parent, "SSH Password", f"Enter password for {user}@{host}", QLineEdit.Password)
    return pwd if ok else None

class SettingsTab(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.init_ui()

        # Keep UI in sync with signals (if settings change elsewhere)
        self.ctx.settings.themeChanged.connect(lambda _: self.redraw())
        self.ctx.ssh.statusChanged.connect(self.update_ssh_status)

    def init_ui(self):
        outer_layout = QVBoxLayout()
        inner_layout = QVBoxLayout()

        # Toggles
        self.success_checkbox = QCheckBox("Show success message after concatenation")
        self.success_checkbox.setChecked(self.ctx.settings.show_success_message)
        self.success_checkbox.stateChanged.connect(lambda s: self.ctx.settings.set_show_success_message(s == Qt.Checked))
        inner_layout.addWidget(self.success_checkbox)

        self.escape_checkbox = QCheckBox("Interpret escape sequences (\\n, \\t, etc.)")
        self.escape_checkbox.setChecked(self.ctx.settings.interpret_escape_sequences)
        self.escape_checkbox.stateChanged.connect(lambda s: self.ctx.settings.set_interpret_escape_sequences(s == Qt.Checked))
        inner_layout.addWidget(self.escape_checkbox)

        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(self.ctx.settings.use_dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(lambda s: self.ctx.settings.set_use_dark_mode(s == Qt.Checked))
        inner_layout.addWidget(self.dark_mode_checkbox)

        ssh_label = QLabel("SSH Connection:")
        inner_layout.addWidget(ssh_label)
        ssh_row = QHBoxLayout()
        self.ssh_host = QLineEdit(self.ctx.settings.ssh_host or "")
        self.ssh_user = QLineEdit(self.ctx.settings.ssh_username or "")
        self.ssh_host.setPlaceholderText("host")
        self.ssh_user.setPlaceholderText("username")
        self.ssh_host.editingFinished.connect(self.update_ssh_settings)
        self.ssh_user.editingFinished.connect(self.update_ssh_settings)
        ssh_row.addWidget(self.ssh_host)
        ssh_row.addWidget(self.ssh_user)
        inner_layout.addLayout(ssh_row)

        ssh_status_row = QHBoxLayout()
        self.ssh_status_indicator = QLabel("\u25CF")
        self.ssh_status_indicator.setFixedWidth(16)
        self.ssh_status_text = QLabel()
        ssh_status_row.addWidget(self.ssh_status_indicator)
        ssh_status_row.addWidget(self.ssh_status_text)
        ssh_status_row.addStretch()

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.ctx.ssh.connect)
        ssh_status_row.addWidget(self.connect_button)
        inner_layout.addLayout(ssh_status_row)
        self.update_ssh_status(self.ctx.ssh.is_connected())

        # Extension filters
        ext_label = QLabel("File Type Filters:")
        inner_layout.addWidget(ext_label)
        self.allow_all_checkbox = QCheckBox("Allow all file types")
        self.allow_all_checkbox.setChecked(self.ctx.settings.extension_allow_all)
        self.allow_all_checkbox.stateChanged.connect(self.on_allow_all_changed)
        inner_layout.addWidget(self.allow_all_checkbox)

        self.category_boxes = {}
        self.extension_fields = {}
        for name in EXTENSION_GROUP_DEFAULTS:
            row = QHBoxLayout()
            box = QCheckBox(name)
            box.setChecked(name in self.ctx.settings.extension_categories)
            box.stateChanged.connect(self.on_categories_changed)
            field = QLineEdit(self.ctx.settings.extension_group_texts[name])
            field.textChanged.connect(partial(self.on_extensions_changed, name))
            row.addWidget(box)
            row.addWidget(field)
            inner_layout.addLayout(row)
            self.category_boxes[name] = box
            self.extension_fields[name] = field

        reset_btn = QPushButton("Reset File Extensions")
        reset_btn.clicked.connect(self.reset_extensions)
        inner_layout.addWidget(reset_btn)

        # Layout
        content_widget = QWidget()
        content_widget.setLayout(inner_layout)
        outer_layout.addWidget(content_widget)
        outer_layout.addStretch()

        from utils import get_app_version
        version_label = QLabel(f"Version: {get_app_version()}")
        version_label.setStyleSheet("font-size: 14px; color: gray;")
        version_label.setAlignment(Qt.AlignRight)
        outer_layout.addWidget(version_label)

        self.setLayout(outer_layout)

    def on_allow_all_changed(self, state):
        allow = (state == Qt.Checked)
        self.ctx.settings.set_extension_allow_all(allow)
        for box in self.category_boxes.values():
            box.setEnabled(not allow)
            box.setHidden(allow)
        for field in self.extension_fields.values():
            field.setEnabled(not allow)
            field.setHidden(allow)

    def on_categories_changed(self, _state):
        categories = [n for n, b in self.category_boxes.items() if b.isChecked()]
        self.ctx.settings.set_extension_categories(categories)

    def on_extensions_changed(self, name: str, text: str):
        self.ctx.settings.set_extension_group_text(name, text)

    def reset_extensions(self):
        self.ctx.settings.reset_extension_settings()
        self.allow_all_checkbox.setChecked(self.ctx.settings.extension_allow_all)
        for name, box in self.category_boxes.items():
            box.setChecked(name in self.ctx.settings.extension_categories)
        for name, field in self.extension_fields.items():
            field.setText(self.ctx.settings.extension_group_texts[name])

    def redraw(self):
        # hook if you later need to restyle per theme
        pass

    def update_ssh_settings(self):
        host = self.ssh_host.text().strip()
        user = self.ssh_user.text().strip()
        self.ctx.settings.set_ssh(host, user)

    def update_ssh_status(self, connected: bool):
        color = "#28a745" if connected else "#dc3545"
        text = "Connected" if connected else "Disconnected"
        self.ssh_status_indicator.setStyleSheet(f"color: {color}; font-size: 14px; margin-right: 4px;")
        self.ssh_status_text.setText(text)
