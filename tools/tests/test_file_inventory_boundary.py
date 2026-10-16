#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Граница allowed-root для drivers/file-inventory (fail-closed, тот же класс, что у drivers/files).

Без --base CLI отказывает. Симлинк, ведущий наружу (или циклический), не попадает в отчёт: ни имени,
ни размера, ни SHA-256, и не даёт признака существования цели. Путь вне базы получает один и тот же
ответ, существует он или нет. «~» под базой не раскрывается. Пустая база — ошибка, а не cwd.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir

# Грузим по пути: в tools/tests уже есть inventory из drivers/files, имена модулей совпадают.
_SPEC = importlib.util.spec_from_file_location(
    "file_inventory_under_test", os.path.join(ROOT, "drivers", "file-inventory", "inventory.py"))
fi = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fi)

MARKER = "TOPSECRET_FILE_INVENTORY_MARKER\n"
INSIDE_TEXT = "обычный текст\n"


def run_cli(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = fi.main(argv)
    return rc, out.getvalue()


class FileInventoryBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = make_temp_dir("file_inventory_boundary_")
        self.base = os.path.join(self.tmp, "allowed")
        self.outside = os.path.join(self.tmp, "outside")
        self.secret = os.path.join(self.outside, "secret.txt")
        os.makedirs(self.base)
        os.makedirs(self.outside)
        with open(os.path.join(self.base, "inside.txt"), "w", encoding="utf-8") as f:
            f.write(INSIDE_TEXT)
        with open(self.secret, "w", encoding="utf-8") as f:
            f.write(MARKER)
        try:
            # Существующая цель снаружи, отсутствующая цель снаружи и каталог-симлинк наружу.
            os.symlink(self.secret, os.path.join(self.base, "link.txt"))
            os.symlink(os.path.join(self.outside, "missing.txt"), os.path.join(self.base, "dangling.txt"))
            os.symlink(self.outside, os.path.join(self.base, "outdir"))
        except (OSError, NotImplementedError):
            shutil.rmtree(self.tmp, ignore_errors=True)
            self.skipTest("симлинки недоступны в этой ОС")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cli_without_base_refuses(self):
        rc, out = run_cli([self.outside])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["error"], "ConfigError")
        self.assertNotIn("secret.txt", out)

    def test_cli_blank_base_refuses(self):
        rc, out = run_cli([self.base, "--base", "   "])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["error"], "ConfigError")

    def test_library_blank_base_is_config_error_not_cwd(self):
        with self.assertRaises(fi.ConfigError):
            fi.scan(self.outside, base_dir="")

    def test_library_without_base_keeps_root_as_boundary(self):
        names = {item["path"] for item in fi.scan(self.base)["files"]}
        self.assertEqual(names, {"inside.txt"})

    def test_cli_with_base_lists_inside_only(self):
        rc, out = run_cli([self.base, "--base", self.base, "--hash"])
        self.assertEqual(rc, 0)
        report = json.loads(out)
        self.assertEqual({item["path"] for item in report["files"]}, {"inside.txt"})
        self.assertIsNotNone(report["files"][0]["sha256"])
        for hidden in (MARKER.strip(), "link.txt", "dangling.txt", "outdir"):
            self.assertNotIn(hidden, out)

    def test_outside_symlinks_are_invisible_including_hash(self):
        # Раньше существующая цель давала размер и SHA, отсутствующая — ошибку stat: признак существования.
        report = fi.scan(self.base, base_dir=self.base, hash_files=True)
        self.assertEqual({item["path"] for item in report["files"]}, {"inside.txt"})
        self.assertFalse(any("error" in item for item in report["files"]))
        self.assertEqual(report["summary"]["total_files"], 1)
        self.assertEqual(report["summary"]["total_size_bytes"], len(INSIDE_TEXT.encode("utf-8")))
        secret_digest = hashlib.sha256(MARKER.encode("utf-8")).hexdigest()
        self.assertNotIn(secret_digest, json.dumps(report))

    def test_dir_symlink_outside_is_not_listed_or_counted(self):
        report = fi.scan(self.base, base_dir=self.base)
        self.assertNotIn("outdir", json.dumps(report))
        self.assertEqual(report["summary"]["total_files"], 1)

    def test_outside_answer_is_the_same_for_existing_missing_and_loop(self):
        loop = os.path.join(self.outside, "loop")
        os.symlink(loop, loop)
        answers = set()
        for path in (self.secret, os.path.join(self.outside, "nope"), loop, os.path.join(self.base, "outdir")):
            with self.subTest(path=os.path.basename(path)):
                with self.assertRaises(fi.PathAccessError) as cm:
                    fi.resolve_root(path, base_dir=self.base)
                answers.add(str(cm.exception).replace(path, "<path>"))
        # Сообщение повторяет входной путь и не называет разрешённую цель симлинка.
        self.assertEqual(answers, {"path is outside allowed root: <path>"})

    def test_loop_outside_is_path_access_error_on_cli(self):
        loop = os.path.join(self.outside, "loop2")
        os.symlink(loop, loop)
        rc, out = run_cli([loop, "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")

    def test_tilde_is_not_expanded_under_base(self):
        os.makedirs(os.path.join(self.base, "~notes"))
        self.assertTrue(fi.scan("~notes", base_dir=self.base)["path"].endswith("~notes"))
        for name in ("~nosuchuser_xyz", "~root", "nosuch"):
            with self.subTest(path=name):
                with self.assertRaises(FileNotFoundError):
                    fi.resolve_root(name, base_dir=self.base)

    def test_symlink_inside_base_is_kept(self):
        os.symlink(os.path.join(self.base, "inside.txt"), os.path.join(self.base, "alias.txt"))
        names = {item["path"] for item in fi.scan(self.base, base_dir=self.base)["files"]}
        self.assertEqual(names, {"inside.txt", "alias.txt"})


if __name__ == "__main__":
    unittest.main()
