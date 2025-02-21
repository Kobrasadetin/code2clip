import platform
import subprocess
import os
import sys

def get_default_wsl_distro():
    """Retrieve the default WSL2 distribution name and clean null bytes."""
    try:
        # Run 'wsl -l -q' to list distros
        result = subprocess.check_output(["wsl", "-l", "-q"], universal_newlines=False)
        # Decode as utf-16-le and strip whitespace
        decoded_result = result.decode("utf-16-le").strip()
        distros = decoded_result.splitlines()
        if distros:
            return distros[0]  # Return the first (default) distro
    except Exception as e:
        print(f"Encountered absolute Unix filepath in Windows. Error retrieving WSL distros: {e}", file=sys.stderr)
        return None
    return None

def convert_wsl_path(filepath):
    """
    Convert a WSL2 path to a Windows-compatible network path using \wsl.localhost\.
    """
    if platform.system() == "Windows" and filepath.startswith("/"):
        # Dynamically get the default WSL2 distro
        default_distro = get_default_wsl_distro()
        if default_distro:
            # Construct the network path
            windows_path = f"\\\\wsl.localhost\\{default_distro}" + filepath.replace("/", "\\")
            if os.path.isfile(windows_path):
                return windows_path
    return filepath