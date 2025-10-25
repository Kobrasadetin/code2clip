
import os
import tempfile
import unittest

from utils import list_files


class TestListFilesIntegration(unittest.TestCase):
    def test_list_files_honors_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = {
                os.path.join(tmp, 'a.py'): 'print("a")',
                os.path.join(tmp, 'b.md'): '# heading',
                os.path.join(tmp, 'c.jpg'): 'binary',
            }
            for path, content in files.items():
                with open(path, 'w') as handle:
                    handle.write(content)

            result = list_files(tmp, ['.py', '.md'], ignore_folders=None)
            names = {os.path.basename(p) for p in result}
            self.assertEqual(names, {'a.py', 'b.md'})


if __name__ == '__main__':
    unittest.main()
