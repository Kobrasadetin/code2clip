"""Helpers for establishing SSH connections and reading remote files."""

from __future__ import annotations

import getpass
from typing import Optional

import paramiko


class SSHConnectionManager:
    """Manage a single SSH connection used throughout the application."""

    def __init__(self, host: Optional[str] = None, username: Optional[str] = None) -> None:
        self.host = host or None
        self.username = username or None
        self.client: Optional[paramiko.SSHClient] = None

    # ------------------------------------------------------------------
    def configure(self, host: str, username: str) -> None:
        """Configure connection settings and drop any existing session."""
        self.host = host or None
        self.username = username or None
        self.close()

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    # ------------------------------------------------------------------
    def is_configured(self) -> bool:
        return bool(self.host and self.username)

    # ------------------------------------------------------------------
    def ensure_connection(self) -> Optional[paramiko.SSHClient]:
        """Ensure an SSH connection is established and return the client."""
        if not self.is_configured():
            return None
        if self.client is not None:
            return self.client

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(self.host, username=self.username)
        except paramiko.AuthenticationException:
            password = getpass.getpass(
                f"Password for {self.username}@{self.host}: "
            )
            client.connect(self.host, username=self.username, password=password)
        self.client = client
        return self.client

    # ------------------------------------------------------------------
    def path_exists(self, path: str) -> bool:
        client = self.ensure_connection()
        if client is None:
            return False
        try:
            sftp = client.open_sftp()
            try:
                sftp.stat(path)
                return True
            finally:
                sftp.close()
        except Exception:
            return False

    # ------------------------------------------------------------------
    def read_bytes(self, path: str) -> bytes:
        client = self.ensure_connection()
        if client is None:
            raise FileNotFoundError(path)
        sftp = client.open_sftp()
        try:
            with sftp.open(path, "rb") as remote_file:
                return remote_file.read()
        finally:
            sftp.close()

