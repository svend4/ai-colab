#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест safe_write.py — CLI-обёртка предохранителя записи (_ioutil.safe_write)."""
import os
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
configure_output()
import safe_write as sw


def run():
    tmp_root = os.path.join(REPO_ROOT, "tmp-work")
    os.makedirs(tmp_root, exist_ok=True)
    root = tempfile.mkdtemp(prefix="safe_write_test_", dir=tmp_root)
    try:
        f = os.path.join(root, "f.txt")
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("a\nb\nc\n")

        # 1) небольшая правка проходит
        assert sw.main([f, "--content", "a\nb\nc\nd\n"]) == 0, "малая правка должна пройти"
        assert open(f, encoding="utf-8").read() == "a\nb\nc\nd\n"

        # 2) массовое урезание — предохранитель блокирует (rc=1), файл НЕ тронут
        big = "\n".join("x" for _ in range(40)) + "\n"
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(big)
        assert sw.main([f, "--content", "y"]) == 1, "урезание 40→1 строк должно блокироваться"
        assert open(f, encoding="utf-8").read() == big, "файл не должен меняться при срабатывании предохранителя"

        # 3) --force обходит предохранитель
        assert sw.main([f, "--content", "y", "--force"]) == 0, "--force должен разрешить урезание"
        assert open(f, encoding="utf-8").read() == "y"

        # 4) нет пути → rc=2
        assert sw.main(["--content", "z"]) == 2, "без пути rc=2"

        print("TESTS OK safe_write: малая-правка · предохранитель-блок(файл цел) · --force-обход · нет-пути")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
