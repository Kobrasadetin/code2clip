import os
import chardet
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QClipboard
from utils import safe_relpath


def concatenate_files(
    file_paths,
    root_path=None,
    prefix='<file filename="$filepath">',
    suffix='</file>',
    show_success_message=True,
    interpret_escape_sequences=True,
    ssh_manager=None,
):
    """
    Concatenates the contents of the given files, wrapping each in custom tags.
    Copies the final result to the clipboard.

    :param file_paths: List of absolute file paths.
    :param root_path: Optional root path to calculate relative file paths.
    :param prefix: String prefix for each file's content. Use $filepath as a placeholder.
    :param suffix: String suffix for each file's content.
    :param show_success_message: If True, show a pop-up after copying.
    :param interpret_escape_sequences: If True, convert literal escape sequences (e.g. "\n") into actual characters.
    """
    if not file_paths:
        QMessageBox.warning(None, "No Files", "No files to concatenate.")
        return

    # Process escape sequences if enabled
    if interpret_escape_sequences:
        try:
            prefix = prefix.encode('latin-1', 'backslashreplace').decode('unicode_escape')
            suffix = suffix.encode('latin-1', 'backslashreplace').decode('unicode_escape')
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to process escape sequences:\n{str(e)}")
            return

    concatenated_text = ""
    warnings: list[str] = []

    for filepath in file_paths:
        filepath_string, warn_msg = safe_relpath(filepath, root_path)
        if warn_msg:
            warnings.append(warn_msg)

        file_prefix = prefix.replace("$filepath", filepath_string)

        try:
            if ssh_manager and ssh_manager.is_connected() and filepath.startswith("/"):
                raw_data = ssh_manager.read_bytes(filepath)
            else:
                with open(filepath, "rb") as file:
                    raw_data = file.read()
            try:
                content = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                result = chardet.detect(raw_data)
                encoding = result["encoding"]
                if encoding:
                    content = raw_data.decode(encoding)
                else:
                    raise UnicodeDecodeError("Unknown encoding", b"", 0, 0, "Unknown")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to read {filepath}.\n{str(e)}")
            return

        # Wrap content with custom prefix and suffix
        concatenated_text += f"{file_prefix}\n{content}\n{suffix}\n"

    # Copy to clipboard
    clipboard: QClipboard = QApplication.clipboard()
    clipboard.setText(concatenated_text)

    if warnings:
        QMessageBox.warning(None, "Path Error", "\n".join(sorted(set(warnings))))

    if show_success_message:
        QMessageBox.information(None, "Success", "Concatenated text copied to clipboard.")
