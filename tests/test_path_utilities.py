import stat
import unittest
from unittest import mock

from path_utilities import is_file, is_dir, convert_path


class DummySFTP:
    def __init__(self, files):
        self.files = files

    def stat(self, path):
        if path not in self.files:
            raise OSError
        class Attr:
            pass
        attr = Attr()
        attr.st_mode = self.files[path]
        return attr

    def close(self):
        pass


class DummySSH:
    def __init__(self, files):
        self.files = files

    def open_sftp(self):
        return DummySFTP(self.files)


class PathUtilitiesTest(unittest.TestCase):
    def setUp(self):
        self.files = {"/file": stat.S_IFREG, "/dir": stat.S_IFDIR}
        self.ssh = DummySSH(self.files)

    def test_is_file_remote(self):
        self.assertTrue(is_file("/file", self.ssh))
        self.assertFalse(is_file("/missing", self.ssh))

    def test_is_dir_remote(self):
        self.assertTrue(is_dir("/dir", self.ssh))
        self.assertFalse(is_dir("/missing", self.ssh))

    def test_convert_path_prefers_ssh(self):
        self.assertEqual(convert_path("/file", self.ssh), "/file")

    def test_convert_path_no_ssh(self):
        with mock.patch("path_utilities.convert_wsl_path", return_value="wsl") as conv:
            self.assertEqual(convert_path("/p"), "wsl")
            conv.assert_called_once()


if __name__ == "__main__":
    unittest.main()
