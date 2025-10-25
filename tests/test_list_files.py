import os
import tempfile
import unittest

from utils import list_files

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

class TestListFiles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = self.tmpdir.name

        # Create a test structure
        os.makedirs(os.path.join(self.root, 'sub'))
        os.makedirs(os.path.join(self.root, 'node_modules', 'pkg'))
        os.makedirs(os.path.join(self.root, '.git', 'objects'))
        os.makedirs(os.path.join(self.root, 'build'))

        self.files = [
            os.path.join(self.root, 'a.txt'),
            os.path.join(self.root, 'b.md'),
            os.path.join(self.root, 'c.py'),
            os.path.join(self.root, 'sub', 'e.txt'),
            os.path.join(self.root, 'node_modules', 'd.js'),
            os.path.join(self.root, '.git', 'config'),
            os.path.join(self.root, 'build', 'output.bin'),
        ]
        for f in self.files:
            with open(f, 'w') as fh:
                fh.write('test')

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_filtering(self):
        result = list_files(self.root, extensions=['.txt', '.md'])
        expected = {
            os.path.join(self.root, 'a.txt'),
            os.path.join(self.root, 'b.md'),
            os.path.join(self.root, 'sub', 'e.txt'),
        }
        # We only check files, not ignored ones, as ignore_folders=None
        self.assertEqual(set(result), expected)

    def test_no_filter(self):
        result = list_files(self.root, extensions=None)
        self.assertEqual(set(result), set(self.files))

    def test_ignore_folders_pruning(self):
        """Test that list_files does not recurse into ignored folders."""
        ignores = {'node_modules', '.git', 'build'}
        
        # Test with no extension filter
        result = list_files(self.root, extensions=None, ignore_folders=ignores)
        expected = {
            os.path.join(self.root, 'a.txt'),
            os.path.join(self.root, 'b.md'),
            os.path.join(self.root, 'c.py'),
            os.path.join(self.root, 'sub', 'e.txt'),
        }
        self.assertEqual(set(result), expected)

    def test_ignore_folders_with_extensions(self):
        """Test that both filters are applied."""
        ignores = {'node_modules', '.git', 'build'}
        extensions = ['.txt', '.py']

        result = list_files(self.root, extensions=extensions, ignore_folders=ignores)
        expected = {
            os.path.join(self.root, 'a.txt'),
            os.path.join(self.root, 'c.py'),
            os.path.join(self.root, 'sub', 'e.txt'),
        }
        self.assertEqual(set(result), expected)

if __name__ == '__main__':
    unittest.main()