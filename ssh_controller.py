# ssh_controller.py
from __future__ import annotations
from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
import paramiko

class SSHError(Exception):
    pass

class SSHConnectionManager:
    """No Qt widgets here. Pure SSH logic."""
    def __init__(self, host: Optional[str] = None, username: Optional[str] = None):
        self.host = host or None
        self.username = username or None
        self.client: Optional[paramiko.SSHClient] = None

    def configure(self, host: str, username: str) -> None:
        self.host = host or None
        self.username = username or None
        self.close()

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def is_configured(self) -> bool:
        return bool(self.host and self.username)

    def is_connected(self) -> bool:
        return self.client is not None

    def try_connect(self, password: Optional[str] = None) -> bool:
        if not self.is_configured():
            return False

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if password:
                client.connect(self.host, username=self.username, password=password, timeout=10, auth_timeout=10, banner_timeout=10)
            else:
                client.connect(self.host, username=self.username, timeout=10, auth_timeout=10, banner_timeout=10)
            transport = client.get_transport()
            if transport:
                transport.set_keepalive(30)
        except paramiko.AuthenticationException:
            raise
        except Exception as exc:
            raise SSHError(str(exc)) from exc

        self.client = client
        return True

# ---------- Qt-aware controller ----------
PasswordProvider = Callable[[], Optional[str]]

class SSHController(QObject):
    statusChanged = pyqtSignal(bool)   # connected?
    error = pyqtSignal(str)

    def __init__(self, manager: SSHConnectionManager, password_provider: Optional[PasswordProvider] = None):
        super().__init__()
        self.manager = manager
        self.password_provider = password_provider

    def configure(self, host: str, username: str):
        self.manager.configure(host, username)
        self.statusChanged.emit(self.manager.is_connected())

    def connect(self):
        if not self.manager.is_configured():
            self.error.emit("Please enter an SSH host and username before connecting.")
            self.statusChanged.emit(False)
            return

        try:
            ok = self.manager.try_connect(password=None)
            if ok:
                self.statusChanged.emit(True)
                return
        except paramiko.AuthenticationException:
            pass  # fall through to password prompt
        except Exception as exc:
            self.error.emit(str(exc))
            self.statusChanged.emit(False)
            return

        # Ask for password if provider is available
        if self.password_provider is None:
            self.error.emit("Authentication required but no password provider is available.")
            self.statusChanged.emit(False)
            return

        pwd = self.password_provider()
        if not pwd:
            self.error.emit("Authentication canceled.")
            self.statusChanged.emit(False)
            return

        try:
            ok = self.manager.try_connect(password=pwd)
            self.statusChanged.emit(bool(ok))
        except Exception as exc:
            self.error.emit(str(exc))
            self.statusChanged.emit(False)

    def disconnect(self):
        self.manager.close()
        self.statusChanged.emit(False)

    def is_connected(self) -> bool:
        return self.manager.is_connected()
