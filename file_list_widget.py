import os
import chardet
from PyQt5.QtWidgets import (
    QListWidget,
    QMenu,
    QMessageBox
)
from PyQt5.QtCore import QDateTime, Qt

class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

    def remove_item(self, item):
        row = self.row(item)
        del self.files[row]
        self.takeItem(row)

    def check_encoding(self, item):
        filepath = self.files[self.row(item)]
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
        filepath = self.files[self.row(item)]
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

    def add_file(self, filepath):
        if filepath not in self.files:
            self.files.append(filepath)
            self.update_list_display()

    def set_root_path(self, root_path):
        self.root_path = root_path
        self.update_list_display()

    def disable_root_path(self):
        self.root_path = None
        self.update_list_display()

    def update_list_display(self):
        self.clear()
        for filepath in self.files:
            relative_path = os.path.relpath(filepath, self.root_path) if self.root_path else os.path.basename(filepath)
            self.addItem(relative_path)
