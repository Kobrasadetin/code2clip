import os
import unittest
from types import SimpleNamespace
from unittest import mock

from PyQt5.QtWidgets import QApplication

from settings_tab import SettingsTab
from settings_store import AppSettings # We will mock this
from extension_filters import EXTENSION_GROUP_DEFAULTS # Import defaults

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

class DummySettingsStore(mock.MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_dark_mode = False
        self.show_success_message = True
        self.interpret_escape_sequences = True
        self.ssh_host = "host"
        self.ssh_username = "user"
        self.extension_allow_all = False
        self.extension_categories = ["Code Files"]
        
        # --- FIX: Populate all keys from the defaults ---
        self.extension_group_texts = {
            name: ",".join(defaults) 
            for name, defaults in EXTENSION_GROUP_DEFAULTS.items()
        }
        # --- End Fix ---

        self.ignore_preset = "Global-Lean"
        self.custom_ignore_list = ""
        self.themeChanged = mock.MagicMock()
        self.sshConfigChanged = mock.MagicMock()
        self.extensionFiltersChanged = mock.MagicMock()
        self.ignoreFiltersChanged = mock.MagicMock()

class DummySSHController(mock.MagicMock):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statusChanged = mock.MagicMock()

     def is_connected(self):
         return False

class DummyAppContext(SimpleNamespace):
    def __init__(self):
        self.settings = DummySettingsStore()
        self.ssh = DummySSHController()

class TestSettingsTabIgnoreUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.ctx = DummyAppContext()
        self.tab = SettingsTab(self.ctx)
        
        # --- FIX: Mock the method we want to check ---
        self.tab.custom_ignore_field.setVisible = mock.MagicMock()
        # --- End Fix ---

    def test_ui_state_preset(self):
        """Test that custom field is hidden when a preset is selected."""
        self.ctx.settings.ignore_preset = "Global-Lean"
        self.tab.ignore_preset_combo.setCurrentText("Global-Lean")
        
        self.tab.update_ignore_ui_state()
        
        # --- FIX: Check the *call* not the *state* ---
        self.tab.custom_ignore_field.setVisible.assert_called_with(False)
        # --- End Fix ---

    def test_ui_state_custom(self):
        """Test that custom field is visible when 'Custom' is selected."""
        self.ctx.settings.ignore_preset = "Custom"
        self.tab.ignore_preset_combo.setCurrentText("Custom")
        
        self.tab.update_ignore_ui_state()
        
        # --- FIX: Check the *call* not the *state* ---
        self.tab.custom_ignore_field.setVisible.assert_called_with(True)
        # --- End Fix ---

    def test_typing_in_custom_field_switches_preset(self):
        """Test that editing the custom field switches the preset to 'Custom'."""
        self.tab.ignore_preset_combo.setCurrentText("Global-Lean")
        
        # Simulate user typing
        self.tab.custom_ignore_field.setText("foo")
        
        # Check that the combo box was updated
        self.assertEqual(self.tab.ignore_preset_combo.currentText(), "Custom")
        # Check that the settings store was updated
        self.ctx.settings.set_ignore_preset.assert_called_with("Custom")
        self.ctx.settings.set_custom_ignore_list.assert_called_with("foo")

    def test_reset_button_resets_ignore_ui(self):
        """Test that the reset button resets the ignore filter UI."""
        self.tab.ignore_preset_combo.setCurrentText("Custom")
        self.tab.custom_ignore_field.setText("foo")
        
        # Simulate reset
        self.ctx.settings.ignore_preset = "Global-Lean"
        self.ctx.settings.custom_ignore_list = ""
        self.tab.reset_extensions() # This method now resets both
        
        self.assertEqual(self.tab.ignore_preset_combo.currentText(), "Global-Lean")
        self.assertEqual(self.tab.custom_ignore_field.text(), "")
        
        # --- FIX: Check the *call* not the *state* ---
        # The last call to setVisible (from update_ignore_ui_state)
        # should be False because the preset is now "Global-Lean".
        self.tab.custom_ignore_field.setVisible.assert_called_with(False)
        # --- End Fix ---

if __name__ == "__main__":
    unittest.main()