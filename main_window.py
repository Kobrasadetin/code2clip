import sys
import platform
import ctypes
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QApplication
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtCore import QSettings, QSize
from concatenator_tab import ConcatenatorTab
from settings_tab import SettingsTab
import os

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
        self.setWindowTitle("File Concatenator")
        self.resize(600, 400)

         # Set window icon
        icon = QIcon()
        icon.addFile(os.path.join("gui", "icon_32.png"), QSize(32, 32))
        icon.addFile(os.path.join("gui", "icon_48.png"), QSize(48, 48))
        icon.addFile(os.path.join("gui", "icon_256.png"), QSize(256, 256))
        self.setWindowIcon(icon)

        # Load persistent settings via QSettings.
        self.settings = QSettings("Dynamint", "FileConcatenator")
        self.use_dark_mode = self.settings.value("use_dark_mode", False, type=bool)
        self.show_success_message = self.settings.value("show_success_message", True, type=bool)
        self.interpret_escape_sequences = self.settings.value("interpret_escape_sequences", True, type=bool)

        # Create the central widget with a tab widget.
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.tabs = QTabWidget()
        self.concatenator_tab = ConcatenatorTab(self)
        self.settings_tab = SettingsTab(self)
        self.tabs.addTab(self.concatenator_tab, "Concatenator")
        self.tabs.addTab(self.settings_tab, "Settings")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        main_widget.setLayout(layout)

        if platform.system() == "Windows":
            hwnd = self.winId().__int__()
            enable_os_override_title_bar(hwnd)

        self.redraw()

        self.show()

    def redraw(self):
        self.apply_dark_mode()
        """Redraw all dynamic UI elements if necessary."""
        self.concatenator_tab.redraw()
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
        self.redraw()
