import paramiko
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox


def connect_ssh(host: str, username: str, parent=None):
    """Establish an SSH connection prompting for password if needed.

    Returns a connected ``paramiko.SSHClient`` or ``None`` if connection fails
    or the user cancels the password prompt.
    """
    password, ok = QInputDialog.getText(
        parent,
        "SSH Password",
        f"Password for {username}@{host}",
        QLineEdit.Password,
    )
    if not ok:
        return None
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=username, password=password)
        return client
    except Exception as e:  # pragma: no cover - GUI error path
        QMessageBox.critical(parent, "SSH Connection Failed", str(e))
        try:
            client.close()
        except Exception:
            pass
        return None
