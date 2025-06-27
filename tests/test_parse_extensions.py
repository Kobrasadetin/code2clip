import unittest
from extension_filters import parse_extensions

class TestParseExtensions(unittest.TestCase):
    def test_parse(self):
        text = 'txt, .md ,py'
        result = parse_extensions(text)
        self.assertEqual(result, ['.txt', '.md', '.py'])

if __name__ == '__main__':
    unittest.main()
