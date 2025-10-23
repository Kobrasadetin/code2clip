import os
import tempfile
import unittest

from utils import list_files

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion") 
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

class TestListFiles(unittest.TestCase):
    def test_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, 'sub'))
            with open(os.path.join(tmpdir, 'a.txt'), 'w'):
                pass
            with open(os.path.join(tmpdir, 'b.md'), 'w'):
                pass
            with open(os.path.join(tmpdir, 'c.py'), 'w'):
                pass
            with open(os.path.join(tmpdir, 'd.jpg'), 'w'):
                pass
            with open(os.path.join(tmpdir, 'sub', 'e.txt'), 'w'):
                pass
            result = list_files(tmpdir, ['.txt', '.md'])
            expected = {
                os.path.join(tmpdir, 'a.txt'),
                os.path.join(tmpdir, 'b.md'),
                os.path.join(tmpdir, 'sub', 'e.txt'),
            }
            self.assertEqual(set(result), expected)

    def test_no_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'a.txt')
            with open(path, 'w'):
                pass
            self.assertEqual(set(list_files(tmpdir, None)), {path})

if __name__ == '__main__':
    unittest.main()

