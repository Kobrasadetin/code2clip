import os
import sys
import tempfile
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

import unittest

from utils import resource_path, get_app_version, safe_relpath

class TestResourcePath(unittest.TestCase):
    def test_not_frozen(self):
        # When not frozen, resource_path should join with abspath('.')
        rel = 'some/file.txt'
        expected = os.path.join(os.path.abspath('.'), rel)
        self.assertEqual(resource_path(rel), expected)

    def test_frozen(self):
        with mock.patch.object(sys, 'frozen', True, create=True), \
             mock.patch.object(sys, '_MEIPASS', '/tmp/meipass', create=True):
            self.assertEqual(resource_path('a'), os.path.join('/tmp/meipass', 'a'))

class TestGetAppVersion(unittest.TestCase):
    def test_existing_version_file(self):
        with unittest.mock.patch('utils.resource_path', return_value='temp_version.txt'):
            with open('temp_version.txt', 'w') as f:
                f.write('1.2.3')
            try:
                self.assertEqual(get_app_version(), '1.2.3')
            finally:
                os.remove('temp_version.txt')

    def test_missing_version_file(self):
        with unittest.mock.patch('utils.resource_path', return_value='nonexistent.txt'):
            self.assertEqual(get_app_version(), 'Loading...')

class TestSafeRelpath(unittest.TestCase):
    def test_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'file.txt')
            with open(file_path, 'w'):
                pass
            rel, msg = safe_relpath(file_path, tmpdir)
            self.assertEqual(rel, 'file.txt')
            self.assertIsNone(msg)

    def test_valueerror(self):
        with mock.patch('os.path.relpath', side_effect=ValueError):
            path, msg = safe_relpath('a', 'b')
            self.assertEqual(path, 'a')
            self.assertIn('different drives', msg)

    def test_exception(self):
        with mock.patch('os.path.relpath', side_effect=RuntimeError('boom')):
            path, msg = safe_relpath('a', 'b')
            self.assertEqual(path, 'a')
            self.assertIn('boom', msg)

if __name__ == '__main__':
    unittest.main()
