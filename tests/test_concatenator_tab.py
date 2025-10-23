import os
import unittest
from types import SimpleNamespace
from unittest import mock

from PyQt5.QtWidgets import QApplication

from concatenator_tab import ConcatenatorTab

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

class DummySettings(dict):
    def value(self, key, default=None):
        return self.get(key, default)

    def setValue(self, key, value):
        self[key] = value


class DummySSH:
    def __init__(self, configured: bool):
        self._configured = configured

    def is_configured(self):
        return self._configured

    def is_connected(self):
        return self._configured


def build_main_window_stub(configured: bool = False):
    return SimpleNamespace(
        settings=DummySettings(),
        use_dark_mode=False,
        ssh_manager=DummySSH(configured),
        show_success_message=True,
        interpret_escape_sequences=True,
        extension_allow_all=True,
        extension_filters=None,
    )


class TestSelectRootPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @mock.patch("concatenator_tab.QInputDialog.getText", return_value=("/home/user", True))
    @mock.patch("concatenator_tab.QFileDialog.getExistingDirectory")
    def test_remote_dialog_used_when_ssh_enabled(self, mock_get_dir, mock_get_text):
        main_window = build_main_window_stub(True)
        tab = ConcatenatorTab(main_window)
        tab.list_widget.files = ["/home/user/a", "/home/user/b"]
        tab.select_root_path()
        mock_get_text.assert_called_once_with(
            tab, "Insert Host Path", "Enter remote root path:", text="/home/user"
        )
        mock_get_dir.assert_not_called()
        self.assertEqual(tab.root_path, "/home/user")

    @mock.patch("concatenator_tab.QFileDialog.getExistingDirectory", return_value="/local")
    @mock.patch("concatenator_tab.QInputDialog.getText")
    def test_local_dialog_used_when_ssh_disabled(self, mock_get_text, mock_get_dir):
        main_window = build_main_window_stub(False)
        tab = ConcatenatorTab(main_window)
        tab.select_root_path()
        mock_get_dir.assert_called_once()
        mock_get_text.assert_not_called()
        self.assertEqual(tab.root_path, "/local")


class TestUndoHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_file_additions_are_undoable(self):
        main_window = build_main_window_stub(False)
        tab = ConcatenatorTab(main_window)
        tab.list_widget.add_file("/tmp/one.txt", enforce_filter=False)
        tab.list_widget.add_file("/tmp/two.txt", enforce_filter=False)
        self.assertEqual(tab.list_widget.files, ["/tmp/one.txt", "/tmp/two.txt"])
        tab.undo()
        self.assertEqual(tab.list_widget.files, ["/tmp/one.txt"])
        tab.redo()
        self.assertEqual(tab.list_widget.files, ["/tmp/one.txt", "/tmp/two.txt"])


if __name__ == "__main__":
    unittest.main()

