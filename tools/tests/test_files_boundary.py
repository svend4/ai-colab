#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Граница allowed-root для drivers/files: файл-симлинк, ведущий наружу, не отдаётся
ни списком, ни поиском, ни сводкой. Регрессия: _iter_files отдавал путь без resolve,
и search читал содержимое через симлинк за пределами разрешённой папки.
read_file такой путь уже отклонял (PathAccessError) — это проверяем тоже."""
import os
import sys
import shutil
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "drivers", "files"))
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import files_driver as fd
from test_tmp import make_temp_dir

MARKER = "TOPSECRET_BOUNDARY_MARKER"


class FilesBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = make_temp_dir("files_boundary_")
        self.base = os.path.join(self.tmp, "allowed")
        self.outside = os.path.join(self.tmp, "outside")
        os.makedirs(self.base)
        os.makedirs(self.outside)
        with open(os.path.join(self.base, "inside.txt"), "w", encoding="utf-8") as f:
            f.write("обычный текст\n")
        with open(os.path.join(self.outside, "secret.txt"), "w", encoding="utf-8") as f:
            f.write(MARKER + "\n")
        try:
            os.symlink(os.path.join(self.outside, "secret.txt"), os.path.join(self.base, "link.txt"))
        except (OSError, NotImplementedError):
            self.skipTest("симлинки недоступны в этой ОС")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_search_does_not_read_through_symlink(self):
        hits = fd.search(MARKER, self.base, base_dir=self.base)
        self.assertEqual(hits, [], "поиск прочитал файл за пределами корня: %s" % hits)

    def test_list_hides_symlink_pointing_outside(self):
        names = fd.list_files(self.base, base_dir=self.base)
        self.assertEqual(names, ["inside.txt"], names)

    def test_summarize_counts_only_inside_files(self):
        s = fd.summarize(self.base, base_dir=self.base)
        self.assertEqual(s["files"], 1, s)

    def test_read_refuses_symlink_outside(self):
        with self.assertRaises(fd.PathAccessError):
            fd.read_file("link.txt", base_dir=self.base)


if __name__ == "__main__":
    unittest.main()
