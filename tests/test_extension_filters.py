import unittest
from extension_filters import build_extension_filters, EXTENSION_GROUPS

class TestExtensionFilters(unittest.TestCase):
    def test_allow_all(self):
        result = build_extension_filters(["Text Files"], True)
        self.assertEqual(result, [])

    def test_combined_groups(self):
        result = build_extension_filters(["Text Files", "Data Files"], False)
        expected = sorted(set(EXTENSION_GROUPS["Text Files"] + EXTENSION_GROUPS["Data Files"]))
        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()

