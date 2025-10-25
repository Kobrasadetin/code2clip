# settings_store.py
from __future__ import annotations
import json
from typing import Dict, List, Set
from PyQt5.QtCore import QObject, pyqtSignal, QSettings

from extension_filters import (
    EXTENSION_GROUP_DEFAULTS,
    DEFAULT_EXTENSION_CATEGORIES,
    parse_categories,
    parse_extensions,
)
from extension_compute import compute_extension_filters
from ignore_filters import (
    IGNORE_PRESETS,
    DEFAULT_IGNORE_PRESET,
    get_ignore_set,
    parse_ignore_list,
)

class AppSettings(QObject):
    # High-level signals
    changed = pyqtSignal()
    themeChanged = pyqtSignal(bool)
    sshConfigChanged = pyqtSignal(str, str)               # host, username
    extensionFiltersChanged = pyqtSignal(object)          # new filters
    ignoreFiltersChanged = pyqtSignal(object)             # new ignore filters

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

        # --- New extension controls ---
        self.extension_mode: str = self._qs.value("extension_mode", "categories", type=str)
        self.include_code: bool = self._qs.value("include_code", True, type=bool)
        self.include_text: bool = self._qs.value("include_text", True, type=bool)
        self.include_data: bool = self._qs.value("include_data", True, type=bool)

        excluded_json = self._qs.value("excluded_subsets", "{}", type=str)
        try:
            self.excluded_subsets: Dict[str, List[str]] = json.loads(excluded_json) or {}
        except Exception:
            self.excluded_subsets = {}

        self.excluded_extensions_text: str = self._qs.value(
            "excluded_extensions_text", "", type=str
        )
        self.custom_extensions_text: str = self._qs.value("custom_extensions_text", "", type=str)

        self.extension_filters = compute_extension_filters(self)

        # --- New Ignore Filters ---
        self.ignore_preset: str = self._qs.value("ignore_preset", DEFAULT_IGNORE_PRESET, type=str)
        self.custom_ignore_list: str = self._qs.value("custom_ignore_list", "", type=str)
        self.ignore_filters: Set[str] = get_ignore_set(self.ignore_preset, self.custom_ignore_list)
        # --- End New ---

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

        # Persist new extension controls
        self._qs.setValue("extension_mode", self.extension_mode)
        self._qs.setValue("include_code", self.include_code)
        self._qs.setValue("include_text", self.include_text)
        self._qs.setValue("include_data", self.include_data)
        self._qs.setValue("excluded_subsets", json.dumps(self.excluded_subsets or {}))
        self._qs.setValue("excluded_extensions_text", self.excluded_extensions_text or "")
        self._qs.setValue("custom_extensions_text", self.custom_extensions_text or "")

        # --- New ---
        self._qs.setValue("ignore_preset", self.ignore_preset or DEFAULT_IGNORE_PRESET)
        self._qs.setValue("custom_ignore_list", self.custom_ignore_list or "")
        # --- End New ---

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
            if value:
                self.set_extension_mode("allow_all")
            elif self.extension_mode == "allow_all":
                self.set_extension_mode("categories")
            else:
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

    def set_extension_mode(self, mode: str):
        if mode not in {"categories", "allow_all", "custom"}:
            mode = "categories"
        if self.extension_mode != mode:
            self.extension_mode = mode
            self._rebuild_filters()

    def set_include_code(self, value: bool):
        if self.include_code != value:
            self.include_code = value
            self._rebuild_filters()

    def set_include_text(self, value: bool):
        if self.include_text != value:
            self.include_text = value
            self._rebuild_filters()

    def set_include_data(self, value: bool):
        if self.include_data != value:
            self.include_data = value
            self._rebuild_filters()

    def set_excluded_subsets(self, mapping: Dict[str, List[str]]):
        if mapping != self.excluded_subsets:
            self.excluded_subsets = mapping
            self._rebuild_filters()

    def set_subset_excluded(self, category: str, subset: str, excluded: bool):
        current = list(self.excluded_subsets.get(category, []))
        changed = False
        if excluded and subset not in current:
            current.append(subset)
            changed = True
        elif not excluded and subset in current:
            current.remove(subset)
            changed = True

        if changed:
            mapping = dict(self.excluded_subsets)
            if current:
                mapping[category] = sorted(set(current))
            elif category in mapping:
                mapping.pop(category)
            self.set_excluded_subsets(mapping)

    def set_excluded_extensions_text(self, text: str):
        if self.excluded_extensions_text != text:
            self.excluded_extensions_text = text
            self._rebuild_filters()

    def set_custom_extensions_text(self, text: str):
        if self.custom_extensions_text != text:
            self.custom_extensions_text = text
            self._rebuild_filters()

    def set_ignore_preset(self, preset_name: str):
        if preset_name not in IGNORE_PRESETS:
            preset_name = DEFAULT_IGNORE_PRESET
        if self.ignore_preset != preset_name:
            self.ignore_preset = preset_name
            self._rebuild_ignore_filters()

    def set_custom_ignore_list(self, text: str):
        if self.custom_ignore_list != text:
            self.custom_ignore_list = text
            if self.ignore_preset == "Custom":
                self._rebuild_ignore_filters()
            else:
                self.save()

    def reset_ignore_filters(self):
        self.ignore_preset = DEFAULT_IGNORE_PRESET
        self.custom_ignore_list = ""
        self._rebuild_ignore_filters()

    def reset_extension_settings(self):
        self.extension_categories = list(DEFAULT_EXTENSION_CATEGORIES)
        self.extension_allow_all = False
        self.extension_group_texts = {n: ",".join(v) for n, v in EXTENSION_GROUP_DEFAULTS.items()}
        self.extension_groups = {n: list(v) for n, v in EXTENSION_GROUP_DEFAULTS.items()}
        self.extension_mode = "categories"
        self.include_code = True
        self.include_text = True
        self.include_data = True
        self.excluded_subsets = {}
        self.excluded_extensions_text = ""
        self.custom_extensions_text = ""
        self._rebuild_filters()
        self.reset_ignore_filters()

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
        self.extension_filters = compute_extension_filters(self)
        self.save()
        self.extensionFiltersChanged.emit(self.extension_filters)

    def _rebuild_ignore_filters(self):
        if self.ignore_preset == "Custom":
            self.ignore_filters = parse_ignore_list(self.custom_ignore_list)
        else:
            self.ignore_filters = get_ignore_set(
                self.ignore_preset, self.custom_ignore_list
            )
        self.save()
        self.ignoreFiltersChanged.emit(self.ignore_filters)
