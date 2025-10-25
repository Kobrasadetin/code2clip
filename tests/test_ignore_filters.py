import unittest
from ignore_filters import (
    parse_ignore_list,
    get_ignore_set,
    GLOBAL_LEAN,
    DEFAULT_IGNORE_PRESET,
    IGNORE_PRESETS,
)

class TestParseIgnoreList(unittest.TestCase):
    def test_parse(self):
        text = 'node_modules, .git ,, target, '
        result = parse_ignore_list(text)
        self.assertEqual(result, {'node_modules', '.git', 'target'})

    def test_parse_empty(self):
        self.assertEqual(parse_ignore_list(''), set())
        self.assertEqual(parse_ignore_list(', ,'), set())

class TestGetIgnoreSet(unittest.TestCase):
    def test_get_preset(self):
        result = get_ignore_set("Global-Lean", "", IGNORE_PRESETS)
        self.assertEqual(result, GLOBAL_LEAN)
        self.assertIn(".git", result)

    def test_get_custom(self):
        result = get_ignore_set("Custom", "foo, bar", IGNORE_PRESETS)
        self.assertEqual(result, {"foo", "bar"})

    def test_get_custom_but_empty(self):
        result = get_ignore_set("Custom", "", IGNORE_PRESETS)
        self.assertEqual(result, set())

    def test_fallback_to_default(self):
        result = get_ignore_set("Invalid-Preset-Name", "", IGNORE_PRESETS)
        self.assertEqual(result, IGNORE_PRESETS[DEFAULT_IGNORE_PRESET])

if __name__ == '__main__':
    unittest.main()