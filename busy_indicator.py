"""Non-modal activity indicators for synchronous GUI operations."""

from contextlib import contextmanager
from typing import Iterator, Type

from PyQt5.QtCore import Qt


@contextmanager
def busy_cursor(application: Type) -> Iterator[None]:
    """Show the OS wait cursor for the duration of a blocking operation."""
    instance = getattr(application, "instance", None)
    set_cursor = getattr(application, "setOverrideCursor", None)
    restore_cursor = getattr(application, "restoreOverrideCursor", None)
    app = instance() if callable(instance) else None

    if app is None or not callable(set_cursor) or not callable(restore_cursor):
        yield
        return

    set_cursor(Qt.WaitCursor)
    try:
        yield
    finally:
        restore_cursor()
