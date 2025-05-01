import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap, QFont
from main_window import MainWindow
import time

from utils import resource_path

def get_app_version():
    try:
        return open("code2clip_version.txt").read().strip()
    except:
        return "Loading..."

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Setup splash screen
    splash_pix = QPixmap(resource_path("gui/splash.png"))
    splash = QSplashScreen(splash_pix)
    splash.setFont(QFont("Arial", 10))
    splash.showMessage(f"{get_app_version()}", alignment=0x84)  # Align bottom-center
    splash.show()
    app.processEvents()

    # Load main window
    window = MainWindow()

    splash.finish(window)
    sys.exit(app.exec_())
