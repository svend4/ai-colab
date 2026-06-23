#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import permissions

class TestPermissionsMatch(unittest.TestCase):
    def test_match_all(self):
        self.assertTrue(permissions.match("any/file/path.txt", "**"))
        self.assertTrue(permissions.match("file.md", "**"))

    def test_match_directory_tree(self):
        self.assertTrue(permissions.match("dir/file.txt", "dir/**"))
        self.assertTrue(permissions.match("dir/subdir/file.py", "dir/**"))
        self.assertFalse(permissions.match("otherdir/file.txt", "dir/**"))
        self.assertFalse(permissions.match("dir_not/file.txt", "dir/**"))

    def test_match_extension(self):
        self.assertTrue(permissions.match("docs/readme.md", "*.md"))
        self.assertTrue(permissions.match("readme.md", "*.md"))
        self.assertFalse(permissions.match("docs/script.py", "*.md"))

    def test_match_exact_path(self):
        self.assertTrue(permissions.match("exact/path/file.py", "exact/path/file.py"))
        self.assertFalse(permissions.match("exact/path/file.py2", "exact/path/file.py"))
        self.assertFalse(permissions.match("other/exact/path/file.py", "exact/path/file.py"))

    def test_match_windows_paths(self):
        # test that path backslashes are handled correctly
        self.assertTrue(permissions.match("dir\\subdir\\file.txt", "dir/**"))
        self.assertTrue(permissions.match("docs\\readme.md", "*.md"))

if __name__ == "__main__":
    unittest.main()
