import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion") 
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

from PyQt5.QtWidgets import QApplication

from main_window import MainWindow


class TestMainWindowTabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_add_and_close_workspace_tabs(self):
        window = MainWindow()
        try:
            initial_count = len(window.workspace_tabs)
            self.assertGreaterEqual(initial_count, 1)

            window.add_workspace_tab()
            self.assertEqual(len(window.workspace_tabs), initial_count + 1)

            settings_index = window.tabs.indexOf(window.settings_tab)
            self.assertEqual(settings_index, window.tabs.count() - 1)

            first_index = window.tabs.indexOf(window.workspace_tabs[0])
            window.close_workspace_tab(first_index)
            self.assertEqual(len(window.workspace_tabs), initial_count)

            remaining_index = window.tabs.indexOf(window.workspace_tabs[0])
            window.close_workspace_tab(remaining_index)
            self.assertEqual(len(window.workspace_tabs), 1)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
