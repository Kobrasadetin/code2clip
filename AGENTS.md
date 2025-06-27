# Project Agents.md Guide for OpenAI Codex

This Agents.md file provides comprehensive guidance for OpenAI Codex and other AI agents working with this codebase.

## Repository layout
- `code2clip.py` – application entry point that sets up the PyQt5 application and launches `MainWindow`.
- `main_window.py` – hosts the tabbed interface and manages persistent settings with `QSettings`.
- `concatenator_tab.py` – user interface for adding files and choosing concatenation presets.
- `file_list_widget.py` – custom list widget supporting drag-and-drop sorting and context menu options.
- `file_concatenator.py` – reads files, wraps them with the selected prefix/suffix and copies text to the clipboard.
- `settings_tab.py` – UI for toggling dark mode and other options.
- `utils.py` – helper functions (resource paths, version information, safe relative path conversion).
- `wsl_utilities.py` – converts WSL paths to Windows paths when running on Windows.
- `assets/` and `gui/` – icons, images and other resources.
- `packaging/` – PyInstaller spec and macOS packaging files.
- `tests/` – unit tests using the standard `unittest` framework.

## Conventions
- Follow standard **PEP8** style for Python code.
- Keep functions and classes small and focused. New modules should be added under the project root unless they belong in an existing package.
- Ensure text files end with a newline.
- When updating or adding features, provide corresponding unit tests under the `tests/` directory.
- Run tests locally with:
  ```bash
  python -m unittest discover
  ```
  All tests should pass before committing.

