import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_file_concatenator import DummyQApplication, modules

class EscapeSequenceTest(unittest.TestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules, modules)
        self.modules_patcher.start()
        from file_concatenator import concatenate_files
        self.concatenate_files = concatenate_files
        DummyQApplication._clipboard.text = ''

    def tearDown(self):
        self.modules_patcher.stop()

    def test_escape_sequences(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'a.txt')
            with open(path, 'w') as f:
                f.write('data')
            self.concatenate_files([path], prefix='start\n', suffix='end\t',
                                   show_success_message=False,
                                   interpret_escape_sequences=True)
            text = DummyQApplication._clipboard.text
            self.assertIn('start\n'.encode('utf-8').decode('unicode_escape'), text)
            self.assertIn('end\t'.encode('utf-8').decode('unicode_escape'), text)

    def test_non_ascii_prefix_preserved_with_escape_sequences(self):
        """Ensure non-ASCII chars survive when escape sequences are interpreted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'a.txt')
            with open(path, 'w') as f:
                f.write('data')
            prefix = 'äß\n'
            self.concatenate_files(
                [path],
                prefix=prefix,
                suffix='',
                show_success_message=False,
                interpret_escape_sequences=True,
            )
            text = DummyQApplication._clipboard.text
            self.assertTrue(text.startswith('äß\n'))

if __name__ == '__main__':
    unittest.main()
