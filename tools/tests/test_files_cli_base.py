#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Граница allowed-root для CLI drivers/files (fail-closed, повторная проверка D-038).

Без --base команды files_driver и inventory отказывают. inventory не отдаёт симлинк,
ведущий наружу (ни имени, ни размера, ни хеша), и отвечает одинаково для существующего
и несуществующего пути снаружи, то есть не работает как оракул существования.
"""
import contextlib
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
sys.path.insert(0, os.path.join(ROOT, "drivers", "files"))
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import files_driver as fd
import inventory as inv
from test_tmp import make_temp_dir

MARKER = "TOPSECRET_CLI_BASE_MARKER"
INSIDE_TEXT = "обычный текст\n"


def run_files_cli(argv):
    out = io.StringIO()
    with mock.patch.object(sys, "argv", ["files_driver.py"] + argv), contextlib.redirect_stdout(out):
        rc = fd.main()
    return rc, out.getvalue()


def run_inventory_cli(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = inv.main(argv)
    return rc, out.getvalue()


class CliBaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = make_temp_dir("files_cli_base_")
        self.base = os.path.join(self.tmp, "allowed")
        self.outside = os.path.join(self.tmp, "outside")
        self.secret = os.path.join(self.outside, "secret.txt")
        os.makedirs(self.base)
        os.makedirs(self.outside)
        with open(os.path.join(self.base, "inside.txt"), "w", encoding="utf-8") as f:
            f.write(INSIDE_TEXT)
        with open(self.secret, "w", encoding="utf-8") as f:
            f.write(MARKER + "\n")
        try:
            os.symlink(self.secret, os.path.join(self.base, "link.txt"))
        except (OSError, NotImplementedError):
            self.skipTest("симлинки недоступны в этой ОС")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_files_cli_without_base_refuses_every_command(self):
        commands = [
            ["list", self.outside],
            ["read", self.secret],
            ["search", MARKER, self.outside],
            ["summarize", self.outside],
        ]
        for argv in commands:
            with self.subTest(command=argv[0]):
                rc, out = run_files_cli(argv)
                self.assertEqual(rc, 2)
                self.assertEqual(json.loads(out)["error"], "ConfigError")
                self.assertNotIn(MARKER, out)

    def test_files_cli_with_base_refuses_outside_read(self):
        rc, out = run_files_cli(["read", self.secret, "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn(MARKER, out)

    def test_files_cli_with_base_reads_inside(self):
        rc, out = run_files_cli(["read", "inside.txt", "--base", self.base])
        self.assertEqual(rc, 0)
        self.assertIn("обычный текст", out)

    def test_inventory_cli_without_base_refuses(self):
        rc, out = run_inventory_cli([self.outside])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["error"], "ConfigError")
        self.assertNotIn("secret.txt", out)

    def test_inventory_cli_with_base_skips_symlink_outside(self):
        rc, out = run_inventory_cli([self.base, "--base", self.base, "--hash"])
        self.assertEqual(rc, 0)
        report = json.loads(out)
        names = {item["path"] for item in report["files"]}
        self.assertEqual(names, {"inside.txt"})
        self.assertNotIn(MARKER, out)

    def test_inventory_hash_does_not_expose_outside_content(self):
        report = inv.inventory(self.base, hash_files=True, base_dir=self.base)
        self.assertNotIn("link.txt", {item["path"] for item in report["files"]})
        self.assertEqual(report["summary"]["total_size_bytes"], len(INSIDE_TEXT.encode("utf-8")))

    def test_inventory_outside_path_has_one_answer(self):
        existing = inv.inventory(self.secret, base_dir=self.base)
        missing = inv.inventory(os.path.join(self.outside, "nope"), base_dir=self.base)
        listing = inv.inventory(self.outside, base_dir=self.base)
        self.assertEqual(existing["error"], "path is outside allowed root")
        self.assertEqual(existing["error"], missing["error"])
        self.assertEqual(existing["error"], listing["error"])
        self.assertNotIn("files", existing)

    def test_inventory_keeps_symlink_inside_base(self):
        os.symlink(os.path.join(self.base, "inside.txt"), os.path.join(self.base, "alias.txt"))
        report = inv.inventory(self.base, base_dir=self.base)
        names = {item["path"] for item in report["files"]}
        self.assertIn("alias.txt", names)

    def test_read_through_symlink_outside_does_not_name_target(self):
        rc, out = run_files_cli(["read", "link.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn("secret.txt", out)
        self.assertNotIn(self.outside, out)

    def test_list_through_dir_symlink_outside_does_not_name_target(self):
        os.symlink(self.outside, os.path.join(self.base, "outdir"))
        rc, out = run_files_cli(["list", "outdir", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn("secret.txt", out)
        self.assertNotIn(self.outside, out)

    def test_inventory_dir_symlink_outside_is_not_counted(self):
        # Имя не из SKIP_DIRS: иначе каталог пропускался бы и без проверки границы.
        os.symlink(self.outside, os.path.join(self.base, "extdir"))
        report = inv.inventory(self.base, base_dir=self.base)
        self.assertEqual(report["summary"]["total_dirs"], 0)
        self.assertEqual(report["skipped_dirs"], [])
        self.assertNotIn("extdir", json.dumps(report))

    def test_inventory_loop_outside_gives_same_answer(self):
        loop = os.path.join(self.outside, "loop")
        os.symlink(loop, loop)
        loop_report = inv.inventory(loop, base_dir=self.base)
        missing_report = inv.inventory(os.path.join(self.outside, "nope"), base_dir=self.base)
        self.assertEqual(loop_report["error"], "path is outside allowed root")
        self.assertEqual(loop_report["error"], missing_report["error"])

    def test_read_loop_outside_gives_same_answer(self):
        loop = os.path.join(self.outside, "loop")
        os.symlink(loop, loop)
        rc, out = run_files_cli(["read", loop, "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        # Сообщение повторяет то, что передал вызывающий: разрешённой цели нет (цикл).
        self.assertEqual(json.loads(out)["message"], "path is outside allowed root: " + loop)

    def test_tilde_is_not_expanded_under_base(self):
        with open(os.path.join(self.base, "~note.txt"), "w", encoding="utf-8") as f:
            f.write("tilde ok\n")
        rc, out = run_files_cli(["read", "~note.txt", "--base", self.base])
        self.assertEqual(rc, 0)
        self.assertIn("tilde ok", out)
        for name in ("~nosuchuser_xyz/x", "~root/x"):
            with self.subTest(path=name):
                rc, out = run_files_cli(["read", name, "--base", self.base])
                self.assertEqual(json.loads(out)["error"], "FileNotFoundError")

    def test_missing_or_blank_base_is_refused(self):
        with self.assertRaises(fd.PathAccessError):
            fd.list_files(self.base)
        with self.assertRaises(fd.PathAccessError):
            fd.read_file("inside.txt", base_dir="   ")
        report = inv.inventory(self.base, base_dir="")
        self.assertEqual(report["error"], "ConfigError")

    def _loop_then_dotdot_fixture(self):
        # L -> сам себя, S -> ../outside. На Python 3.12 resolve() после цикла оставляет хвост с L
        # нерешённым и схлопывает «..» по тексту: L/../S/secret.txt превращался в S/secret.txt и
        # читал внешний файл через S.
        loop = os.path.join(self.base, "L")
        os.symlink(loop, loop)
        os.symlink(os.path.join("..", "outside"), os.path.join(self.base, "S"))

    def test_dotdot_after_loop_read_does_not_reach_outside(self):
        self._loop_then_dotdot_fixture()
        rc, out = run_files_cli(["read", "L/../S/secret.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn(MARKER, out)

    def test_dotdot_after_loop_inventory_does_not_list_outside(self):
        self._loop_then_dotdot_fixture()
        # inventory резолвит относительный путь от cwd, поэтому здесь путь абсолютный, через базу.
        rc, out = run_inventory_cli([os.path.join(self.base, "L", "..", "S"), "--base", self.base, "--hash"])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "path is outside allowed root")
        self.assertNotIn("secret.txt", out)
        self.assertNotIn(MARKER, out)

    def test_in_root_loop_is_outside_on_every_version(self):
        loop = os.path.join(self.base, "Lin")
        os.symlink(loop, loop)
        rc, out = run_files_cli(["read", "Lin", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")

    def test_read_outside_exists_and_missing_give_same_answer(self):
        missing = os.path.join(self.outside, "nope.txt")
        rc_e, out_e = run_files_cli(["read", self.secret, "--base", self.base])
        rc_m, out_m = run_files_cli(["read", missing, "--base", self.base])
        self.assertEqual(rc_e, rc_m)
        existing, absent = json.loads(out_e), json.loads(out_m)
        self.assertEqual(existing["error"], absent["error"])
        self.assertEqual(existing["message"].replace(self.secret, "<path>"),
                         absent["message"].replace(missing, "<path>"))

    def test_sibling_with_same_prefix_is_outside(self):
        sibling = os.path.join(self.tmp, "allowed2")
        os.makedirs(sibling)
        with open(os.path.join(sibling, "x.txt"), "w", encoding="utf-8") as f:
            f.write("SIBLING_MARKER\n")
        rc, out = run_files_cli(["read", "../allowed2/x.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn("SIBLING_MARKER", out)

    def test_relative_base_reads_inside_and_refuses_outside(self):
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            rc, out = run_files_cli(["read", "inside.txt", "--base", "allowed"])
            self.assertEqual(rc, 0)
            self.assertIn("обычный текст", out)
            rc, out = run_files_cli(["read", self.secret, "--base", "allowed"])
            self.assertEqual(json.loads(out)["error"], "PathAccessError")
            self.assertNotIn(MARKER, out)
        finally:
            os.chdir(cwd)

    def test_dot_or_empty_path_base_is_refused_by_engine(self):
        for base in (".", Path("")):
            with self.subTest(base=str(base)):
                with self.assertRaises(fd.PathAccessError):
                    fd.read_file("inside.txt", base_dir=base)
                with self.assertRaises(fd.PathAccessError):
                    fd.list_files(self.base, base_dir=base)
                self.assertEqual(inv.inventory(self.base, base_dir=base)["error"], "ConfigError")

    def test_read_error_for_in_base_symlink_names_the_given_path(self):
        os.symlink(os.path.join(self.base, "missing_in.txt"), os.path.join(self.base, "dangling_in.txt"))
        rc, out = run_files_cli(["read", "dangling_in.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "FileNotFoundError")
        self.assertEqual(json.loads(out)["message"], "dangling_in.txt")

    def test_list_error_for_in_base_symlink_names_the_given_path(self):
        os.symlink(os.path.join(self.base, "inside.txt"), os.path.join(self.base, "alias_in.txt"))
        rc, out = run_files_cli(["list", "alias_in.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "NotADirectoryError")
        self.assertEqual(json.loads(out)["message"], "alias_in.txt")

    def test_open_error_for_in_base_symlink_names_the_given_path(self):
        os.symlink(os.path.join(self.base, "inside.txt"), os.path.join(self.base, "alias_in.txt"))
        real_open = os.open

        def failing_open(name, flags, *args, **kwargs):
            if os.path.basename(str(name)) == "inside.txt":
                raise PermissionError(13, "Permission denied", str(name))
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(fd.os, "open", side_effect=failing_open):
            rc, out = run_files_cli(["read", "alias_in.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PermissionError")
        self.assertNotIn("inside.txt", out)

    def test_in_root_file_loop_is_not_listed(self):
        loop = os.path.join(self.base, "Lfile")
        os.symlink(loop, loop)
        self.assertEqual(fd.list_files(self.base, base_dir=self.base), ["inside.txt"])

    def test_cli_dot_base_is_the_explicit_current_directory(self):
        cwd = os.getcwd()
        os.chdir(self.base)
        try:
            rc, out = run_files_cli(["read", "inside.txt", "--base", "."])
            rc_inv, out_inv = run_inventory_cli([".", "--base", "."])
        finally:
            os.chdir(cwd)
        self.assertEqual(rc, 0)
        self.assertIn("обычный текст", out)
        self.assertEqual(rc_inv, 0)
        self.assertEqual({item["path"] for item in json.loads(out_inv)["files"]}, {"inside.txt"})

    def test_loop_base_is_refused_on_every_version(self):
        loop = os.path.join(self.base, "Lbase")
        os.symlink(loop, loop)
        with self.assertRaises(fd.PathAccessError):
            fd.read_file("inside.txt", base_dir=loop)

    def test_tilde_base_with_empty_home_is_refused(self):
        with mock.patch.dict(os.environ, {"HOME": ""}):
            self.assertEqual(os.path.expanduser("~"), "/")  # ловушка: пустой HOME даёт корень
            with self.assertRaises(fd.PathAccessError):
                fd.read_file(self.secret, base_dir="~")
            rc, out = run_files_cli(["read", self.secret, "--base", "~"])
            self.assertEqual(rc, 1)
            self.assertEqual(json.loads(out)["error"], "PathAccessError")
            self.assertNotIn(MARKER, out)
            rc, out = run_inventory_cli([self.outside, "--base", "~"])
            self.assertEqual(rc, 2)
            self.assertEqual(json.loads(out)["error"], "ConfigError")
            self.assertNotIn("secret.txt", out)

    def test_dotdot_after_in_base_loop_is_refused(self):
        loop = os.path.join(self.base, "Lin2")
        os.symlink(loop, loop)
        rc, out = run_files_cli(["read", "Lin2/../inside.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")

    def test_inventory_error_names_the_given_path(self):
        os.symlink(os.path.join(self.base, "missing_in.txt"), os.path.join(self.base, "dangling_in.txt"))
        os.symlink(os.path.join(self.base, "inside.txt"), os.path.join(self.base, "alias_in.txt"))
        dangling = inv.inventory(os.path.join(self.base, "dangling_in.txt"), base_dir=self.base)
        self.assertEqual(dangling["error"], "path not found")
        self.assertEqual(dangling["path"], os.path.join(self.base, "dangling_in.txt"))
        alias = inv.inventory(os.path.join(self.base, "alias_in.txt"), base_dir=self.base)
        self.assertEqual(alias["error"], "not a directory")
        self.assertEqual(alias["path"], os.path.join(self.base, "alias_in.txt"))
        self.assertNotIn("missing_in.txt", json.dumps([dangling, alias]))

    def test_dangling_in_base_symlink_is_error_entry_without_target_name(self):
        # Симлинк внутри базы на отсутствующий внутри файл: в списке ошибка, а имени цели в отчёте нет.
        os.symlink(os.path.join(self.base, "missing_in.txt"), os.path.join(self.base, "dangling_in.txt"))
        report = inv.inventory(self.base, base_dir=self.base)
        self.assertEqual([item["path"] for item in report["errors"]], ["dangling_in.txt"])
        self.assertNotIn("missing_in.txt", json.dumps(report))

    def test_inventory_library_without_base_is_refused(self):
        # Корень сам себе граница не служит: без базы библиотека отказывает (fail-closed).
        for base in (None, ""):
            with self.subTest(base=base):
                report = inv.inventory(self.base, base_dir=base)
                self.assertEqual(report["error"], "ConfigError")
                self.assertNotIn("inside.txt", json.dumps(report))
        self.assertEqual(inv.inventory(self.base)["error"], "ConfigError")

    def test_hard_link_to_outside_file_is_not_served_or_listed(self):
        hard = os.path.join(self.base, "hard.txt")
        try:
            os.link(self.secret, hard)
        except OSError:
            self.skipTest("жёсткие ссылки недоступны в этой ФС")
        rc, out = run_files_cli(["read", "hard.txt", "--base", self.base])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn(MARKER, out)
        self.assertNotIn("hard.txt", fd.list_files(self.base, base_dir=self.base))
        report = inv.inventory(self.base, base_dir=self.base, hash_files=True)
        self.assertNotIn("hard.txt", {item["path"] for item in report["files"]})
        self.assertNotIn(MARKER, json.dumps(report))

    def test_race_swap_of_file_before_open_is_refused(self):
        # Файл прошёл проверку границы, а перед открытием заменён симлинком наружу: O_NOFOLLOW даёт ELOOP.
        target = os.path.join(self.base, "inside.txt")
        real_open = os.open
        swapped = []

        def swap_then_open(name, flags, *args, **kwargs):
            if os.path.basename(str(name)) == "inside.txt" and not swapped:
                swapped.append(name)
                os.remove(target)
                os.symlink(self.secret, target)
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(fd.os, "open", side_effect=swap_then_open):
            rc, out = run_files_cli(["read", "inside.txt", "--base", self.base])
        self.assertEqual(swapped, ["inside.txt"])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn(MARKER, out)

    def test_race_swap_of_directory_before_open_is_refused(self):
        # Каталог внутри базы подменён симлинком наружу уже после проверки: цепочка dir_fd по нему не идёт.
        sub = os.path.join(self.base, "sub")
        os.makedirs(sub)
        with open(os.path.join(sub, "deep.txt"), "w", encoding="utf-8") as f:
            f.write(INSIDE_TEXT)
        with open(os.path.join(self.outside, "deep.txt"), "w", encoding="utf-8") as f:
            f.write(MARKER + "\n")
        real_open = os.open
        swapped = []

        def swap_then_open(name, flags, *args, **kwargs):
            if name == "sub" and not swapped:
                swapped.append(name)
                shutil.rmtree(sub)
                os.symlink(self.outside, sub)
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(fd.os, "open", side_effect=swap_then_open):
            rc, out = run_files_cli(["read", "sub/deep.txt", "--base", self.base])
        self.assertEqual(swapped, ["sub"])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(out)["error"], "PathAccessError")
        self.assertNotIn(MARKER, out)


if __name__ == "__main__":
    unittest.main()
