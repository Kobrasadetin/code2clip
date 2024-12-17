import sys
import os
import chardet
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QMenu,
)
from PyQt5.QtCore import Qt, QMimeData, QDateTime
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QClipboard

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
        self.takeItem(row)

    def check_encoding(self, item):
        filepath = item.text()
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
        filepath = item.text()
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

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Concatenator")
        self.setGeometry(100, 100, 600, 400)
        self.setAcceptDrops(True)  # Enable drag and drop on the main window

        # Set up the layout
        layout = QVBoxLayout()

        # Instruction label
        self.instruction_label = QPushButton("Drag and Drop Files Here")
        self.instruction_label.setStyleSheet("font-size: 16px;")
        self.instruction_label.setEnabled(False)  # Make it look like a label
        layout.addWidget(self.instruction_label)

        # List widget to display files
        self.list_widget = FileListWidget()
        layout.addWidget(self.list_widget)

        # Concatenate button
        self.concat_button = QPushButton("Concatenate and Copy to Clipboard")
        self.concat_button.clicked.connect(self.concatenate_files)
        layout.addWidget(self.concat_button)

        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if os.path.isfile(filepath):
                    self.add_file(filepath)
            event.acceptProposedAction()
        else:
            event.ignore()

    def add_file(self, filepath):
        # Avoid adding duplicate files
        existing_items = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        if filepath not in existing_items:
            item = QListWidgetItem(filepath)
            self.list_widget.addItem(item)

    def concatenate_files(self):
        if self.list_widget.count() == 0:
            QMessageBox.warning(self, "No Files", "Please add files to concatenate.")
            return

        concatenated_text = ""

        for index in range(self.list_widget.count()):
            filepath = self.list_widget.item(index).text()
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                # If UTF-8 fails, try detecting encoding
                try:
                    with open(filepath, 'rb') as file:
                        raw_data = file.read()
                        result = chardet.detect(raw_data)
                        encoding = result['encoding']
                        if encoding:
                            content = raw_data.decode(encoding)
                        else:
                            raise UnicodeDecodeError("Unknown encoding")
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to read {filename} with detected encoding.\n{str(e)}",
                    )
                    return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read {filename}.\n{str(e)}")
                return

            # Wrap content with XML-like tags
            concatenated_text += f'<file filename="{filename}">\n{content}\n</file>\n'

        # Copy to clipboard
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(concatenated_text)

        QMessageBox.information(self, "Success", "Concatenated text copied to clipboard.")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
