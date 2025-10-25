
import unittest

from settings_store import AppSettings


class TestSettingsDefaults(unittest.TestCase):
    def test_defaults_are_categories_all_on(self):
        settings = AppSettings(org="TestOrg", app="TestApp-Temp")
        try:
            self.assertEqual(settings.extension_mode, "categories")
            self.assertTrue(settings.include_code)
            self.assertTrue(settings.include_text)
            self.assertTrue(settings.include_data)
            self.assertEqual(settings.included_extensions_text, "")
        finally:
            settings._qs.clear()
            settings._qs.sync()


if __name__ == "__main__":
    unittest.main()
