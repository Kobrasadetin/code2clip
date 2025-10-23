import sys
import platform
import ctypes
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QTabBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtCore import QSettings, QSize, Qt

from extension_filters import (
    EXTENSION_GROUP_DEFAULTS,
    DEFAULT_EXTENSION_CATEGORIES,
    parse_categories,
    parse_extensions,
    build_extension_filters,
)

import os

from utils import resource_path
from ssh_utilities import SSHConnectionManager

def enable_os_override_title_bar(hwnd):
    """Force a dark title bar on Windows 10 (1809+) when dark mode is enabled."""
    if platform.system() == "Windows":
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # Supported on Windows 10 1809+ and Windows 11
            is_dark_mode = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(is_dark_mode),
                ctypes.sizeof(is_dark_mode)
            )
        except Exception as e:
            print("Could not enable dark title bar:", e, file=sys.stderr)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Lazy-import tabs only when GUI is starting up
        from concatenator_tab import ConcatenatorTab
        from settings_tab import SettingsTab

        self.setWindowTitle("File Concatenator")
        self.resize(600, 400)

         # Set window icon
        icon = QIcon()
        icon.addFile(resource_path("gui/icon_32.png"), QSize(32, 32))
        icon.addFile(resource_path("gui/icon_48.png"), QSize(48, 48))
        icon.addFile(resource_path("gui/icon_256.png"), QSize(256, 256))
        self.setWindowIcon(icon)

        # Load persistent settings via QSettings.
        self.settings = QSettings("Dynamint", "FileConcatenator")
        self.use_dark_mode = self.settings.value("use_dark_mode", False, type=bool)
        self.show_success_message = self.settings.value("show_success_message", True, type=bool)
        self.interpret_escape_sequences = self.settings.value("interpret_escape_sequences", True, type=bool)
        self.extension_allow_all = self.settings.value(
            "extension_allow_all", False, type=bool
        )
        cat_default = ",".join(DEFAULT_EXTENSION_CATEGORIES)
        cat_text = self.settings.value("extension_categories", cat_default, type=str)
        self.extension_categories = parse_categories(cat_text)

        self.extension_group_texts: dict[str, str] = {}
        self.extension_groups: dict[str, list[str]] = {}
        for name, default_list in EXTENSION_GROUP_DEFAULTS.items():
            key = f"extensions_{name.replace(' ', '_').lower()}"
            default_text = ",".join(default_list)
            text = self.settings.value(key, default_text, type=str)
            self.extension_group_texts[name] = text
            self.extension_groups[name] = parse_extensions(text)

        self.extension_filters = build_extension_filters(
            self.extension_categories, self.extension_allow_all, self.extension_groups
        )

        ssh_host = self.settings.value("ssh_host", "", type=str)
        ssh_user = self.settings.value("ssh_username", "", type=str)
        self.ssh_manager = SSHConnectionManager(ssh_host or None, ssh_user or None)

        # Create the central widget with a tab widget.
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_workspace_tab)

        self.new_tab_button = QToolButton()
        self.new_tab_button.setText("+")
        self.new_tab_button.clicked.connect(self.add_workspace_tab)
        self.tabs.setCornerWidget(self.new_tab_button, Qt.TopRightCorner)

        self._concatenator_tab_cls = ConcatenatorTab
        self.workspace_tabs: list = []
        self.workspace_counter = 0

        self.settings_tab = SettingsTab(self)
        self.add_workspace_tab()
        self.tabs.addTab(self.settings_tab, "Settings")
        self._update_tab_close_buttons()

        self.settings_tab.update_ssh_status(self.is_ssh_connected())

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        main_widget.setLayout(layout)

        if platform.system() == "Windows":
            hwnd = self.winId().__int__()
            enable_os_override_title_bar(hwnd)

        self.redraw()


    def add_workspace_tab(self):
        tab_cls = getattr(self, "_concatenator_tab_cls", None)
        if tab_cls is None:
            from concatenator_tab import ConcatenatorTab as tab_cls  # Lazy import fallback
            self._concatenator_tab_cls = tab_cls
        new_tab = tab_cls(self)
        self.workspace_tabs.append(new_tab)
        self.workspace_counter += 1
        title = f"Workspace {self.workspace_counter}"
        settings_index = self.tabs.indexOf(self.settings_tab) if hasattr(self, "settings_tab") else -1
        if settings_index >= 0:
            index = self.tabs.insertTab(settings_index, new_tab, title)
        else:
            index = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(index)
        self._update_tab_close_buttons()
        return new_tab

    def close_workspace_tab(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if widget is None or widget is self.settings_tab:
            return
        if widget not in self.workspace_tabs:
            return
        self.workspace_tabs.remove(widget)
        self.tabs.removeTab(index)
        widget.deleteLater()
        if not self.workspace_tabs:
            self.add_workspace_tab()
        else:
            self._update_tab_close_buttons()

    def _update_tab_close_buttons(self) -> None:
        tab_bar = self.tabs.tabBar()
        if hasattr(self, "settings_tab"):
            settings_index = self.tabs.indexOf(self.settings_tab)
            if settings_index != -1:
                for side in (QTabBar.LeftSide, QTabBar.RightSide):
                    tab_bar.setTabButton(settings_index, side, None)

    def redraw(self):
        """Redraw all dynamic UI elements if necessary."""
        self.apply_dark_mode()
        for tab in self.workspace_tabs:
            tab.redraw()
        self.settings_tab.redraw()

    def apply_dark_mode(self):
        """Applies the dark palette if dark mode is enabled; otherwise, reverts to the standard palette."""
        app = QApplication.instance()
        if self.use_dark_mode:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
            app.setPalette(dark_palette)
        else:
            app.setPalette(app.style().standardPalette())

    def save_settings(self):
        """Persist settings to disk."""
        self.settings.setValue("use_dark_mode", self.use_dark_mode)
        self.settings.setValue("show_success_message", self.show_success_message)
        self.settings.setValue("interpret_escape_sequences", self.interpret_escape_sequences)
        self.settings.setValue(
            "extension_allow_all", self.extension_allow_all
        )
        self.settings.setValue(
            "extension_categories", ",".join(self.extension_categories)
        )
        for name, text in self.extension_group_texts.items():
            key = f"extensions_{name.replace(' ', '_').lower()}"
            self.settings.setValue(key, text)
        self.settings.setValue("ssh_host", self.ssh_manager.host or "")
        self.settings.setValue("ssh_username", self.ssh_manager.username or "")
        self.redraw()

    def set_extension_allow_all(self, state: bool):
        self.extension_allow_all = state
        self.extension_filters = build_extension_filters(
            self.extension_categories,
            self.extension_allow_all,
            self.extension_groups,
        )
        self.save_settings()

    def set_extension_categories(self, categories: list[str]):
        self.extension_categories = categories
        self.extension_filters = build_extension_filters(
            self.extension_categories,
            self.extension_allow_all,
            self.extension_groups,
        )
        self.save_settings()

    def set_extension_group_text(self, name: str, text: str):
        self.extension_group_texts[name] = text
        self.extension_groups[name] = parse_extensions(text)
        self.extension_filters = build_extension_filters(
            self.extension_categories,
            self.extension_allow_all,
            self.extension_groups,
        )
        self.save_settings()

    def set_ssh_settings(self, host: str, username: str) -> None:
        self.ssh_manager.configure(host, username)
        self.save_settings()
        if hasattr(self, "settings_tab"):
            self.settings_tab.update_ssh_status(self.is_ssh_connected())

    def connect_to_ssh(self) -> None:
        if not self.ssh_manager.is_configured():
            QMessageBox.warning(
                self,
                "SSH Connection",
                "Please enter an SSH host and username before connecting.",
            )
            if hasattr(self, "settings_tab"):
                self.settings_tab.update_ssh_status(False)
            return

        self.ssh_manager.ensure_connection()
        is_connected = self.is_ssh_connected()
        if hasattr(self, "settings_tab"):
            self.settings_tab.update_ssh_status(is_connected)
        if is_connected:
            QMessageBox.information(
                self, "SSH Connection", "SSH connection established successfully."
            )

    def is_ssh_connected(self) -> bool:
        return self.ssh_manager.is_connected()

    def reset_extension_settings(self):
        self.extension_categories = list(DEFAULT_EXTENSION_CATEGORIES)
        self.extension_allow_all = False
        self.extension_group_texts = {
            name: ",".join(vals) for name, vals in EXTENSION_GROUP_DEFAULTS.items()
        }
        self.extension_groups = {
            name: list(vals) for name, vals in EXTENSION_GROUP_DEFAULTS.items()
        }
        self.extension_filters = build_extension_filters(
            self.extension_categories,
            self.extension_allow_all,
            self.extension_groups,
        )
        self.save_settings()

    def closeEvent(self, event):
        try:
            if getattr(self, "ssh_manager", None):
                self.ssh_manager.close()
        finally:
            super().closeEvent(event)
