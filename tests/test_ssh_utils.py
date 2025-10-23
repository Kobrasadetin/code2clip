import os
import sys
import types
import unittest
from unittest import mock

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

from ssh_controller import SSHConnectionManager, SSHController


class TestSSHConnectionManager(unittest.TestCase):
    @mock.patch("paramiko.SSHClient")
    def test_try_connect_without_password(self, mock_client_cls):
        mock_client = mock.Mock()
        mock_client_cls.return_value = mock_client
        manager = SSHConnectionManager("host", "user")
        manager.try_connect()
        args, kwargs = mock_client.connect.call_args
        self.assertEqual(args[0], "host")
        self.assertEqual(kwargs["username"], "user")

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
        manager.client = mock_client
        data = manager.read_bytes("/tmp/file")
        self.assertEqual(data, b"data")
        mock_client.open_sftp.assert_called_once()


class TestSSHController(unittest.TestCase):
    def test_connect_prompts_for_password_on_auth_failure(self):
        manager = mock.create_autospec(SSHConnectionManager, instance=True)
        manager.is_configured.return_value = True
        manager.try_connect.side_effect = [
            paramiko.AuthenticationException(),
            True,
        ]
        manager.is_connected.return_value = False

        password_provider = mock.Mock(return_value="secret")
        controller = SSHController(manager, password_provider=password_provider)

        controller.connect()

        self.assertEqual(manager.try_connect.call_count, 2)
        manager.try_connect.assert_called_with(password="secret")
        password_provider.assert_called_once()


if __name__ == "__main__":
    unittest.main()

