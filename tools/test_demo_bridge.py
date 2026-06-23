#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hermetic-тест для tools/demo_bridge.py (демо AI-OS моста — 6 read-only способностей).

demo_bridge.py — монолитный main(), который грузит 4 драйвера (files / repo-runner /
workbench / git-log) на ПЕРЕДАННОЙ папке-allowed-root и печатает результат. Тестируем
сквозной контракт интеграции через subprocess на детерминированной temp-папке (а не на
реальном data/fixtures), чтобы утверждать содержимое вывода:

  1. demo на temp-папке с известными файлами → exit 0; вывод отражает РЕАЛЬНЫЙ контент:
     счётчик файлов, список файлов, files.search('sample') находит наш маркер,
     workbench.memory заносит ровно N документов и query('sample') их находит.
  2. контракт несуществующей папки → exit 2 (ранний выход, драйверы не грузятся).
  3. demo НЕ загрязняет workspace: свою БД (logs/demo_bridge.db) убирает за собой.

Изоляция: target — make_temp_dir; запуск через subprocess с PYTHONUTF8=1 (demo сам
зовёт configure_output()). ASCII-имена файлов фикстуры.
"""
import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir

sys.path.insert(0, HERE)
from _ioutil import configure_output

configure_output()

DEMO = os.path.join(HERE, "demo_bridge.py")
DB = os.path.join(ROOT, "logs", "demo_bridge.db")  # demo пишет сюда и сам чистит


def _run(*args):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, DEMO, *args],
        env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL, cwd=ROOT,
    )


def make_fixture(d):
    # ASCII-имена; "sample" — это термин, который ищет demo (term = "sample").
    with open(os.path.join(d, "alpha.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# sample module alpha\nprint('hello sample')\n")
    with open(os.path.join(d, "beta.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Beta\n\nplain text without the marker word.\n")
    with open(os.path.join(d, "readme.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("another sample line lives here\n")
    return 3  # число файлов в фикстуре


def test_happy_path():
    target = make_temp_dir("demo_bridge_")
    try:
        nfiles = make_fixture(target)
        p = _run(target)
        out = p.stdout
        assert p.returncode == 0, (p.returncode, out, p.stderr)

        # allowed-root в выводе = наш target
        assert target in out, out
        # [1] files.summarize — карта папки отражает реальный счётчик
        assert ("файлов: %d" % nfiles) in out, out
        # [2] files.list — перечислил наши файлы
        assert "alpha.py" in out and "readme.txt" in out, out
        # [3] files.search('sample') — наш маркер найден (две строки с 'sample')
        assert "files.search" in out, out
        assert "sample" in out, out
        assert "(нет совпадений)" not in out, out
        # [4] repo-runner.inspect — инвентаризация отработала (read-only)
        assert "repo-runner.inspect" in out, out
        # [5] workbench.memory — занесено ровно nfiles документов и query нашёл
        assert ("занесено документов: %d" % nfiles) in out, out
        assert "query(text=" in out, out
        # хотя бы один документ-совпадение по 'sample' (alpha.py или readme.txt)
        assert ("alpha.py" in out) or ("readme.txt" in out), out
        # [6] git-log — секция присутствует (target не git → demo берёт сам репозиторий)
        assert "git-log" in out, out
        # итоговая строка демо
        assert "средний слой" in out, out
    finally:
        shutil.rmtree(target, ignore_errors=True)


def test_missing_dir_exit2():
    bogus = os.path.join(ROOT, "tmp-work", "no_such_demo_dir_zzz123")
    assert not os.path.isdir(bogus)
    p = _run(bogus)
    assert p.returncode == 2, (p.returncode, p.stdout, p.stderr)
    assert "нет папки" in p.stdout, p.stdout


def test_no_db_leak():
    # после двух запусков demo не должен оставлять свою рабочую БД в logs/
    assert not os.path.exists(DB), "demo_bridge.db должен быть убран самим демо: %s" % DB


def run():
    try:
        test_happy_path()
        test_missing_dir_exit2()
        test_no_db_leak()
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        return 1
    print("TESTS OK demo_bridge: 6 capabilities on temp allowed-root (files/search/inventory/memory/git) + missing-dir exit2 + no db leak")
    return 0


if __name__ == "__main__":
    sys.exit(run())
