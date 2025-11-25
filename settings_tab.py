from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from extension_filters_widget import ExtensionFiltersWidget
from ignore_filters import (
    DEFAULT_IGNORE_PRESET,
    IGNORE_PRESETS,
    get_ignore_set,
)


def default_password_prompt(parent=None, user="", host=""):
    from PyQt5.QtWidgets import QInputDialog, QLineEdit

    pwd, ok = QInputDialog.getText(
        parent,
        "SSH Password",
        f"Enter password for {user}@{host}",
        QLineEdit.Password,
    )
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
        self.success_checkbox = QCheckBox(
            "Show success message after concatenation"
        )
        self.success_checkbox.setChecked(
            self.ctx.settings.show_success_message
        )
        self.success_checkbox.stateChanged.connect(
            lambda s: self.ctx.settings.set_show_success_message(s == Qt.Checked)
        )
        inner_layout.addWidget(self.success_checkbox)

        self.escape_checkbox = QCheckBox(
            "Interpret escape sequences (\\n, \\t, etc.)"
        )
        self.escape_checkbox.setChecked(
            self.ctx.settings.interpret_escape_sequences
        )
        self.escape_checkbox.stateChanged.connect(
            lambda s: self.ctx.settings.set_interpret_escape_sequences(
                s == Qt.Checked
            )
        )
        inner_layout.addWidget(self.escape_checkbox)

        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setChecked(self.ctx.settings.use_dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(
            lambda s: self.ctx.settings.set_use_dark_mode(s == Qt.Checked)
        )
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
        self.extension_filters_widget = ExtensionFiltersWidget(self.ctx.settings)
        self.extension_filters_widget.extensionsReset.connect(
            self._on_extensions_reset
        )
        inner_layout.addWidget(self.extension_filters_widget)

        # --- Ignore Filters UI ---
        inner_layout.addSpacing(10)
        ignore_label = QLabel("Ignored Folder Presets:")
        inner_layout.addWidget(ignore_label)

        self.ignore_preset_combo = QComboBox()
        self.ignore_preset_combo.addItems(list(IGNORE_PRESETS.keys()))
        self.ignore_preset_combo.setCurrentText(
            self.ctx.settings.ignore_preset
        )
        self.ignore_preset_combo.currentTextChanged.connect(
            self.on_ignore_preset_changed
        )
        inner_layout.addWidget(self.ignore_preset_combo)

        self._last_non_custom_preset = (
            self.ctx.settings.ignore_preset
            if self.ctx.settings.ignore_preset != "Custom"
            else DEFAULT_IGNORE_PRESET
        )

        self._apply_ignore_preset_tooltips()

        self.ignore_preview_widget = QWidget()
        preview_layout = QHBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.ignore_count_label = QLabel("")
        self.ignore_preview_label = QLabel("")
        self.ignore_preview_label.setWordWrap(True)
        self.ignore_preview_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        self.ignore_preview_label.setStyleSheet(
            "font-family: 'Courier New', monospace;"
        )
        self.copy_ignores_btn = QPushButton("Copy")
        self.copy_ignores_btn.clicked.connect(self.copy_current_ignores)
        self.show_all_ignores_btn = QPushButton("Show all…")
        self.show_all_ignores_btn.clicked.connect(self.show_all_ignores_dialog)
        self.edit_as_custom_btn = QPushButton("Edit as Custom")
        self.edit_as_custom_btn.clicked.connect(self.convert_preset_to_custom)
        preview_layout.addWidget(self.ignore_count_label)
        preview_layout.addWidget(self.ignore_preview_label, 1)
        preview_layout.addWidget(self.copy_ignores_btn)
        preview_layout.addWidget(self.show_all_ignores_btn)
        preview_layout.addWidget(self.edit_as_custom_btn)
        self.ignore_preview_widget.setLayout(preview_layout)
        inner_layout.addWidget(self.ignore_preview_widget)

        self.custom_ignore_container = QWidget()
        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_ignore_field = QLineEdit()
        self.custom_ignore_field.setPlaceholderText(
            "e.g., node_modules, .git, target"
        )
        self.custom_ignore_field.setText(
            self.ctx.settings.custom_ignore_list
        )
        self.custom_ignore_field.textChanged.connect(
            self.on_custom_ignore_changed
        )
        self.reset_to_preset_btn = QPushButton("Reset to preset")
        self.reset_to_preset_btn.clicked.connect(self.reset_ignore_to_preset)
        custom_layout.addWidget(self.custom_ignore_field, 1)
        custom_layout.addWidget(self.reset_to_preset_btn)
        self.custom_ignore_container.setLayout(custom_layout)
        inner_layout.addWidget(self.custom_ignore_container)

        self.update_ignore_ui_state()
        # --- End Ignore Filters UI ---

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

    def _on_extensions_reset(self):
        self.extension_filters_widget.refresh_from_settings()
        self._resync_ignore_controls()

    def reset_extensions(self):
        self.extension_filters_widget.reset_to_defaults()

    def _resync_ignore_controls(self):
        self.ignore_preset_combo.blockSignals(True)
        self.custom_ignore_field.blockSignals(True)
        self.ignore_preset_combo.setCurrentText(
            self.ctx.settings.ignore_preset
        )
        self.custom_ignore_field.setText(
            self.ctx.settings.custom_ignore_list
        )
        self.update_ignore_ui_state()
        self.ignore_preset_combo.blockSignals(False)
        self.custom_ignore_field.blockSignals(False)

    def update_ignore_ui_state(self):
        if not hasattr(self, "custom_ignore_container"):
            return
        is_custom = self.ignore_preset_combo.currentText() == "Custom"
        self.custom_ignore_container.setVisible(is_custom)
        self.custom_ignore_field.setVisible(is_custom)
        self.ignore_preview_widget.setVisible(not is_custom)
        self.copy_ignores_btn.setVisible(not is_custom)
        self.show_all_ignores_btn.setVisible(not is_custom)
        self.edit_as_custom_btn.setVisible(not is_custom)
        self.reset_to_preset_btn.setVisible(is_custom)
        if not is_custom:
            self._refresh_ignore_preview()

    def on_ignore_preset_changed(self, preset_name: str):
        self.ctx.settings.set_ignore_preset(preset_name)
        if preset_name != "Custom":
            self._last_non_custom_preset = preset_name
        self.update_ignore_ui_state()

    def on_custom_ignore_changed(self, text: str):
        self.ctx.settings.set_custom_ignore_list(text)
        if self.ignore_preset_combo.currentText() != "Custom":
            self.ignore_preset_combo.blockSignals(True)
            self.ignore_preset_combo.setCurrentText("Custom")
            self.ignore_preset_combo.blockSignals(False)
            self.ctx.settings.set_ignore_preset("Custom")
            self.update_ignore_ui_state()

    def _current_ignore_items(self):
        items = get_ignore_set(
            self.ignore_preset_combo.currentText(),
            self.custom_ignore_field.text(),
        )
        return sorted(items, key=str.lower)

    def _refresh_ignore_preview(self, max_items: int = 10):
        items = self._current_ignore_items()
        total = len(items)
        if total == 0:
            preview_text = "(empty)"
        else:
            shown_items = items[:max_items]
            preview_text = ", ".join(shown_items)
            if total > max_items:
                preview_text += ", …more"
        self.ignore_count_label.setText(
            f"{total} item{'s' if total != 1 else ''}"
        )
        self.ignore_preview_label.setText(preview_text)

    def copy_current_ignores(self):
        items = self._current_ignore_items()
        QApplication.clipboard().setText(", ".join(items))

    def show_all_ignores_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ignored folders")
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("\n".join(self._current_ignore_items()))
        text.setStyleSheet("font-family: 'Courier New', monospace;")
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        copy_btn = buttons.addButton("Copy all", QDialogButtonBox.ActionRole)

        def _copy_all():
            QApplication.clipboard().setText(
                ", ".join(self._current_ignore_items())
            )

        copy_btn.clicked.connect(_copy_all)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.resize(520, 380)
        dialog.exec_()

    def convert_preset_to_custom(self):
        items = self._current_ignore_items()
        self.custom_ignore_field.setText(", ".join(items))
        self.ignore_preset_combo.setCurrentText("Custom")
        self.custom_ignore_field.setFocus()

    def reset_ignore_to_preset(self):
        target = self._last_non_custom_preset or DEFAULT_IGNORE_PRESET
        self.ignore_preset_combo.setCurrentText(target)

    def _apply_ignore_preset_tooltips(self):
        model = self.ignore_preset_combo.model()
        for row, name in enumerate(IGNORE_PRESETS.keys()):
            items = sorted(IGNORE_PRESETS[name], key=str.lower)
            if not items:
                tip = "(empty)"
            else:
                preview_items = items[:20]
                tip = ", ".join(preview_items)
                if len(items) > 20:
                    tip += f", … (+{len(items) - 20} more)"
            index = model.index(row, 0)
            model.setData(index, tip, Qt.ToolTipRole)

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
        self.ssh_status_indicator.setStyleSheet(
            f"color: {color}; font-size: 14px; margin-right: 4px;"
        )
        self.ssh_status_text.setText(text)

