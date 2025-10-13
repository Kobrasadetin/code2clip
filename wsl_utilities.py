"""Utilities for handling WSL paths on Windows systems."""

import os
import platform
import subprocess
import sys


def get_default_wsl_distro():
    """Retrieve the default WSL2 distribution name and clean null bytes."""
    try:
        result = subprocess.check_output(["wsl", "-l", "-q"], universal_newlines=False)
        decoded_result = result.decode("utf-16-le").strip()
        distros = decoded_result.splitlines()
        if distros:
            return distros[0]
    except Exception as exc:  # pragma: no cover - network/OS specific
        print(
            "Encountered absolute Unix filepath in Windows. "
            f"Error retrieving WSL distros: {exc}",
            file=sys.stderr,
        )
        return None
    return None


def convert_wsl_path(filepath: str, network_host: str | None = None) -> str:
    """Convert a WSL2 path to a Windows-compatible path.

    When a network host is specified, the path is assumed to refer to that host
    and no conversion is performed.
    """
    if network_host:
        return filepath

    if platform.system() == "Windows" and filepath.startswith("/"):
        default_distro = get_default_wsl_distro()
        if default_distro:
            windows_path = (
                f"\\\\wsl.localhost\\{default_distro}" + filepath.replace("/", "\\")
            )
            if os.path.isfile(windows_path):
                return windows_path
    return filepath

