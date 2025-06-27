import sys
import os

def resource_path(rel_path: str) -> str:
    """
    Get the absolute path to a resource, whether running normally
    or from a PyInstaller one-file bundle.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller one-file puts everything into _MEIPASS
        base = sys._MEIPASS
    else:
        # running in normal Python interpreter
        base = os.path.abspath(".")
    return os.path.join(base, rel_path)

def get_app_version():
    try:
        return open(resource_path("code2clip_version.txt")).read().strip()
    except:
        return "Loading..."


def safe_relpath(path: str, start: str | None) -> tuple[str, str | None]:
    """Return a path relative to ``start`` if possible."""
    if not start:
        return os.path.basename(path), None
    try:
        return os.path.relpath(path, start), None
    except ValueError:
        msg = (
            "Cannot calculate relative path because the file and root path are on "
            "different drives or filesystems. Displaying the absolute path instead."
        )
        return path, msg
    except Exception as e:
        msg = (
            f"Failed to calculate relative path:\n{e}\n"
            "Displaying the absolute path instead."
        )
        return path, msg

def list_files(directory: str, extensions: list[str] | None = None) -> list[str]:
    """Return a list of files under ``directory`` filtered by extensions."""
    selected: list[str] = []
    normalized = [ext.lower() for ext in extensions] if extensions else None
    for root, _, files in os.walk(directory):
        for name in files:
            if normalized:
                ext = os.path.splitext(name)[1].lower()
                if ext not in normalized:
                    continue
            selected.append(os.path.join(root, name))
    return selected

