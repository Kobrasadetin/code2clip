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
    :param include_path: Whether to include the relative path in $filepath (default: True).
    :param prefix: String prefix for each file's content. Use $filepath as a placeholder.
    :param suffix: String suffix for each file's content.
    """
    if not file_paths:
        QMessageBox.warning(None, "No Files", "No files to concatenate.")
        return

    concatenated_text = ""

    for filepath in file_paths:
        # Calculate relative path based on root_path
        relative_path = os.path.relpath(filepath, root_path) if root_path else ""
        filename = os.path.basename(filepath)

        # Determine the value of $filepath
        filepath_string = os.path.join(relative_path, filename) if relative_path else filename

        # Replace $filepath in the prefix
        file_prefix = prefix.replace("$filepath", filepath_string)

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
                QMessageBox.critical(None, "Error", f"Failed to read {filepath}.\n{str(e)}")
                return
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to read {filepath}.\n{str(e)}")
            return

        # Wrap content with custom prefix and suffix
        concatenated_text += f"{file_prefix}\n{content}\n{suffix}\n"

    # Copy to clipboard
    clipboard: QClipboard = QApplication.clipboard()
    clipboard.setText(concatenated_text)

    QMessageBox.information(None, "Success", "Concatenated text copied to clipboard.")

