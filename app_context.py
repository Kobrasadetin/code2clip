# app_context.py
from __future__ import annotations
from typing import Callable, Optional
from settings_store import AppSettings
from ssh_controller import SSHConnectionManager, SSHController, PasswordProvider

class AppContext:
    def __init__(self, password_provider: Optional[PasswordProvider] = None):
        self.settings = AppSettings()
        self.ssh_manager = SSHConnectionManager(self.settings.ssh_host or None, self.settings.ssh_username or None)
        self.ssh = SSHController(self.ssh_manager, password_provider=password_provider)

        # Keep SSH manager config synced to settings
        self.settings.sshConfigChanged.connect(self._on_ssh_config_changed)

    def _on_ssh_config_changed(self, host: str, username: str):
        self.ssh.configure(host, username)
