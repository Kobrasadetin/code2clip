from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QToolButton, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
import platform

from app_context import AppContext
from utils import resource_path
from main_window_styles import apply_app_palette, update_tab_close_buttons, enable_os_override_title_bar

class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        # Lazy-import tabs only when GUI is starting up
        from concatenator_tab import ConcatenatorTab
        from settings_tab import SettingsTab

        self.setWindowTitle("File Concatenator")
        self.resize(600, 400)

        icon = QIcon()
        icon.addFile(resource_path("gui/icon_32.png"), QSize(32, 32))
        icon.addFile(resource_path("gui/icon_48.png"), QSize(48, 48))
        icon.addFile(resource_path("gui/icon_256.png"), QSize(256, 256))
        self.setWindowIcon(icon)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.tabCloseRequested.connect(self.close_workspace_tab)

        self.new_tab_button = QToolButton()
        self.new_tab_button.setText("+")
        self.new_tab_button.setAutoRaise(True)
        self.new_tab_button.clicked.connect(self.add_workspace_tab)
        self.tabs.setCornerWidget(self.new_tab_button, Qt.TopRightCorner)

        self._concatenator_tab_cls = ConcatenatorTab
        self.workspace_tabs = []
        self.workspace_counter = 0

        self.settings_tab = SettingsTab(self.ctx)  # pass context, not main_window
        self.add_workspace_tab()
        self.tabs.addTab(self.settings_tab, "Settings")
        update_tab_close_buttons(self.tabs, self.settings_tab, self._close_workspace_widget)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        main_widget.setLayout(layout)

        if platform.system() == "Windows":
            hwnd = self.winId().__int__()
            enable_os_override_title_bar(hwnd)

        # ---- Signals wiring ----
        self.ctx.settings.themeChanged.connect(self._apply_palette)
        self.ctx.settings.extensionFiltersChanged.connect(lambda _: self._redraw_tabs())
        self.ctx.ssh.statusChanged.connect(self._on_ssh_status_changed)
        self.ctx.ssh.error.connect(self._show_error)

        self._apply_palette(self.ctx.settings.use_dark_mode)
        self._redraw_tabs()

    # ---- UI plumbing only ----
    def add_workspace_tab(self):
        tab_cls = getattr(self, "_concatenator_tab_cls", None)
        if tab_cls is None:
            from concatenator_tab import ConcatenatorTab as tab_cls
            self._concatenator_tab_cls = tab_cls
        new_tab = tab_cls(self.ctx)  # pass context
        self.workspace_tabs.append(new_tab)
        self.workspace_counter += 1
        title = f"Workspace {self.workspace_counter}"
        settings_index = self.tabs.indexOf(self.settings_tab) if self.settings_tab else -1
        if settings_index >= 0:
            index = self.tabs.insertTab(settings_index, new_tab, title)
        else:
            index = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(index)
        update_tab_close_buttons(self.tabs, self.settings_tab, self._close_workspace_widget)
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
            update_tab_close_buttons(self.tabs, self.settings_tab, self._close_workspace_widget)

    def _close_workspace_widget(self, widget: QWidget) -> None:
        index = self.tabs.indexOf(widget)
        if index != -1:
            self.close_workspace_tab(index)

    def _apply_palette(self, use_dark: bool):
        app = QApplication.instance()
        apply_app_palette(app, use_dark)
        update_tab_close_buttons(self.tabs, self.settings_tab, self._close_workspace_widget)

    def _redraw_tabs(self):
        for tab in self.workspace_tabs:
            if hasattr(tab, "redraw"):
                tab.redraw()
        if hasattr(self.settings_tab, "redraw"):
            self.settings_tab.redraw()

    def _on_ssh_status_changed(self, connected: bool):
        # SettingsTab listens to controller too, so this is optional.
        pass

    def _show_error(self, message: str):
        QMessageBox.warning(self, "SSH Connection", message)

    def closeEvent(self, event):
        try:
            self.ctx.ssh.disconnect()
        finally:
            super().closeEvent(event)
