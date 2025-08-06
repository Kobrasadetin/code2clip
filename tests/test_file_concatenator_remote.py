import sys
import unittest
from io import BytesIO
from unittest.mock import patch

from tests.test_file_concatenator import DummyQApplication, modules


class DummySFTP:
    def __init__(self, files):
        self.files = files

    def open(self, path, mode):
        return BytesIO(self.files[path])

    def close(self):
        pass


class DummySSH:
    def __init__(self, files):
        self.files = files

    def open_sftp(self):
        return DummySFTP(self.files)


class RemoteConcatTest(unittest.TestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules, modules)
        self.modules_patcher.start()
        from file_concatenator import concatenate_files  # noqa: E402
        self.concatenate_files = concatenate_files
        DummyQApplication._clipboard.text = ""

    def tearDown(self):
        self.modules_patcher.stop()

    def test_remote_file_read(self):
        ssh = DummySSH({"/a.txt": b"data"})
        self.concatenate_files(["/a.txt"], ssh_client=ssh, show_success_message=False)
        self.assertIn("data", DummyQApplication._clipboard.text)


if __name__ == "__main__":
    unittest.main()
