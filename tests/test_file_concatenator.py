import os
import sys
import unittest
import tempfile
from types import ModuleType
from unittest.mock import MagicMock, patch

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
        global concatenate_files
        from file_concatenator import concatenate_files  # noqa: E402
        self.concatenate_files = concatenate_files

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

if __name__ == '__main__':
    unittest.main()
