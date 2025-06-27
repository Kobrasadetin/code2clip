import os
from unittest import mock
import unittest

import wsl_utilities

class TestConvertWslPath(unittest.TestCase):
    def test_non_windows(self):
        with mock.patch('platform.system', return_value='Linux'):
            self.assertEqual(wsl_utilities.convert_wsl_path('/tmp/file'), '/tmp/file')

    def test_windows_conversion(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('wsl_utilities.get_default_wsl_distro', return_value='Ubuntu'), \
             mock.patch('os.path.isfile', return_value=True):
            result = wsl_utilities.convert_wsl_path('/home/user/file')
            expected = '\\\\wsl.localhost\\Ubuntu\\home\\user\\file'
            self.assertEqual(result, expected)

    def test_windows_no_conversion(self):
        with mock.patch('platform.system', return_value='Windows'), \
             mock.patch('wsl_utilities.get_default_wsl_distro', return_value=None):
            self.assertEqual(wsl_utilities.convert_wsl_path('/path'), '/path')

if __name__ == '__main__':
    unittest.main()
