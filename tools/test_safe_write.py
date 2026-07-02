#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест safe_write.py — CLI-обёртка предохранителя записи (_ioutil.safe_write) + атомарность (аудит C11/C49)."""
import os
import sys
import tempfile
import shutil
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _ioutil
from _ioutil import configure_output
configure_output()
import safe_write as sw


def _no_tmp_leftovers(root):
    """В папке не должно оставаться tmp-хвостов атомарной записи (*.tmp.*)."""
    return glob.glob(os.path.join(root, "*.tmp.*")) == []


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

        # 5) атомарность (аудит C11): штатная запись не оставляет tmp-хвостов
        assert _no_tmp_leftovers(root), "после safe_write не должно оставаться *.tmp.* файлов"

        # 6) атомарность при сбое (аудит C11): падение на финальной подмене
        #    (симулируем крах между truncate и write старого пути) НЕ трогает
        #    оригинал и не оставляет tmp-файлов
        f2 = os.path.join(root, "crash.txt")
        original = "важное содержимое\nстрока 2\n"
        with open(f2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(original)

        real_replace = _ioutil.os.replace

        def broken_replace(src, dst):
            raise OSError("симуляция краха записи (диск полон / kill)")

        _ioutil.os.replace = broken_replace
        try:
            crashed = False
            try:
                _ioutil.safe_write(f2, original + "ещё строка\n")
            except OSError:
                crashed = True
            assert crashed, "симуляция сбоя должна была выбросить OSError"
        finally:
            _ioutil.os.replace = real_replace
        assert open(f2, encoding="utf-8").read() == original, \
            "при сбое записи оригинальный файл должен остаться целым (не пустым/усечённым)"
        assert _no_tmp_leftovers(root), "после сбоя tmp-хвосты должны подчищаться"

        # 7) atomic_write (аудит C49): пишет контент, подменяет существующий, без tmp-хвостов
        f3 = os.path.join(root, "atomic.txt")
        _ioutil.atomic_write(f3, "v1\n")
        assert open(f3, encoding="utf-8").read() == "v1\n", "atomic_write должен записать контент"
        _ioutil.atomic_write(f3, "v2\n")
        assert open(f3, encoding="utf-8").read() == "v2\n", "atomic_write должен подменить контент"
        assert _no_tmp_leftovers(root), "atomic_write не должен оставлять tmp-хвостов"

        print("TESTS OK safe_write: малая-правка · предохранитель-блок(файл цел) · --force-обход · нет-пути · атомарность(сбой не рушит файл, tmp подчищен) · atomic_write")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
