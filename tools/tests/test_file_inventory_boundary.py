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
from pathlib import Path
from unittest import mock

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

    def test_library_without_base_is_refused(self):
        # Корень сам себе граница не служит: без base_dir библиотека отказывает (fail-closed).
        with self.assertRaises(fi.ConfigError):
            fi.scan(self.base)
        with self.assertRaises(fi.ConfigError):
            fi.resolve_root(self.base)

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

    def _loop_then_dotdot_fixture(self):
        # L -> сам себя, S -> ../outside. На Python 3.12 L/../S читал внешний каталог: resolve()
        # после цикла схлопывает «..» по тексту, и результат называет S внутри базы.
        loop = os.path.join(self.base, "L")
        os.symlink(loop, loop)
        os.symlink(os.path.join("..", "outside"), os.path.join(self.base, "S"))

    def test_dotdot_after_loop_cannot_reach_outside(self):
        self._loop_then_dotdot_fixture()
        with self.assertRaises(fi.PathAccessError):
            fi.resolve_root("L/../S", base_dir=self.base)
        rc, out = run_cli(["L/../S", "--base", self.base, "--hash"])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn("secret.txt", out)
        self.assertNotIn(MARKER.strip(), out)

    def test_in_root_loop_is_outside_on_every_version(self):
        loop = os.path.join(self.base, "Lin")
        os.symlink(loop, loop)
        with self.assertRaises(fi.PathAccessError):
            fi.resolve_root("Lin", base_dir=self.base)

    def test_in_root_file_loop_is_not_listed(self):
        loop = os.path.join(self.base, "Lfile")
        os.symlink(loop, loop)
        report = fi.scan(self.base, base_dir=self.base)
        self.assertEqual({item["path"] for item in report["files"]}, {"inside.txt"})

    def test_error_entry_does_not_name_resolved_target(self):
        # Внутренний симлинк на отсутствующий внутренний файл: ошибка видна, имя цели — нет.
        os.symlink(os.path.join(self.base, "missing_in.txt"), os.path.join(self.base, "dangling_in.txt"))
        report = fi.scan(self.base, base_dir=self.base)
        errors = [item for item in report["files"] if "error" in item]
        self.assertEqual([item["path"] for item in errors], ["dangling_in.txt"])
        self.assertNotIn("missing_in.txt", json.dumps(report))

    def test_unreadable_file_is_not_hashed_and_does_not_stop_scan(self):
        # Каталог вместо файла: открыть его нельзя, но это не должно ни ронять обход, ни давать хеш.
        self.assertIsNone(fi._sha256_fd(Path(self.base), Path(self.base)))
        report = fi.scan(self.base, base_dir=self.base, hash_files=True)
        self.assertEqual({item["path"] for item in report["files"]}, {"inside.txt"})
        self.assertIsNotNone(report["files"][0]["sha256"])

    def test_symlink_whose_lstat_fails_is_not_reported(self):
        real_lstat = os.lstat

        def flaky_lstat(path, *args, **kwargs):
            if str(path).endswith("link.txt"):
                raise PermissionError(13, "Permission denied")
            return real_lstat(path, *args, **kwargs)

        with mock.patch.object(os, "lstat", side_effect=flaky_lstat):
            report = fi.scan(self.base, base_dir=self.base, hash_files=True)
        self.assertEqual({item["path"] for item in report["files"]}, {"inside.txt"})
        self.assertNotIn("link.txt", json.dumps(report))

    def test_library_refuses_dot_and_empty_base(self):
        for base in ("", ".", "   ", Path(""), Path(".")):
            with self.subTest(base=str(base)):
                with self.assertRaises(fi.ConfigError):
                    fi.scan(self.outside, base_dir=base)

    def test_cli_dot_base_is_the_explicit_current_directory(self):
        cwd = os.getcwd()
        os.chdir(self.base)
        try:
            rc, out = run_cli([".", "--base", "."])
        finally:
            os.chdir(cwd)
        self.assertEqual(rc, 0)
        self.assertEqual({item["path"] for item in json.loads(out)["files"]}, {"inside.txt"})

    def test_tilde_base_with_empty_home_is_refused(self):
        if os.name == "nt":
            self.skipTest("expanduser на Windows берёт USERPROFILE, а не HOME")
        with mock.patch.dict(os.environ, {"HOME": ""}):
            self.assertEqual(os.path.expanduser("~"), "/")  # ловушка: пустой HOME даёт корень
            with self.assertRaises(fi.ConfigError):
                fi.scan(self.outside, base_dir="~")
            rc, out = run_cli([self.outside, "--base", "~"])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "ConfigError")
        self.assertNotIn("secret.txt", out)

    def test_dotdot_after_in_root_loop_is_refused(self):
        loop = os.path.join(self.base, "Lin3")
        os.symlink(loop, loop)
        os.makedirs(os.path.join(self.base, "sub"))
        with self.assertRaises(fi.PathAccessError):
            fi.resolve_root("Lin3/../sub", base_dir=self.base)

    def test_hard_link_to_outside_file_is_not_listed_or_hashed(self):
        try:
            os.link(self.secret, os.path.join(self.base, "hard.txt"))
        except OSError:
            self.skipTest("жёсткие ссылки недоступны в этой ФС")
        report = fi.scan(self.base, base_dir=self.base, hash_files=True)
        self.assertEqual({item["path"] for item in report["files"]}, {"inside.txt"})
        self.assertNotIn(hashlib.sha256(MARKER.encode("utf-8")).hexdigest(), json.dumps(report))

    def test_race_swap_before_hash_is_not_hashed(self):
        if not fi._SAFE_OPEN:
            self.skipTest("нужны O_NOFOLLOW и dir_fd (нет на Windows)")
        # inside.txt прошёл проверку, а перед хешированием стал симлинком на секрет: O_NOFOLLOW даёт ELOOP.
        target = os.path.join(self.base, "inside.txt")
        real_open = os.open
        swapped = []

        def swap_then_open(name, flags, *args, **kwargs):
            if os.path.basename(str(name)) == "inside.txt" and not swapped:
                swapped.append(name)
                os.remove(target)
                os.symlink(self.secret, target)
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(fi.os, "open", side_effect=swap_then_open):
            report = fi.scan(self.base, base_dir=self.base, hash_files=True)
        self.assertEqual(swapped, ["inside.txt"])
        self.assertEqual([item["path"] for item in report["files"]], ["inside.txt"])
        item = report["files"][0]
        self.assertIsNone(item["sha256"])
        self.assertTrue(item["hash_skipped"])
        self.assertNotIn(hashlib.sha256(MARKER.encode("utf-8")).hexdigest(), json.dumps(report))
        self.assertNotIn(MARKER.strip(), json.dumps(report))

    def test_fifo_in_base_is_listed_without_hash_and_not_opened(self):
        # Тип проверяется до open(): FIFO в базе не открывается вовсе и попадает в список без хеша.
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO недоступен в этой ОС")
        os.mkfifo(os.path.join(self.base, "pipe.txt"))
        real_open = os.open
        opened = []

        def recording_open(name, flags, *args, **kwargs):
            opened.append(os.path.basename(str(name)))
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(fi.os, "open", side_effect=recording_open):
            report = fi.scan(self.base, base_dir=self.base, hash_files=True)
        self.assertNotIn("pipe.txt", opened)
        entries = {item["path"]: item for item in report["files"]}
        self.assertTrue(entries["pipe.txt"]["hash_skipped"])


if __name__ == "__main__":
    unittest.main()
