import unittest
from unittest import mock
import sys
import types
import os
os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion") 
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

try:  # pragma: no cover - used only when paramiko isn't installed
    import paramiko
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    paramiko = types.ModuleType("paramiko")

    class AuthenticationException(Exception):
        pass

    class AutoAddPolicy:  # minimal stub
        pass

    class SSHClient:
        def set_missing_host_key_policy(self, _):
            pass

        def connect(self, *_, **__):
            pass

        def open_sftp(self):
            return types.SimpleNamespace(open=lambda *a, **k: open(*a, **k))

        def close(self):
            pass

    paramiko.AuthenticationException = AuthenticationException
    paramiko.AutoAddPolicy = AutoAddPolicy
    paramiko.SSHClient = SSHClient
    sys.modules["paramiko"] = paramiko

from ssh_utilities import SSHConnectionManager


class TestSSHConnectionManager(unittest.TestCase):
    @mock.patch("paramiko.SSHClient")
    def test_connect_without_password(self, mock_client_cls):
        mock_client = mock.Mock()
        mock_client_cls.return_value = mock_client
        manager = SSHConnectionManager("host", "user")
        manager.ensure_connection()
        args, kwargs = mock_client.connect.call_args
        self.assertEqual(args[0], "host")
        self.assertEqual(kwargs["username"], "user")

    @mock.patch("ssh_utilities.QMessageBox.warning")
    @mock.patch("ssh_utilities.QInputDialog.getText", return_value=("secret", True))
    @mock.patch("paramiko.SSHClient")
    def test_connect_with_password(self, mock_client_cls, mock_get_text, _warn):
        mock_client = mock.Mock()
        mock_client.connect.side_effect = [
            paramiko.AuthenticationException(),
            None,
        ]
        mock_client_cls.return_value = mock_client
        manager = SSHConnectionManager("host", "user")
        manager.ensure_connection()
        self.assertEqual(mock_client.connect.call_count, 2)
        mock_get_text.assert_called_once()

    @mock.patch("paramiko.SSHClient")
    def test_read_bytes(self, mock_client_cls):
        mock_client = mock.Mock()
        mock_sftp = mock.MagicMock()
        mock_file = mock.MagicMock()
        mock_file.read.return_value = b"data"
        mock_sftp.open.return_value.__enter__.return_value = mock_file
        mock_client.open_sftp.return_value = mock_sftp
        mock_client_cls.return_value = mock_client

        manager = SSHConnectionManager("host", "user")
        data = manager.read_bytes("/tmp/file")
        self.assertEqual(data, b"data")
        mock_client.open_sftp.assert_called_once()


if __name__ == "__main__":
    unittest.main()

