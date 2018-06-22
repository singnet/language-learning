import unittest
import os

from common.cliutils import *


class TestCliUtils(unittest.TestCase):

    def test_strip_quotes(self):
        """ Test for quotes strip """
        self.assertEqual(strip_quotes("'text'"), "text")
        self.assertEqual(strip_quotes('"text"'), "text")

    def test_strip_brackets(self):
        """ Test for square brackets strip """
        self.assertEqual(strip_brackets('[a]'), 'a')
        self.assertEqual(strip_brackets('[human]'), 'human')
        self.assertEqual(strip_brackets('[]'), '')
        self.assertEqual(strip_brackets(None), '')

    def test_strip_trailing_slash(self):
        """ Test for trailing slash strip """
        self.assertEqual(strip_trailing_slash("/home/user/"), "/home/user")
        self.assertEqual(strip_trailing_slash("/home/user"), "/home/user")
        self.assertEqual(strip_trailing_slash("etc"), "etc")
        self.assertEqual(strip_trailing_slash(""), "")
        self.assertEqual(strip_trailing_slash("/"), "")

    def test_handle_path_string(self):
        """ Test it altogether """
        self.assertEqual(handle_path_string("/home/user/"), "/home/user")
        self.assertEqual(handle_path_string("'/home/user/'"), "/home/user")
        self.assertEqual(handle_path_string('"/home/user/"'), "/home/user")
        self.assertEqual(handle_path_string("~/data/"), os.environ["HOME"]+"/data")


if __name__ == '__main__':
    unittest.main()
