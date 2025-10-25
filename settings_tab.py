# settings_tab.py (excerpt – key changes)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
    QRadioButton,
    QButtonGroup,
    QToolButton,
    QLayout,
    QWidgetItem,
)
from PyQt5.QtCore import Qt, QRect, QSize, QPoint
from functools import partial
from extension_sets import TOP_CATEGORIES, EXTENSION_SETS
from ignore_filters import (
    DEFAULT_IGNORE_PRESET,
    IGNORE_PRESETS,
    get_ignore_set,
)
from app_context import AppContext


class FlowLayout(QLayout):
    """A simple flow layout for arranging chip buttons."""

    def __init__(self, parent=None, margin: int = 0, spacing: int = -1):
        super().__init__(parent)
        self._item_list: list[QWidgetItem] = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing if spacing >= 0 else 6)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()
        effective_rect = rect.adjusted(
            self.contentsMargins().left(),
            self.contentsMargins().top(),
            -self.contentsMargins().right(),
            -self.contentsMargins().bottom(),
        )
        x = effective_rect.x()
        y = effective_rect.y()

        for item in self._item_list:
            widget = item.widget()
            if widget is None or not widget.isVisible():
                continue
            space_x = spacing
            space_y = spacing
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + self.contentsMargins().bottom()


class ExtensionChipButton(QToolButton):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)
        self.toggled.connect(self._update_style)
        self._update_style(self.isChecked())

    def sizeHint(self):
        hint = super().sizeHint()
        return hint.expandedTo(QSize(80, hint.height()))

    def _update_style(self, checked: bool):
        base = "border-radius: 12px; padding: 4px 12px;"
        if checked:
            style = "background-color: palette(highlight); color: palette(highlighted-text);"
        else:
            style = (
                "background-color: palette(button); color: palette(button-text);"
                "border: 1px solid palette(mid);"
            )
        self.setStyleSheet(base + style)

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

        self.mode_group = QButtonGroup(self)
        self._mode_to_button: dict[str, QRadioButton] = {}
        self._id_to_mode: dict[int, str] = {}

        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.addWidget(QLabel("Mode:"))
        modes = [
            ("Categories", "categories"),
            ("Allow all", "allow_all"),
            ("Custom list", "custom"),
        ]
        for idx, (label, mode_key) in enumerate(modes):
            radio = QRadioButton(label)
            self.mode_group.addButton(radio, idx)
            self._mode_to_button[mode_key] = radio
            self._id_to_mode[idx] = mode_key
            mode_layout.addWidget(radio)
        mode_layout.addStretch()
        self.mode_group.buttonClicked[int].connect(self._on_mode_button_clicked)
        inner_layout.addLayout(mode_layout)

        self.category_master_container = QWidget()
        master_layout = QHBoxLayout()
        master_layout.setContentsMargins(0, 0, 0, 0)
        self.category_toggles = {}
        self._category_attr = {
            "Code": "include_code",
            "Text": "include_text",
            "Data": "include_data",
        }
        for label, attr in self._category_attr.items():
            box = QCheckBox(label)
            box.stateChanged.connect(partial(self._on_master_category_toggled, attr))
            self.category_toggles[attr] = box
            master_layout.addWidget(box)
        master_layout.addStretch()
        self.category_master_container.setLayout(master_layout)
        inner_layout.addWidget(self.category_master_container)

        self.subset_container = QWidget()
        subset_layout = QVBoxLayout()
        subset_layout.setContentsMargins(0, 0, 0, 0)
        self.subset_buttons: dict[str, dict[str, ExtensionChipButton]] = {}
        for category, subsets in TOP_CATEGORIES.items():
            category_label = QLabel(category)
            category_label.setStyleSheet("font-weight: bold;")
            subset_layout.addWidget(category_label)
            flow_widget = QWidget()
            flow = FlowLayout()
            flow_widget.setLayout(flow)
            buttons = {}
            for subset in subsets:
                chip = ExtensionChipButton(subset)
                tooltip_values = EXTENSION_SETS.get(subset, [])
                if tooltip_values:
                    chip.setToolTip(", ".join(sorted(set(tooltip_values))))
                chip.toggled.connect(partial(self._on_subset_chip_toggled, category, subset))
                buttons[subset] = chip
                flow.addWidget(chip)
            self.subset_buttons[category] = buttons
            subset_layout.addWidget(flow_widget)
        self.subset_container.setLayout(subset_layout)
        inner_layout.addWidget(self.subset_container)

        exclude_row = QHBoxLayout()
        exclude_row.setContentsMargins(0, 0, 0, 0)
        self.exclude_label = QLabel("Exclude extensions:")
        exclude_row.addWidget(self.exclude_label)
        self.excluded_extensions_input = QLineEdit(
            self.ctx.settings.excluded_extensions_text or ""
        )
        self.excluded_extensions_input.setPlaceholderText("e.g., .log, .tmp")
        self.excluded_extensions_input.textChanged.connect(
            self.ctx.settings.set_excluded_extensions_text
        )
        exclude_row.addWidget(self.excluded_extensions_input, 1)
        inner_layout.addLayout(exclude_row)

        self.custom_container = QWidget()
        custom_layout = QVBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(
            QLabel("Custom extensions (comma or newline separated):")
        )
        self.custom_extensions_edit = QTextEdit()
        self.custom_extensions_edit.setPlaceholderText(".py, .md, .json")
        self.custom_extensions_edit.setPlainText(
            self.ctx.settings.custom_extensions_text or ""
        )
        self.custom_extensions_edit.textChanged.connect(self._on_custom_text_changed)
        custom_layout.addWidget(self.custom_extensions_edit)
        self.custom_container.setLayout(custom_layout)
        inner_layout.addWidget(self.custom_container)

        preview_layout = QHBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.allowed_label = QLabel("")
        preview_layout.addWidget(self.allowed_label)
        preview_layout.addStretch()
        self.show_allowed_btn = QPushButton("Show…")
        self.show_allowed_btn.clicked.connect(self.show_allowed_extensions_dialog)
        preview_layout.addWidget(self.show_allowed_btn)
        inner_layout.addLayout(preview_layout)

        reset_btn = QPushButton("Reset File Extensions")
        reset_btn.clicked.connect(self.reset_extensions)
        inner_layout.addWidget(reset_btn)

        self.ctx.settings.extensionFiltersChanged.connect(self._refresh_extension_preview)
        self._sync_extension_controls()
        self._refresh_extension_preview(self.ctx.settings.extension_filters)

        # --- Ignore Filters UI ---
        inner_layout.addSpacing(10)
        ignore_label = QLabel("Ignored Folder Presets:")
        inner_layout.addWidget(ignore_label)

        self.ignore_preset_combo = QComboBox()
        self.ignore_preset_combo.addItems(list(IGNORE_PRESETS.keys()))
        self.ignore_preset_combo.setCurrentText(self.ctx.settings.ignore_preset)
        self.ignore_preset_combo.currentTextChanged.connect(self.on_ignore_preset_changed)
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
        self.ignore_preview_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
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
        self.custom_ignore_field.setPlaceholderText("e.g., node_modules, .git, target")
        self.custom_ignore_field.setText(self.ctx.settings.custom_ignore_list)
        self.custom_ignore_field.textChanged.connect(self.on_custom_ignore_changed)
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

    def _on_mode_button_clicked(self, idx: int):
        mode = self._id_to_mode.get(idx, "categories")
        self.ctx.settings.set_extension_mode(mode)
        self._update_extension_mode_visibility()

    def _on_master_category_toggled(self, attr: str, state: int):
        setter = getattr(self.ctx.settings, f"set_{attr}")
        setter(state == Qt.Checked)
        self._update_subset_enabled_states()

    def _on_subset_chip_toggled(self, category: str, subset: str, checked: bool):
        self.ctx.settings.set_subset_excluded(category, subset, not checked)

    def _on_custom_text_changed(self):
        self.ctx.settings.set_custom_extensions_text(
            self.custom_extensions_edit.toPlainText()
        )

    def _sync_extension_controls(self):
        settings = self.ctx.settings
        mode = settings.extension_mode or "categories"
        for mode_key, button in self._mode_to_button.items():
            button.blockSignals(True)
            button.setChecked(mode_key == mode)
            button.blockSignals(False)

        for attr, checkbox in self.category_toggles.items():
            value = getattr(settings, attr, True)
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(value))
            checkbox.blockSignals(False)

        excluded = settings.excluded_subsets or {}
        for category, buttons in self.subset_buttons.items():
            excluded_set = set(excluded.get(category, []) or [])
            attr_name = self._category_attr.get(category)
            enabled = getattr(settings, attr_name, True) if attr_name else True
            for subset, chip in buttons.items():
                chip.blockSignals(True)
                chip.setChecked(subset not in excluded_set)
                chip.setEnabled(enabled)
                chip.blockSignals(False)

        self.excluded_extensions_input.blockSignals(True)
        self.excluded_extensions_input.setText(settings.excluded_extensions_text or "")
        self.excluded_extensions_input.blockSignals(False)

        self.custom_extensions_edit.blockSignals(True)
        self.custom_extensions_edit.setPlainText(settings.custom_extensions_text or "")
        self.custom_extensions_edit.blockSignals(False)

        self._update_extension_mode_visibility()

    def _update_subset_enabled_states(self):
        for category, buttons in self.subset_buttons.items():
            attr_name = self._category_attr.get(category)
            enabled = getattr(self.ctx.settings, attr_name, True) if attr_name else True
            for chip in buttons.values():
                chip.setEnabled(enabled)

    def _update_extension_mode_visibility(self):
        mode = self.ctx.settings.extension_mode or "categories"
        is_categories = mode == "categories"
        is_custom = mode == "custom"
        self.category_master_container.setVisible(is_categories)
        self.subset_container.setVisible(is_categories)
        self.custom_container.setVisible(is_custom)
        enable_exclude = mode != "allow_all"
        self.exclude_label.setEnabled(enable_exclude)
        self.excluded_extensions_input.setEnabled(enable_exclude)
        self._update_subset_enabled_states()

    def _refresh_extension_preview(self, filters=None):
        if filters is None:
            filters = self.ctx.settings.extension_filters
        mode = self.ctx.settings.extension_mode or "categories"
        if mode == "allow_all":
            self.allowed_label.setText("Allowed extensions: all")
            self.show_allowed_btn.setEnabled(False)
        else:
            count = len(filters or [])
            self.allowed_label.setText(f"Allowed extensions: {count}")
            self.show_allowed_btn.setEnabled(count > 0)

    def show_allowed_extensions_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Allowed extensions")
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        extensions = self.ctx.settings.extension_filters
        mode = self.ctx.settings.extension_mode or "categories"
        if mode == "allow_all":
            text.setPlainText("All extensions are allowed.")
        elif extensions:
            text.setPlainText("\n".join(extensions))
        else:
            text.setPlainText("(no extensions)")
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.resize(360, 420)
        dialog.exec_()

    def reset_extensions(self):
        self.ctx.settings.reset_extension_settings()
        self._sync_extension_controls()
        self._refresh_extension_preview(self.ctx.settings.extension_filters)

        # Update ignore filters UI
        self.ignore_preset_combo.blockSignals(True)
        self.custom_ignore_field.blockSignals(True)
        self.ignore_preset_combo.setCurrentText(self.ctx.settings.ignore_preset)
        self.custom_ignore_field.setText(self.ctx.settings.custom_ignore_list)
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
        self.ignore_count_label.setText(f"{total} item{'s' if total != 1 else ''}")
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
            QApplication.clipboard().setText(", ".join(self._current_ignore_items()))

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
        self.ssh_status_indicator.setStyleSheet(f"color: {color}; font-size: 14px; margin-right: 4px;")
        self.ssh_status_text.setText(text)
