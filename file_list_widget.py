import os
import chardet
from PyQt5.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QFileDialog,
    QApplication,
)
from PyQt5.QtGui import QClipboard
from PyQt5.QtCore import QDateTime, Qt
from wsl_utilities import convert_wsl_path
from utils import safe_relpath, list_files

class FileListWidget(QListWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        # Enable drag and drop reordering within the list
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(self.SingleSelection)
        self.setDragDropMode(QListWidget.InternalMove)
        self.files = []
        self.root_path = None

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        # handle item clicked
        if item:
            menu = QMenu(self)
            remove_action = menu.addAction("Remove File")
            encoding_action = menu.addAction("Check Encoding")
            metadata_action = menu.addAction("View Metadata")

            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == remove_action:
                self.remove_item(item)
            elif action == encoding_action:
                self.check_encoding(item)
            elif action == metadata_action:
                self.view_metadata(item)
        # handle empty space clicked
        else:
            menu = QMenu(self)
            add_action = menu.addAction("Add File(s) From Clipboard")
            add_folder_action = menu.addAction("Add Folder")
            remove_all_action = menu.addAction("Remove All Files")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == add_action:
                self.add_clipboard_files()
            elif action == add_folder_action:
                self.add_folder(folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "Select Folder",
                    options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
                ))
            elif action == remove_all_action:
                self.remove_all()

    def add_clipboard_files(self):
        clipboard: QClipboard = QApplication.clipboard()
        text = clipboard.text()
        # split text by newline and filter out empty strings
        file_paths = list(filter(None, text.split("\n")))
        not_found_files = []
        ssh = self.main_window.ssh_manager if self.main_window else None
        host = ssh.host if (ssh and ssh.is_connected()) else None
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
            files = list_files(
                folder_path,
                self.main_window.extension_filters if self.main_window else None,
            )
            allowed_files = [f for f in files if self.is_allowed(f)]
            if allowed_files:
                for file_path in files:
                    self.add_file(file_path)
            else:
                all_files = list_files(folder_path, None)
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
        if text.startswith('"') and text.endswith('"'):
            return text[1:-1]
        return text

    def remove_item(self, item):
        row = self.row(item)
        del self.files[row]
        self.takeItem(row)

    def remove_all(self):
        self.files.clear()
        self.update_list_display()

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
        if filepath in self.files:
            return
        if enforce_filter and not self.is_allowed(filepath):
            return
        self.files.append(filepath)
        self.update_list_display()

    def is_allowed(self, filepath: str) -> bool:
        if not self.main_window:
            return True
        if self.main_window.extension_allow_all:
            return True
        extensions = self.main_window.extension_filters
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
