import os
import ntpath
import posixpath
from functools import partial
from typing import Callable, Iterable, Optional

import chardet
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
)
from PyQt5.QtGui import QClipboard
from PyQt5.QtCore import QDateTime, Qt

from wsl_utilities import convert_wsl_path
from utils import safe_relpath, list_files

class FileListWidget(QListWidget):
    def __init__(
        self,
        ctx=None,
        parent=None,
        change_callback: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.ctx = ctx
        # Enable drag and drop reordering within the list
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(self.SingleSelection)
        self.setDragDropMode(QListWidget.InternalMove)
        self.files = []
        self.root_path = None
        self._change_callback = change_callback
        self._undo_handler: Optional[Callable[[], None]] = None
        self._redo_handler: Optional[Callable[[], None]] = None
        self._can_undo: Optional[Callable[[], bool]] = None
        self._can_redo: Optional[Callable[[], bool]] = None

    def _looks_like_windows_path(self, filepath: str) -> bool:
        if not filepath:
            return False
        if filepath.startswith(("\\\\", "//")):
            return True
        if "\\" in filepath:
            return True
        if ":" in filepath:
            return True
        return False

    def _convert_wsl_unc_to_drive(self, filepath: str) -> str:
        simplified = filepath.replace("\\\\", "\\")
        lowered = simplified.lower()
        prefix = "\\wsl.localhost\\"
        if not lowered.startswith(prefix):
            return filepath
        parts = [segment for segment in simplified.split("\\") if segment]
        if len(parts) < 4:
            return filepath
        if parts[0].lower() != "wsl.localhost":
            return filepath
        if parts[2].lower() != "mnt":
            return filepath
        drive = parts[3]
        if len(drive) != 1 or not drive.isalpha():
            return filepath
        remainder = "\\".join(parts[4:])
        if remainder:
            return f"{drive.upper()}:\\{remainder}"
        return f"{drive.upper()}:\\"

    def _normalize_incoming_path(self, filepath: str) -> str:
        if not filepath:
            return filepath
        if self._looks_like_windows_path(filepath):
            normalized = filepath.replace("/", "\\")
            normalized = self._convert_wsl_unc_to_drive(normalized)
            return ntpath.normpath(normalized)
        if "/" in filepath and "\\" not in filepath:
            # Preserve forward slashes for POSIX-like paths even when running
            # on Windows. This avoids inadvertently converting clipboard paths
            # such as "/tmp/example.py" into "\\tmp\\example.py" which breaks
            # expectations in tests and in user workflows that rely on POSIX
            # semantics. posixpath.normpath keeps separators consistent.
            return posixpath.normpath(filepath)
        return os.path.normpath(filepath)

    def _canonical_key(self, filepath: str) -> str:
        normalized = self._normalize_incoming_path(filepath)
        if self._looks_like_windows_path(normalized):
            return ntpath.normcase(normalized)
        return normalized

    def _path_exists_in_list(self, filepath: str) -> bool:
        candidate_key = self._canonical_key(filepath)
        for existing in self.files:
            if candidate_key == self._canonical_key(existing):
                return True
        return False

    def set_change_callback(self, callback: Optional[Callable[[], None]]) -> None:
        self._change_callback = callback

    def _notify_change(self) -> None:
        callback = self.__dict__.get("_change_callback")
        if callback:
            callback()

    def set_history_handlers(
        self,
        *,
        undo_handler: Optional[Callable[[], None]] = None,
        redo_handler: Optional[Callable[[], None]] = None,
        can_undo: Optional[Callable[[], bool]] = None,
        can_redo: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._undo_handler = undo_handler
        self._redo_handler = redo_handler
        self._can_undo = can_undo
        self._can_redo = can_redo

    def set_files(self, files: Iterable[str], notify: bool = True) -> None:
        unique_files: list[str] = []
        seen_keys: set[str] = set()
        for filepath in files:
            normalized = self._normalize_incoming_path(filepath)
            key = self._canonical_key(normalized)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique_files.append(normalized)
        self.files = unique_files
        self.update_list_display()
        if notify:
            self._notify_change()

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        menu = QMenu(self)

        if item:           
            remove_action = menu.addAction("Remove File")
            remove_action.triggered.connect(partial(self.remove_item, item))

            encoding_action = menu.addAction("Check Encoding")
            encoding_action.triggered.connect(partial(self.check_encoding, item))

            metadata_action = menu.addAction("View Metadata")
            metadata_action.triggered.connect(partial(self.view_metadata, item))

            menu.addSeparator()

        add_clipboard_action = menu.addAction("Add File(s) From Clipboard")
        add_clipboard_action.triggered.connect(self.add_clipboard_files)

        def add_folder_from_dialog():
            folder = QFileDialog.getExistingDirectory(
                self,
                "Select Folder",
                options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )
            if folder:
                self.add_folder(folder)

        add_folder_action = menu.addAction("Add Folder")
        add_folder_action.triggered.connect(add_folder_from_dialog)

        remove_all_action = menu.addAction("Remove All Files")
        remove_all_action.triggered.connect(self.remove_all)

        menu.addSeparator()

        undo_action = menu.addAction("Undo")
        can_undo = self._can_undo() if self._can_undo else False
        undo_action.setEnabled(can_undo)
        if can_undo and self._undo_handler:
            undo_action.triggered.connect(self._undo_handler)

        redo_action = menu.addAction("Redo")
        can_redo = self._can_redo() if self._can_redo else False
        redo_action.setEnabled(can_redo)
        if can_redo and self._redo_handler:
            redo_action.triggered.connect(self._redo_handler)

        menu.exec_(self.mapToGlobal(event.pos()))

    def add_clipboard_files(self):
        clipboard: QClipboard = QApplication.clipboard()
        text = clipboard.text()
        # split text by newline and filter out empty strings
        file_paths = list(filter(None, text.split("\n")))
        not_found_files = []
        ssh_ctrl = getattr(self.ctx, "ssh", None)
        ssh = ssh_ctrl.manager if ssh_ctrl else None
        host = ssh.host if (ssh and ssh_ctrl and ssh_ctrl.is_connected()) else None
        for file_path in file_paths:
            original = file_path
            file_path = self.strip_quotes(file_path)
            file_path = convert_wsl_path(file_path, host)
            if ssh and ssh.is_connected() and file_path.startswith("/"):
                if ssh.path_exists(file_path):
                    self.add_file(file_path, enforce_filter=False)
                else:
                    not_found_files.append(original)
            elif os.path.exists(file_path):
                self.add_file(file_path, enforce_filter=False)
            elif self.root_path:
                candidate = os.path.join(self.root_path, file_path)
                if os.path.exists(candidate):
                    self.add_file(candidate, enforce_filter=False)
                else:
                    not_found_files.append(original)
            else:
                not_found_files.append(original)
        if not_found_files:
            QMessageBox.warning(
                self,
                "Files Not Found",
                "The following files were not found:\n" + "\n".join(not_found_files),
            )

    def add_folder(self, folder_path=None):
        if folder_path:
            settings = getattr(self.ctx, "settings", None)
            filters = settings.extension_filters if settings else None
            ignores = settings.ignore_filters if settings else None
            files = list_files(
                folder_path,
                filters,
                ignores,
            )
            allowed_files = [f for f in files if self.is_allowed(f)]
            if allowed_files:
                normalized_files = [self._normalize_incoming_path(f) for f in allowed_files]
                new_files = [f for f in normalized_files if not self._path_exists_in_list(f)]
                if new_files:
                    self.files.extend(new_files)
                    self.update_list_display()
                    self._notify_change()
            else:
                all_files = list_files(folder_path, None, ignores)
                if not all_files:
                    QMessageBox.information(
                        self,
                        "No Files Added",
                        "The selected folder contains no files.",
                    )
                    return
                ext_set = {os.path.splitext(f)[1].lower() for f in all_files}
                from extension_filters import EXTENSION_GROUP_DEFAULTS

                category_counts: dict[str, int] = {}
                for ext in ext_set:
                    for cat, items in EXTENSION_GROUP_DEFAULTS.items():
                        if ext in items:
                            category_counts[cat] = category_counts.get(cat, 0) + 1

                if not category_counts:
                    suggested = "Code Files"
                elif len(category_counts) == 1:
                    suggested = next(iter(category_counts))
                else:
                    suggested = (
                        "Code Files" if "Code Files" in category_counts else max(category_counts, key=category_counts.get)
                    )

                suggested_exts = ", ".join(sorted(ext_set))
                QMessageBox.information(
                    self,
                    "No Files Added",
                    f"No approved files were found. The folder contains: {suggested_exts}.\n"
                    f"Consider enabling the '{suggested}' category.",
                )

    def strip_quotes(self, text):
        text = text.strip()
        if len(text) >= 2 and (
            (text.startswith('"') and text.endswith('"'))
            or (text.startswith("'") and text.endswith("'"))
        ):
            return text[1:-1]
        return text

    def remove_item(self, item):
        row = self.row(item)
        del self.files[row]
        self.takeItem(row)
        self._notify_change()

    def remove_all(self):
        self.files.clear()
        self.update_list_display()
        self._notify_change()

    def check_encoding(self, item):
        filepath = item.data(Qt.UserRole)
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                if encoding:
                    QMessageBox.information(
                        self,
                        "File Encoding",
                        f"Encoding: {encoding}\nConfidence: {confidence*100:.2f}%",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Encoding Detection Failed",
                        "Could not detect the encoding of the file.",
                    )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to read {os.path.basename(filepath)}.\n{str(e)}",
            )

    def view_metadata(self, item):
        filepath = item.data(Qt.UserRole)
        try:
            size = os.path.getsize(filepath)
            last_modified_timestamp = os.path.getmtime(filepath)
            last_modified = QDateTime.fromSecsSinceEpoch(int(last_modified_timestamp)).toString(
                Qt.DefaultLocaleLongDate
            )
            metadata = (
                f"Filename: {os.path.basename(filepath)}\n"
                f"Size: {size} bytes\n"
                f"Last Modified: {last_modified}"
            )
            QMessageBox.information(
                self,
                "File Metadata",
                metadata,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to retrieve metadata for {os.path.basename(filepath)}.\n{str(e)}",
            )

    def add_file(self, filepath, enforce_filter=True):
        normalized = self._normalize_incoming_path(filepath)
        if self._path_exists_in_list(normalized):
            return
        if enforce_filter and not self.is_allowed(normalized):
            return
        self.files.append(normalized)
        self.update_list_display()
        self._notify_change()

    def is_allowed(self, filepath: str) -> bool:
        settings = getattr(self.ctx, "settings", None)
        if not settings:
            return True
        if settings.extension_allow_all:
            return True
        extensions = settings.extension_filters
        if not extensions:
            return False
        return os.path.splitext(filepath)[1].lower() in extensions

    def set_root_path(self, root_path):
        self.root_path = root_path
        self.update_list_display()

    def disable_root_path(self):
        self.root_path = None
        self.update_list_display()

    def update_list_display(self):
        self.clear()
        warnings: list[str] = []
        for filepath in self.files:
            display_path, warn_msg = safe_relpath(filepath, self.root_path)
            if warn_msg:
                warnings.append(warn_msg)
                display_path = f"{display_path} [abs]"
            item = QListWidgetItem(display_path)
            item.setData(Qt.UserRole, filepath)  # Store full path
            self.addItem(item)
        if warnings:
            QMessageBox.warning(self, "Path Error", "\n".join(sorted(set(warnings))))

    def dropEvent(self, event):
        super().dropEvent(event)
        # update self.files to match the new order
        new_files = []
        for index in range(self.count()):
            item = self.item(index)
            filepath = item.data(Qt.UserRole)
            new_files.append(filepath)
        self.files = new_files  # Update the internal list
        self._notify_change()
