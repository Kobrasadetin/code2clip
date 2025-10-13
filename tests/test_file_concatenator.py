import os
import sys
import unittest
import tempfile
from types import ModuleType
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

# Create dummy Qt modules so file_concatenator imports succeed without PyQt5
class DummyClipboard:
    def __init__(self):
        self.text = ""
    def setText(self, text):
        self.text = text

class DummyQApplication:
    _clipboard = DummyClipboard()
    @staticmethod
    def clipboard():
        return DummyQApplication._clipboard

# Prepare stub modules
qtwidgets = ModuleType('PyQt5.QtWidgets')
qtwidgets.QMessageBox = MagicMock()
qtwidgets.QApplication = DummyQApplication
qtgui = ModuleType('PyQt5.QtGui')
qtgui.QClipboard = DummyClipboard
dummy_chardet = ModuleType('chardet')
def _detect(data):
    return {'encoding': 'utf-8'}
dummy_chardet.detect = _detect

modules = {
    'PyQt5': ModuleType('PyQt5'),
    'PyQt5.QtWidgets': qtwidgets,
    'PyQt5.QtGui': qtgui,
    'chardet': dummy_chardet,
}

class ConcatenateFilesTest(unittest.TestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules, modules)
        self.modules_patcher.start()
 
        # Ensure a fresh import after patching sys.modules to use the mocks
        sys.modules.pop('file_concatenator', None)
        import importlib
        mod = importlib.import_module('file_concatenator')
        self.concatenate_files = mod.concatenate_files
        qtwidgets.QMessageBox.warning.reset_mock()
        DummyQApplication._clipboard.text = ""

    def tearDown(self):
        self.modules_patcher.stop()

    def test_filepath_substitution_relative(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, 'file1.txt')
            subdir = os.path.join(tmpdir, 'sub')
            os.makedirs(subdir)
            file2 = os.path.join(subdir, 'file2.txt')
            with open(file1, 'w') as f:
                f.write('one')
            with open(file2, 'w') as f:
                f.write('two')

            prefix = "<file path='$filepath'>"
            suffix = "</file>"

            self.concatenate_files([file1, file2], root_path=tmpdir,
                                   prefix=prefix, suffix=suffix,
                                   show_success_message=False)
            clip_text = DummyQApplication._clipboard.text
            self.assertIn("<file path='file1.txt'>", clip_text)
            self.assertIn(os.path.join('sub', 'file2.txt'), clip_text)
            self.assertNotIn('file1.txt/file1.txt', clip_text)
            self.assertNotIn('file2.txt/file2.txt', clip_text)


    def test_relpath_error_falls_back_to_absolute(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, 'file1.txt')
            with open(file1, 'w') as f:
                f.write('one')

            prefix = "<file path='$filepath'>"
            suffix = "</file>"

            with patch('os.path.relpath', side_effect=ValueError):
                self.concatenate_files([file1], root_path=tmpdir,
                                       prefix=prefix, suffix=suffix,
                                       show_success_message=False)

            clip_text = DummyQApplication._clipboard.text
            self.assertIn(file1, clip_text)
            qtwidgets.QMessageBox.warning.assert_called_once()

    def test_multiple_relpath_errors_warn_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, 'file1.txt')
            file2 = os.path.join(tmpdir, 'file2.txt')
            with open(file1, 'w') as f:
                f.write('one')
            with open(file2, 'w') as f:
                f.write('two')

            prefix = "<file path='$filepath'>"
            suffix = "</file>"

            qtwidgets.QMessageBox.warning.reset_mock()
            with patch('os.path.relpath', side_effect=ValueError):
                self.concatenate_files([file1, file2], root_path=tmpdir,
                                       prefix=prefix, suffix=suffix,
                                       show_success_message=False)

        self.assertEqual(qtwidgets.QMessageBox.warning.call_count, 1)
        
    def test_spaces_in_root_path(self):
        with tempfile.TemporaryDirectory(prefix="space path ") as tmpdir:
            file1 = os.path.join(tmpdir, 'file1.txt')
            subdir = os.path.join(tmpdir, 'sub dir')
            os.makedirs(subdir)
            file2 = os.path.join(subdir, 'file2.txt')
            with open(file1, 'w') as f:
                f.write('one')
            with open(file2, 'w') as f:
                f.write('two')

            prefix = "<file path='$filepath'>"
            suffix = "</file>"

            self.concatenate_files([file1, file2], root_path=tmpdir,
                                   prefix=prefix, suffix=suffix,
                                   show_success_message=False)
            clip_text = DummyQApplication._clipboard.text
            self.assertIn("<file path='file1.txt'>", clip_text)
            self.assertIn(os.path.join('sub dir', 'file2.txt'), clip_text)
            self.assertNotIn('file1.txt/file1.txt', clip_text)
            self.assertNotIn('file2.txt/file2.txt', clip_text)

    def test_safe_relpath_no_root_no_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, 'file1.txt')
            with open(file1, 'w') as f:
                f.write('one')

            prefix = "<file path='$filepath'>"
            suffix = "</file>"

            qtwidgets.QMessageBox.warning.reset_mock()
            self.concatenate_files([file1], root_path=None,
                                   prefix=prefix, suffix=suffix,
                                   show_success_message=False)

            clip_text = DummyQApplication._clipboard.text
            self.assertIn("file1.txt", clip_text)
            qtwidgets.QMessageBox.warning.assert_not_called()

if __name__ == '__main__':
    unittest.main()
