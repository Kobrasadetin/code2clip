# settings_store.py
from __future__ import annotations
from typing import Dict, List
from PyQt5.QtCore import QObject, pyqtSignal, QSettings

from extension_filters import (
    EXTENSION_GROUP_DEFAULTS,
    DEFAULT_EXTENSION_CATEGORIES,
    parse_categories,
    parse_extensions,
    build_extension_filters,
)

class AppSettings(QObject):
    # High-level signals
    changed = pyqtSignal()
    themeChanged = pyqtSignal(bool)
    sshConfigChanged = pyqtSignal(str, str)               # host, username
    extensionFiltersChanged = pyqtSignal(object)          # new filters

    def __init__(self, org: str = "Dynamint", app: str = "FileConcatenator"):
        super().__init__()
        self._qs = QSettings(org, app)

        # Load
        self.use_dark_mode: bool = self._qs.value("use_dark_mode", False, type=bool)
        self.show_success_message: bool = self._qs.value("show_success_message", True, type=bool)
        self.interpret_escape_sequences: bool = self._qs.value("interpret_escape_sequences", True, type=bool)

        self.extension_allow_all: bool = self._qs.value("extension_allow_all", False, type=bool)
        cat_default = ",".join(DEFAULT_EXTENSION_CATEGORIES)
        cat_text = self._qs.value("extension_categories", cat_default, type=str)
        self.extension_categories: List[str] = parse_categories(cat_text)

        self.extension_group_texts: Dict[str, str] = {}
        self.extension_groups: Dict[str, List[str]] = {}
        for name, default_list in EXTENSION_GROUP_DEFAULTS.items():
            key = f"extensions_{name.replace(' ', '_').lower()}"
            default_text = ",".join(default_list)
            text = self._qs.value(key, default_text, type=str)
            self.extension_group_texts[name] = text
            self.extension_groups[name] = parse_extensions(text)

        self.extension_filters = build_extension_filters(
            self.extension_categories, self.extension_allow_all, self.extension_groups
        )

        self.ssh_host: str = self._qs.value("ssh_host", "", type=str)
        self.ssh_username: str = self._qs.value("ssh_username", "", type=str)

        self.last_preset: str = self._qs.value("last_preset", "Markdown", type=str)
        self.custom_prefix: str = self._qs.value("custom_prefix", "", type=str)
        self.custom_suffix: str = self._qs.value("custom_suffix", "", type=str)

    # -------- persist ----------
    def save(self) -> None:
        self._qs.setValue("use_dark_mode", self.use_dark_mode)
        self._qs.setValue("show_success_message", self.show_success_message)
        self._qs.setValue("interpret_escape_sequences", self.interpret_escape_sequences)

        self._qs.setValue("extension_allow_all", self.extension_allow_all)
        self._qs.setValue("extension_categories", ",".join(self.extension_categories))

        for name, text in self.extension_group_texts.items():
            key = f"extensions_{name.replace(' ', '_').lower()}"
            self._qs.setValue(key, text)

        self._qs.setValue("ssh_host", self.ssh_host or "")
        self._qs.setValue("ssh_username", self.ssh_username or "")
        self._qs.setValue("last_preset", self.last_preset or "")
        self._qs.setValue("custom_prefix", self.custom_prefix or "")
        self._qs.setValue("custom_suffix", self.custom_suffix or "")
        self.changed.emit()

    # -------- setters with signals ----------
    def set_use_dark_mode(self, value: bool):
        if self.use_dark_mode != value:
            self.use_dark_mode = value
            self.save()
            self.themeChanged.emit(value)

    def set_show_success_message(self, value: bool):
        if self.show_success_message != value:
            self.show_success_message = value
            self.save()

    def set_interpret_escape_sequences(self, value: bool):
        if self.interpret_escape_sequences != value:
            self.interpret_escape_sequences = value
            self.save()

    def set_ssh(self, host: str, username: str):
        changed = (self.ssh_host != host) or (self.ssh_username != username)
        if changed:
            self.ssh_host = host
            self.ssh_username = username
            self.save()
            self.sshConfigChanged.emit(host, username)

    def set_extension_allow_all(self, value: bool):
        if self.extension_allow_all != value:
            self.extension_allow_all = value
            self._rebuild_filters()

    def set_extension_categories(self, categories: List[str]):
        if categories != self.extension_categories:
            self.extension_categories = categories
            self._rebuild_filters()

    def set_extension_group_text(self, name: str, text: str):
        if self.extension_group_texts.get(name) != text:
            self.extension_group_texts[name] = text
            self.extension_groups[name] = parse_extensions(text)
            self._rebuild_filters()

    def reset_extension_settings(self):
        self.extension_categories = list(DEFAULT_EXTENSION_CATEGORIES)
        self.extension_allow_all = False
        self.extension_group_texts = {n: ",".join(v) for n, v in EXTENSION_GROUP_DEFAULTS.items()}
        self.extension_groups = {n: list(v) for n, v in EXTENSION_GROUP_DEFAULTS.items()}
        self._rebuild_filters()

    def set_last_preset(self, preset: str):
        if self.last_preset != preset:
            self.last_preset = preset
            self.save()

    def set_custom_prefix(self, prefix: str):
        if self.custom_prefix != prefix:
            self.custom_prefix = prefix
            self.save()

    def set_custom_suffix(self, suffix: str):
        if self.custom_suffix != suffix:
            self.custom_suffix = suffix
            self.save()

    def _rebuild_filters(self):
        self.extension_filters = build_extension_filters(
            self.extension_categories, self.extension_allow_all, self.extension_groups
        )
        self.save()
        self.extensionFiltersChanged.emit(self.extension_filters)
