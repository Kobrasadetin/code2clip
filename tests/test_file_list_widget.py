import sys
import unittest
from types import ModuleType
from unittest.mock import patch
import os

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

class DummyMainWindow:
    def __init__(self, allow_all=False, filters=None):
        self.extension_allow_all = allow_all
        self.extension_filters = filters or []

class FileListWidgetTest(unittest.TestCase):
    def setUp(self):
        Dummy = type('Dummy', (), {})
        qtwidgets = ModuleType('PyQt5.QtWidgets')
        qtwidgets.QListWidget = Dummy
        qtwidgets.QListWidgetItem = Dummy
        qtwidgets.QMenu = Dummy
        qtwidgets.QMessageBox = Dummy
        qtwidgets.QFileDialog = Dummy
        qtwidgets.QApplication = Dummy
        qtgui = ModuleType('PyQt5.QtGui')
        qtgui.QClipboard = Dummy
        qtcore = ModuleType('PyQt5.QtCore')
        qtcore.QDateTime = Dummy
        qtcore.Qt = Dummy
        dummy_chardet = ModuleType('chardet')
        dummy_chardet.detect = lambda data: {'encoding': 'utf-8'}
        modules = {
            'PyQt5': ModuleType('PyQt5'),
            'PyQt5.QtWidgets': qtwidgets,
            'PyQt5.QtGui': qtgui,
            'PyQt5.QtCore': qtcore,
            'chardet': dummy_chardet,
        }
        self.patch = patch.dict(sys.modules, modules)
        self.patch.start()
        import importlib
        self.fw_module = importlib.import_module('file_list_widget')

    def tearDown(self):
        self.patch.stop()
        if 'file_list_widget' in sys.modules:
            del sys.modules['file_list_widget']

    def create_widget(self, allow_all=False, filters=None):
        obj = self.fw_module.FileListWidget.__new__(self.fw_module.FileListWidget)
        obj.main_window = DummyMainWindow(allow_all, filters)
        return obj

    def test_allow_all(self):
        widget = self.create_widget(True, [])
        self.assertTrue(False)
        self.assertTrue(widget.is_allowed('a.txt'))
        self.assertTrue(widget.is_allowed('b.py'))

    def test_extension_filters(self):
        widget = self.create_widget(False, ['.txt'])
        self.assertTrue(widget.is_allowed('a.txt'))
        self.assertFalse(widget.is_allowed('b.py'))

    def test_no_selection_disallowed(self):
        widget = self.create_widget(False, [])
        self.assertFalse(widget.is_allowed('a.txt'))
        self.assertFalse(widget.is_allowed('b.py'))

if __name__ == '__main__':
    unittest.main()
