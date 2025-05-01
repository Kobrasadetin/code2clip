import sys, os

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