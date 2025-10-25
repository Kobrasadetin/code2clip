from __future__ import annotations

from typing import Dict

from PyQt5.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QToolButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QWidgetItem,
)

from extension_sets import EXTENSION_SETS, TOP_CATEGORIES


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
        size += QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )
        return size

    def _do_layout(self, rect: QRect, test_only: bool):
        spacing = self.spacing()
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(
            margins.left(),
            margins.top(),
            -margins.right(),
            -margins.bottom(),
        )

        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            widget = item.widget()
            if widget is None or not widget.isVisible():
                continue

            hint = item.sizeHint()
            next_x = x + hint.width() + spacing
            if next_x - spacing > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + spacing
                next_x = x + hint.width() + spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + margins.bottom()


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

    def refresh_style(self):
        self._update_style(self.isChecked())

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


class ExtensionFiltersWidget(QWidget):
    """Encapsulates the extension filtering controls in the settings tab."""

    extensionsReset = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._mode_to_button: Dict[str, QRadioButton] = {}
        self._id_to_mode: Dict[int, str] = {}
        self.category_toggles: Dict[str, QCheckBox] = {}
        self._category_attr = {
            "Code": "include_code",
            "Text": "include_text",
            "Data": "include_data",
        }
        self.subset_buttons: Dict[str, Dict[str, ExtensionChipButton]] = {}

        self._build_ui()

        self.settings.extensionFiltersChanged.connect(
            self._refresh_extension_preview
        )
        self._sync_extension_controls()
        self._refresh_extension_preview(self.settings.extension_filters)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("File Type Filters:"))

        self.mode_group = QButtonGroup(self)
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
        layout.addLayout(mode_layout)

        self.category_master_container = QWidget()
        master_layout = QHBoxLayout()
        master_layout.setContentsMargins(0, 0, 0, 0)
        for label, attr in self._category_attr.items():
            box = QCheckBox(label)
            box.stateChanged.connect(
                lambda state, attr=attr: self._on_master_category_toggled(
                    attr, state
                )
            )
            self.category_toggles[attr] = box
            master_layout.addWidget(box)
        master_layout.addStretch()
        self.category_master_container.setLayout(master_layout)
        layout.addWidget(self.category_master_container)

        self.subset_container = QWidget()
        subset_layout = QVBoxLayout()
        subset_layout.setContentsMargins(0, 0, 0, 0)
        for category, subsets in TOP_CATEGORIES.items():
            category_label = QLabel(category)
            category_label.setStyleSheet("font-weight: bold;")
            subset_layout.addWidget(category_label)
            flow_widget = QWidget()
            flow = FlowLayout()
            flow_widget.setLayout(flow)
            buttons: Dict[str, ExtensionChipButton] = {}
            for subset in subsets:
                chip = ExtensionChipButton(subset)
                tooltip_values = EXTENSION_SETS.get(subset, [])
                if tooltip_values:
                    chip.setToolTip(", ".join(sorted(set(tooltip_values))))
                chip.toggled.connect(
                    lambda checked, category=category, subset=subset: self._on_subset_chip_toggled(
                        category, subset, checked
                    )
                )
                buttons[subset] = chip
                flow.addWidget(chip)
            self.subset_buttons[category] = buttons
            subset_layout.addWidget(flow_widget)
        self.subset_container.setLayout(subset_layout)
        layout.addWidget(self.subset_container)

        include_row = QHBoxLayout()
        include_row.setContentsMargins(0, 0, 0, 0)
        self.include_label = QLabel("Include extensions:")
        include_row.addWidget(self.include_label)
        self.included_extensions_input = QLineEdit(
            self.settings.included_extensions_text or ""
        )
        self.included_extensions_input.setPlaceholderText("e.g., .svg, .blend")
        self.included_extensions_input.textChanged.connect(
            self.settings.set_included_extensions_text
        )
        include_row.addWidget(self.included_extensions_input, 1)
        layout.addLayout(include_row)

        exclude_row = QHBoxLayout()
        exclude_row.setContentsMargins(0, 0, 0, 0)
        self.exclude_label = QLabel("Exclude extensions:")
        exclude_row.addWidget(self.exclude_label)
        self.excluded_extensions_input = QLineEdit(
            self.settings.excluded_extensions_text or ""
        )
        self.excluded_extensions_input.setPlaceholderText("e.g., .log, .tmp")
        self.excluded_extensions_input.textChanged.connect(
            self.settings.set_excluded_extensions_text
        )
        exclude_row.addWidget(self.excluded_extensions_input, 1)
        layout.addLayout(exclude_row)

        self.custom_container = QWidget()
        custom_layout = QVBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(
            QLabel("Custom extensions (comma or newline separated):")
        )
        self.custom_extensions_edit = QTextEdit()
        self.custom_extensions_edit.setPlaceholderText(".py, .md, .json")
        self.custom_extensions_edit.setPlainText(
            self.settings.custom_extensions_text or ""
        )
        self.custom_extensions_edit.textChanged.connect(
            self._on_custom_text_changed
        )
        custom_layout.addWidget(self.custom_extensions_edit)
        self.custom_container.setLayout(custom_layout)
        layout.addWidget(self.custom_container)

        preview_layout = QHBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.allowed_label = QLabel("")
        preview_layout.addWidget(self.allowed_label)
        preview_layout.addStretch()
        self.show_allowed_btn = QPushButton("Show…")
        self.show_allowed_btn.clicked.connect(
            self.show_allowed_extensions_dialog
        )
        preview_layout.addWidget(self.show_allowed_btn)
        layout.addLayout(preview_layout)

        self.reset_button = QPushButton("Reset File Extensions")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        layout.addWidget(self.reset_button)

    def _on_mode_button_clicked(self, idx: int):
        mode = self._id_to_mode.get(idx, "categories")
        self.settings.set_extension_mode(mode)
        self._update_extension_mode_visibility()

    def _on_master_category_toggled(self, attr: str, state: int):
        setter = getattr(self.settings, f"set_{attr}")
        setter(state == Qt.Checked)
        self._update_subset_enabled_states()

    def _on_subset_chip_toggled(
        self, category: str, subset: str, checked: bool
    ):
        self.settings.set_subset_excluded(category, subset, not checked)

    def _on_custom_text_changed(self):
        self.settings.set_custom_extensions_text(
            self.custom_extensions_edit.toPlainText()
        )

    def _sync_extension_controls(self):
        mode = self.settings.extension_mode or "categories"
        for mode_key, button in self._mode_to_button.items():
            button.blockSignals(True)
            button.setChecked(mode_key == mode)
            button.blockSignals(False)

        for attr, checkbox in self.category_toggles.items():
            value = getattr(self.settings, attr, True)
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(value))
            checkbox.blockSignals(False)

        excluded = self.settings.excluded_subsets or {}
        for category, buttons in self.subset_buttons.items():
            excluded_set = set(excluded.get(category, []) or [])
            attr_name = self._category_attr.get(category)
            enabled = getattr(self.settings, attr_name, True) if attr_name else True
            for subset, chip in buttons.items():
                chip.blockSignals(True)
                chip.setChecked(subset not in excluded_set)
                chip.refresh_style()
                chip.setEnabled(enabled)
                chip.blockSignals(False)

        self.included_extensions_input.blockSignals(True)
        self.included_extensions_input.setText(
            self.settings.included_extensions_text or ""
        )
        self.included_extensions_input.blockSignals(False)

        self.excluded_extensions_input.blockSignals(True)
        self.excluded_extensions_input.setText(
            self.settings.excluded_extensions_text or ""
        )
        self.excluded_extensions_input.blockSignals(False)

        self.custom_extensions_edit.blockSignals(True)
        self.custom_extensions_edit.setPlainText(
            self.settings.custom_extensions_text or ""
        )
        self.custom_extensions_edit.blockSignals(False)

        self._update_extension_mode_visibility()

    def _update_subset_enabled_states(self):
        for category, buttons in self.subset_buttons.items():
            attr_name = self._category_attr.get(category)
            enabled = getattr(self.settings, attr_name, True) if attr_name else True
            for chip in buttons.values():
                chip.setEnabled(enabled)
                chip.refresh_style()

    def _update_extension_mode_visibility(self):
        mode = self.settings.extension_mode or "categories"
        is_categories = mode == "categories"
        is_custom = mode == "custom"
        self.category_master_container.setVisible(is_categories)
        self.subset_container.setVisible(is_categories)
        self.custom_container.setVisible(is_custom)
        self.include_label.setVisible(is_categories)
        self.included_extensions_input.setVisible(is_categories)
        enable_exclude = mode != "allow_all"
        self.exclude_label.setEnabled(enable_exclude)
        self.excluded_extensions_input.setEnabled(enable_exclude)
        self._update_subset_enabled_states()

    def _refresh_extension_preview(self, filters=None):
        if filters is None:
            filters = self.settings.extension_filters
        mode = self.settings.extension_mode or "categories"
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
        extensions = self.settings.extension_filters
        mode = self.settings.extension_mode or "categories"
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

    def reset_to_defaults(self):
        self.settings.reset_extension_settings()
        self._sync_extension_controls()
        self._refresh_extension_preview(self.settings.extension_filters)
        self.extensionsReset.emit()

    def refresh_from_settings(self):
        """Re-synchronise UI state if settings are mutated externally."""
        self._sync_extension_controls()
        self._refresh_extension_preview(self.settings.extension_filters)

