import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

from PyQt5.QtWidgets import QApplication

from main_window import MainWindow


class TestMainWindowTabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_workspace_tabs_are_independent(self):
        window = MainWindow()
        try:
            self.assertEqual(len(window.workspace_tabs), 1)
            first_tab = window.workspace_tabs[0]
            first_tab.list_widget.add_file("/tmp/a.txt", enforce_filter=False)

            second_tab = window.add_workspace_tab()
            self.assertEqual(len(window.workspace_tabs), 2)
            self.assertIs(window.tabs.currentWidget(), second_tab)
            self.assertEqual(second_tab.list_widget.files, [])
            self.assertEqual(first_tab.list_widget.files, ["/tmp/a.txt"])

            second_tab.list_widget.add_file("/tmp/b.txt", enforce_filter=False)
            self.assertEqual(second_tab.list_widget.files, ["/tmp/b.txt"])
            self.assertEqual(first_tab.list_widget.files, ["/tmp/a.txt"])

            second_index = window.tabs.indexOf(second_tab)
            window.close_workspace_tab(second_index)
            self.assertEqual(len(window.workspace_tabs), 1)
            self.assertNotIn(second_tab, window.workspace_tabs)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
