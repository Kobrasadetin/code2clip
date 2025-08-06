import os
import stat
from typing import Optional

from wsl_utilities import convert_wsl_path


def _sftp_stat(ssh_client, path: str):
    sftp = ssh_client.open_sftp()
    try:
        return sftp.stat(path)
    finally:
        sftp.close()


def is_file(path: str, ssh_client: Optional[object] = None) -> bool:
    if ssh_client and path.startswith('/'):
        try:
            attr = _sftp_stat(ssh_client, path)
            return stat.S_ISREG(attr.st_mode)
        except OSError:
            return False
    return os.path.isfile(path)


def is_dir(path: str, ssh_client: Optional[object] = None) -> bool:
    if ssh_client and path.startswith('/'):
        try:
            attr = _sftp_stat(ssh_client, path)
            return stat.S_ISDIR(attr.st_mode)
        except OSError:
            return False
    return os.path.isdir(path)


def convert_path(path: str, ssh_client: Optional[object] = None) -> str:
    """Resolve special paths for Windows WSL or remote hosts."""
    if ssh_client and path.startswith('/'):
        if is_file(path, ssh_client) or is_dir(path, ssh_client):
            return path
    return convert_wsl_path(path)
