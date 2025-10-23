import os
import unittest
from types import SimpleNamespace
from unittest import mock

from PyQt5.QtWidgets import QApplication

from concatenator_tab import ConcatenatorTab, PRESETS

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")


class DummySettings:
    def __init__(self):
        self.last_preset = "Markdown"
        self.custom_prefix = PRESETS["Custom"]["prefix"]
        self.custom_suffix = PRESETS["Custom"]["suffix"]
        self.show_success_message = True
        self.interpret_escape_sequences = True
        self.use_dark_mode = False
        self.extension_allow_all = True
        self.extension_filters = []

    def set_last_preset(self, preset: str):
        self.last_preset = preset

    def set_custom_prefix(self, prefix: str):
        self.custom_prefix = prefix

    def set_custom_suffix(self, suffix: str):
        self.custom_suffix = suffix


class DummySSHManager:
    def __init__(self, connected: bool):
        self._connected = connected
        self.host = "remote" if connected else None

    def is_connected(self) -> bool:
        return self._connected

    def path_exists(self, _path: str) -> bool:
        return True


class DummySSHController:
    def __init__(self, connected: bool):
        self._connected = connected
        self.manager = DummySSHManager(connected)

    def is_connected(self) -> bool:
        return self._connected


def create_ctx_stub(ssh_enabled: bool):
    return SimpleNamespace(
        settings=DummySettings(),
        ssh=DummySSHController(ssh_enabled),
    )


class TestSelectRootPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @mock.patch("concatenator_tab.QInputDialog.getText", return_value=("/home/user", True))
    @mock.patch("concatenator_tab.QFileDialog.getExistingDirectory")
    def test_remote_dialog_used_when_ssh_enabled(self, mock_get_dir, mock_get_text):
        ctx = create_ctx_stub(True)
        tab = ConcatenatorTab(ctx)
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
        ctx = create_ctx_stub(False)
        tab = ConcatenatorTab(ctx)
        tab.select_root_path()
        mock_get_dir.assert_called_once()
        mock_get_text.assert_not_called()
        self.assertEqual(tab.root_path, "/local")


class TestTabHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def create_tab(self):
        return ConcatenatorTab(create_ctx_stub(False))

    def test_undo_redo_file_changes(self):
        tab = self.create_tab()
        tab.list_widget.add_file("/tmp/example.py", enforce_filter=False)
        self.assertEqual(tab.list_widget.files, ["/tmp/example.py"])
        self.assertTrue(tab.can_undo())
        self.assertFalse(tab.can_redo())
        tab.undo()
        self.assertEqual(tab.list_widget.files, [])
        self.assertFalse(tab.can_undo())
        self.assertTrue(tab.can_redo())
        tab.redo()
        self.assertEqual(tab.list_widget.files, ["/tmp/example.py"])
        self.assertTrue(tab.can_undo())
        self.assertFalse(tab.can_redo())

    def test_tabs_have_independent_prefixes(self):
        tab_one = self.create_tab()
        tab_two = self.create_tab()

        tab_one.prefix_input.setText("// header\n")

        self.assertEqual(tab_two.prefix_input.text(), PRESETS["Markdown"]["prefix"])
        self.assertNotEqual(tab_one.prefix_input.text(), tab_two.prefix_input.text())


if __name__ == "__main__":
    unittest.main()

