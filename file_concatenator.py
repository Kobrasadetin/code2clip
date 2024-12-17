import os
import chardet
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication

def concatenate_files(file_paths, root_path=None, prefix='<file filename="$path/$filename">', suffix='</file>'):
    """
    Concatenates the contents of the given files, wrapping each in custom tags.
    Copies the final result to the clipboard.

    :param file_paths: List of absolute file paths.
    :param root_path: Common root path to calculate relative paths (optional).
    :param prefix: String prefix for each file's content. Use $path and $filename for placeholders.
    :param suffix: String suffix for each file's content.
    """
    if not file_paths:
        QMessageBox.warning(None, "No Files", "No files to concatenate.")
        return

    concatenated_text = ""

    for filepath in file_paths:
        # Calculate relative path based on root_path
        relative_path = os.path.relpath(filepath, root_path) if root_path else os.path.basename(filepath)
        path_only, filename = os.path.split(relative_path)

        # Replace placeholders in prefix
        file_prefix = prefix.replace("$path", path_only).replace("$filename", filename)

        try:
            # Attempt to read file as UTF-8
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Detect encoding if UTF-8 fails
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
                QMessageBox.critical(None, "Error", f"Failed to read {relative_path} with detected encoding.\n{str(e)}")
                return
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to read {relative_path}.\n{str(e)}")
            return

        # Wrap content with custom prefix and suffix
        concatenated_text += f"{file_prefix}\n{content}\n{suffix}\n"

    # Copy to clipboard
    clipboard: QClipboard = QApplication.clipboard()
    clipboard.setText(concatenated_text)

    QMessageBox.information(None, "Success", "Concatenated text copied to clipboard.")
