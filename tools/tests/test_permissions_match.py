#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_permissions_match
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_permissions_match.py. Описание сгенерировано автоматически.
# ==========================================
"""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import unittest

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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
