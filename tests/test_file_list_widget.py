import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import os

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

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
        settings = SimpleNamespace(
            extension_allow_all=allow_all,
            extension_filters=[f.lower() for f in (filters or [])],
        )
        ssh = SimpleNamespace(manager=None, is_connected=lambda: False)
        obj.ctx = SimpleNamespace(settings=settings, ssh=ssh)
        obj.files = []
        obj.root_path = None
        obj.update_list_display = lambda: None
        return obj

    def test_allow_all(self):
        widget = self.create_widget(True, [])
        self.assertTrue(widget.is_allowed('a.txt'))
        self.assertTrue(widget.is_allowed('b.py'))

    def test_extension_filters(self):
        widget = self.create_widget(False, ['.txt'])
        self.assertTrue(widget.is_allowed('a.txt'))
        self.assertFalse(widget.is_allowed('b.py'))

    def test_extension_filters_case_insensitive(self):
        widget = self.create_widget(False, ['.Txt'])
        self.assertTrue(widget.is_allowed('notes.TXT'))
        self.assertFalse(widget.is_allowed('script.py'))

    def test_no_selection_disallowed(self):
        widget = self.create_widget(False, [])
        self.assertFalse(widget.is_allowed('a.txt'))
        self.assertFalse(widget.is_allowed('b.py'))

    def test_add_file_respects_filters_by_default(self):
        widget = self.create_widget(False, ['.txt'])
        widget.add_file('/tmp/sample.py')
        self.assertEqual(widget.files, [])

    def test_add_file_can_bypass_filters(self):
        widget = self.create_widget(False, ['.txt'])
        widget.add_file('/tmp/sample.py', enforce_filter=False)
        self.assertEqual(widget.files, ['/tmp/sample.py'])

    def test_add_clipboard_files_bypass_filter(self):
        widget = self.create_widget(False, ['.txt'])

        class DummyClipboard:
            def text(self):
                return '/tmp/sample.py\n'

        dummy_app = type('DummyApp', (), {'clipboard': staticmethod(lambda: DummyClipboard())})
        self.fw_module.QApplication = dummy_app

        with patch('file_list_widget.os.path.exists', return_value=True):
            widget.add_clipboard_files()

        self.assertEqual(widget.files, ['/tmp/sample.py'])

    def test_oversized_clipboard_is_rejected_before_filesystem_access(self):
        widget = self.create_widget(True, [])

        class DummyClipboard:
            def text(self):
                return "x" * (self_limit + 1)

        self_limit = self.fw_module.MAX_CLIPBOARD_TEXT_CHARS
        dummy_app = type(
            'DummyApp',
            (),
            {'clipboard': staticmethod(lambda: DummyClipboard())},
        )
        self.fw_module.QApplication = dummy_app

        with patch('file_list_widget.os.path.exists') as mock_exists, \
                patch.object(
                    self.fw_module.QMessageBox,
                    'warning',
                    create=True,
                ) as mock_warning:
            widget.add_clipboard_files()

        mock_exists.assert_not_called()
        mock_warning.assert_called_once()
        self.assertEqual(widget.files, [])

    def test_too_many_clipboard_lines_are_rejected_before_path_conversion(self):
        widget = self.create_widget(True, [])
        line_count = self.fw_module.MAX_CLIPBOARD_PATHS + 1

        class DummyClipboard:
            def text(self):
                return "\n".join(f"file-{number}.txt" for number in range(line_count))

        dummy_app = type(
            'DummyApp',
            (),
            {'clipboard': staticmethod(lambda: DummyClipboard())},
        )
        self.fw_module.QApplication = dummy_app

        with patch('file_list_widget.convert_wsl_path') as mock_convert, \
                patch('file_list_widget.os.path.exists') as mock_exists, \
                patch.object(
                    self.fw_module.QMessageBox,
                    'warning',
                    create=True,
                ):
            widget.add_clipboard_files()

        mock_convert.assert_not_called()
        mock_exists.assert_not_called()

    def test_unsafe_device_path_is_rejected_before_filesystem_access(self):
        widget = self.create_widget(True, [])

        class DummyClipboard:
            def text(self):
                return "NUL.txt"

        dummy_app = type(
            'DummyApp',
            (),
            {'clipboard': staticmethod(lambda: DummyClipboard())},
        )
        self.fw_module.QApplication = dummy_app

        with patch('file_list_widget.os.path.exists') as mock_exists, \
                patch.object(
                    self.fw_module.QMessageBox,
                    'warning',
                    create=True,
                ):
            widget.add_clipboard_files()

        mock_exists.assert_not_called()
        self.assertEqual(widget.files, [])

    def test_clipboard_add_is_batched_into_one_redraw_and_notification(self):
        widget = self.create_widget(True, [])
        redraws = []
        notifications = []
        widget.update_list_display = lambda: redraws.append(True)
        widget._change_callback = lambda: notifications.append(True)

        class DummyClipboard:
            def text(self):
                return "/tmp/one.py\n/tmp/two.py"

        dummy_app = type(
            'DummyApp',
            (),
            {'clipboard': staticmethod(lambda: DummyClipboard())},
        )
        self.fw_module.QApplication = dummy_app

        with patch('file_list_widget.os.path.exists', return_value=True):
            widget.add_clipboard_files()

        self.assertEqual(widget.files, ['/tmp/one.py', '/tmp/two.py'])
        self.assertEqual(len(redraws), 1)
        self.assertEqual(len(notifications), 1)

    def test_clipboard_add_ignores_reentrant_invocation(self):
        widget = self.create_widget(True, [])

        class DummyClipboard:
            def text(self):
                return "/tmp/one.py"

        dummy_app = type(
            'DummyApp',
            (),
            {'clipboard': staticmethod(lambda: DummyClipboard())},
        )
        self.fw_module.QApplication = dummy_app
        exists_calls = []

        def reentrant_exists(_path):
            exists_calls.append(True)
            widget.add_clipboard_files()
            return True

        with patch('file_list_widget.os.path.exists', side_effect=reentrant_exists):
            widget.add_clipboard_files()

        self.assertEqual(len(exists_calls), 1)
        self.assertEqual(widget.files, ['/tmp/one.py'])

    def test_clipboard_filesystem_checks_stop_at_probe_budget(self):
        widget = self.create_widget(True, [])
        widget.root_path = "C:\\project"
        path_count = self.fw_module.MAX_CLIPBOARD_PATHS

        class DummyClipboard:
            def text(self):
                return "\n".join(
                    f"missing-{number}.txt" for number in range(path_count)
                )

        dummy_app = type(
            'DummyApp',
            (),
            {'clipboard': staticmethod(lambda: DummyClipboard())},
        )
        self.fw_module.QApplication = dummy_app

        with patch(
            'file_list_widget.os.path.exists',
            return_value=False,
        ) as mock_exists, patch.object(
            self.fw_module.QMessageBox,
            'warning',
            create=True,
        ) as mock_warning:
            widget.add_clipboard_files()

        self.assertEqual(
            mock_exists.call_count,
            self.fw_module.MAX_CLIPBOARD_FILESYSTEM_PROBES,
        )
        self.assertIn(
            "filesystem safety limit",
            mock_warning.call_args.args[2],
        )

    def test_add_clipboard_files_skip_duplicates_with_trailing_whitespace(self):
        widget = self.create_widget(True, [])
        widget.add_file('/tmp/sample.py', enforce_filter=False)

        class DummyClipboard:
            def text(self):
                return '"/tmp/sample.py"\r\n/tmp/another.py\r\n'

        dummy_app = type('DummyApp', (), {'clipboard': staticmethod(lambda: DummyClipboard())})
        self.fw_module.QApplication = dummy_app

        with patch('file_list_widget.os.path.exists', return_value=True):
            widget.add_clipboard_files()

        self.assertEqual(widget.files, ['/tmp/sample.py', '/tmp/another.py'])

    def test_clipboard_wsl_paths_do_not_duplicate_existing_files(self):
        widget = self.create_widget(True, [])
        widget.files = ['C:\\Users\\demo\\sample.txt']

        class DummyClipboard:
            def text(self):
                return '/mnt/c/Users/demo/sample.txt\n/mnt/c/Users/demo/other.txt\n'

        dummy_app = type('DummyApp', (), {'clipboard': staticmethod(lambda: DummyClipboard())})
        self.fw_module.QApplication = dummy_app

        conversions = {
            '/mnt/c/Users/demo/sample.txt': r'\\wsl.localhost\\Ubuntu\\mnt\\c\\Users\\demo\\sample.txt',
            '/mnt/c/Users/demo/other.txt': r'\\wsl.localhost\\Ubuntu\\mnt\\c\\Users\\demo\\other.txt',
        }

        def fake_convert(path, host):
            return conversions.get(path, path)

        with patch('file_list_widget.convert_wsl_path', side_effect=fake_convert), \
            patch('file_list_widget.os.path.exists', return_value=True):
            widget.add_clipboard_files()

        self.assertEqual(
            widget.files,
            [
                'C:\\Users\\demo\\sample.txt',
                'C:\\Users\\demo\\other.txt',
            ],
        )

    def test_root_folder_options_include_eligible_ancestors(self):
        widget = self.create_widget(True, [])
        widget.root_path = "/src"
        widget.files = [
            "/src/packages/lib/somefile.md",
            "/src/packages/lib/other.md",
            "/src/packages/readme.md",
            "/src/main.py",
            "/outside/keep.py",
        ]

        options = widget.folder_removal_options(widget.files[0])

        self.assertEqual(
            [folder for folder, _files in options],
            ["/src/packages/lib", "/src/packages", "/src"],
        )
        self.assertEqual(
            [len(files) for _folder, files in options],
            [2, 3, 4],
        )

    def test_root_folder_options_do_not_escape_configured_root(self):
        widget = self.create_widget(True, [])
        widget.root_path = "/src/packages"
        widget.files = [
            "/src/packages/lib/somefile.md",
            "/src/packages/lib/other.md",
            "/src/keep.py",
        ]

        options = widget.folder_removal_options(widget.files[0])

        self.assertEqual(
            [folder for folder, _files in options],
            ["/src/packages/lib", "/src/packages"],
        )

    def test_no_root_offers_only_current_folder_and_parent(self):
        widget = self.create_widget(True, [])
        widget.files = [
            "/src/packages/lib/somefile.md",
            "/src/packages/lib/other.md",
            "/src/packages/readme.md",
            "/src/main.py",
        ]

        options = widget.folder_removal_options(widget.files[0])

        self.assertEqual(
            [folder for folder, _files in options],
            ["/src/packages/lib", "/src/packages"],
        )

    def test_folder_option_requires_another_listed_file(self):
        widget = self.create_widget(True, [])
        widget.root_path = "/src"
        widget.files = [
            "/src/packages/lib/somefile.md",
            "/elsewhere/keep.py",
        ]

        self.assertEqual(
            widget.folder_removal_options(widget.files[0]),
            [],
        )

    def test_folder_option_is_hidden_when_it_matches_remove_all(self):
        widget = self.create_widget(True, [])
        widget.root_path = "/src"
        widget.files = [
            "/src/packages/lib/somefile.md",
            "/src/packages/lib/other.md",
            "/src/readme.md",
        ]

        options = widget.folder_removal_options(widget.files[0])

        self.assertEqual(
            [folder for folder, _files in options],
            ["/src/packages/lib", "/src/packages"],
        )

    def test_remove_files_in_folder_only_changes_listing(self):
        widget = self.create_widget(True, [])
        widget.files = [
            "/src/packages/lib/one.md",
            "/src/packages/lib/nested/two.md",
            "/src/packages/library/keep.md",
        ]
        notifications = []
        redraws = []
        widget._change_callback = lambda: notifications.append(True)
        widget.update_list_display = lambda: redraws.append(True)

        with patch("file_list_widget.os.remove") as remove:
            widget.remove_files_in_folder("/src/packages/lib")

        self.assertEqual(
            widget.files,
            ["/src/packages/library/keep.md"],
        )
        self.assertEqual(redraws, [True])
        self.assertEqual(notifications, [True])
        remove.assert_not_called()

if __name__ == '__main__':
    unittest.main()
