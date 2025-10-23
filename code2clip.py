import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer
from app_context import AppContext
from main_window import MainWindow
from settings_tab import default_password_prompt
from utils import resource_path, get_app_version

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Setup splash screen
    splash_pix = QPixmap(resource_path("gui/splash.png"))
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setFont(QFont("Arial", 10))
    splash.showMessage(f"{get_app_version()}", alignment=Qt.AlignBottom | Qt.AlignHCenter)
    splash.show()
    app.processEvents()

    ctx = AppContext(password_provider=None)
    ctx.ssh.password_provider = lambda: default_password_prompt(
        parent=app.activeWindow(),
        user=ctx.settings.ssh_username,
        host=ctx.settings.ssh_host,
    )

    # Create the main window
    window = MainWindow(ctx)

    # show the window and finish splash
    window.show()
    QTimer.singleShot(200, lambda: splash.finish(window))

    sys.exit(app.exec_())