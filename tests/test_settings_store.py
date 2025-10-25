import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

from ignore_filters import DEFAULT_IGNORE_PRESET, IGNORE_PRESETS

# Mock PyQt dependencies
class MockQSettings:
    _global_store = {} # Use a static store to pre-populate

    def __init__(self, *args, **kwargs):
        # This accepts QSettings(org, app)
        # We don't use org/app, but we must accept them.
        self.store = MockQSettings._global_store

    def value(self, key, defaultValue, type):
        return self.store.get(key, defaultValue)

    def setValue(self, key, value):
        self.store[key] = value

class MockQObject:
    def __init__(self):
        pass

class MockSignal:
    def __init__(self, *args, **kwargs): # Accept arguments
        self.emit = MagicMock()

    def connect(self, slot):
        pass

# Patch before importing AppSettings
with patch.dict('sys.modules', {
    'PyQt5.QtCore': MagicMock(QObject=MockQObject, pyqtSignal=MockSignal, QSettings=MockQSettings)
}):
    from settings_store import AppSettings

class TestSettingsStore(unittest.TestCase):
    def setUp(self):
        # Reset signals for each test
        self.patcher = patch.dict('sys.modules', {
            'PyQt5.QtCore': MagicMock(QObject=MockQObject, pyqtSignal=MockSignal, QSettings=MockQSettings)
        })
        self.patcher.start()
        
        # Clear the global store before each test
        MockQSettings._global_store = {}

        # Re-import to get fresh signal mocks
        global AppSettings
        import importlib
        import settings_store
        importlib.reload(settings_store)
        AppSettings = settings_store.AppSettings

    def tearDown(self):
        self.patcher.stop()

    def test_load_defaults(self):
        """Test that default values are loaded correctly."""
        MockQSettings._global_store = {} # Ensure empty
        settings = AppSettings()
        self.assertEqual(settings.ignore_preset, DEFAULT_IGNORE_PRESET)
        self.assertEqual(settings.custom_ignore_list, "")
        self.assertEqual(settings.ignore_filters, IGNORE_PRESETS[DEFAULT_IGNORE_PRESET])

    def test_load_from_qsettings(self):
        """Test that values are loaded from the mock QSettings."""
        MockQSettings._global_store = {
            "ignore_preset": "Custom",
            "custom_ignore_list": "foo, bar"
        }
        settings = AppSettings()
        # The __init__ will now read from the pre-populated store

        self.assertEqual(settings.ignore_preset, "Custom")
        self.assertEqual(settings.custom_ignore_list, "foo, bar")
        self.assertEqual(settings.ignore_filters, {"foo", "bar"})

    def test_save_values(self):
        """Test that save writes to QSettings."""
        MockQSettings._global_store = {}
        settings = AppSettings()
        
        settings.set_ignore_preset("Pythonic")
        settings.set_custom_ignore_list("my_folder")
        
        # Check the store that _qs points to
        self.assertEqual(settings._qs.store["ignore_preset"], "Pythonic")
        self.assertEqual(settings._qs.store["custom_ignore_list"], "my_folder")
        # Also check the global store
        self.assertEqual(MockQSettings._global_store["ignore_preset"], "Pythonic")

    def test_set_ignore_preset_triggers_rebuild(self):
        settings = AppSettings()
        settings.ignore_filters = set() # Clear initial set
        
        with patch.object(settings, '_rebuild_ignore_filters', wraps=settings._rebuild_ignore_filters) as mock_rebuild:
            settings.set_ignore_preset("Pythonic")
            
            mock_rebuild.assert_called_once()
            self.assertEqual(settings.ignore_preset, "Pythonic")
            self.assertEqual(settings.ignore_filters, IGNORE_PRESETS["Pythonic"])
            settings.ignoreFiltersChanged.emit.assert_called_with(IGNORE_PRESETS["Pythonic"])

    def test_set_custom_ignore_list_no_rebuild_if_not_custom(self):
        settings = AppSettings()
        settings.set_ignore_preset("Global-Lean") # Not custom
        
        with patch.object(settings, '_rebuild_ignore_filters') as mock_rebuild:
            settings.set_custom_ignore_list("foo")
            
            mock_rebuild.assert_not_called()
            self.assertEqual(settings.custom_ignore_list, "foo")
            # Filters should NOT have changed
            self.assertEqual(settings.ignore_filters, IGNORE_PRESETS["Global-Lean"])

    def test_set_custom_ignore_list_triggers_rebuild_if_custom(self):
        settings = AppSettings()
        settings.set_ignore_preset("Custom")
        
        with patch.object(settings, '_rebuild_ignore_filters', wraps=settings._rebuild_ignore_filters) as mock_rebuild:
            settings.set_custom_ignore_list("foo, bar")
            
            mock_rebuild.assert_called_once()
            self.assertEqual(settings.custom_ignore_list, "foo, bar")
            self.assertEqual(settings.ignore_filters, {"foo", "bar"})
            settings.ignoreFiltersChanged.emit.assert_called_with({"foo", "bar"})

    def test_reset_ignore_filters(self):
        settings = AppSettings()
        settings.set_ignore_preset("Custom")
        settings.set_custom_ignore_list("foo")
        
        settings.reset_ignore_filters()
        
        self.assertEqual(settings.ignore_preset, DEFAULT_IGNORE_PRESET)
        self.assertEqual(settings.custom_ignore_list, "")
        self.assertEqual(settings.ignore_filters, IGNORE_PRESETS[DEFAULT_IGNORE_PRESET])

if __name__ == '__main__':
    unittest.main()