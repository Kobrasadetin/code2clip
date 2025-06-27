import unittest
from extension_filters import (
    build_extension_filters,
    EXTENSION_GROUP_DEFAULTS,
)

class TestExtensionFilters(unittest.TestCase):
    def test_allow_all(self):
        result = build_extension_filters(["Text Files"], True, EXTENSION_GROUP_DEFAULTS)
        self.assertEqual(result, [])

    def test_combined_groups(self):
        result = build_extension_filters(
            ["Text Files", "Data Files"], False, EXTENSION_GROUP_DEFAULTS
        )
        expected = sorted(
            set(
                EXTENSION_GROUP_DEFAULTS["Text Files"]
                + EXTENSION_GROUP_DEFAULTS["Data Files"]
            )
        )
        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()

