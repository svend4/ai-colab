# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_all
# TYPE: active-script
# DOMAIN: core.testing
# DEPTH_LEVEL: 1
# SUMMARY: Полный раннер самозапускающихся тестов tools/tests/ + агрегация exit-кодов (C13-c).
# ==========================================
"""
"""test_all.py — полный прогон тестового контура tools/tests/ (C13-c, решение Q-W2-3).

Двухступенчатый канон тестов (аудит 2026-07-02, план fix-wave2):
  1) быстрый:  py -3 -m pytest tools/tests/      # pytest-collectable подмножество
  2) полный:   python tools/test_all.py          # ВСЕ самозапускающиеся __main__-скрипты
                                                 # tools/tests/test_*.py, агрегация exit-кодов

«Зелёный pytest» ≠ «весь набор прогнан» (C13: pytest собирает ~15% файлов) — полный
вердикт даёт именно этот раннер: не-ноль хотя бы одного скрипта → не-ноль итог.
Файлы без блока `if __name__ ==` (чисто pytest-овые) раннер помечает skip:
их покрывает ступень 1. Миграция скриптов на pytest — органически при касании (C13-c).

CLI:
    python tools/test_all.py                 # полный прогон self-running скриптов
    python tools/test_all.py --list          # план прогона (что run / что skip), без запуска
    python tools/test_all.py --filter SUB    # только файлы с подстрокой SUB в имени
    python tools/test_all.py --with-pytest   # ступень 1 (pytest -q) + ступень 2 одним вызовом
    python tools/test_all.py --timeout N     # секунд на один скрипт (дефолт 300)
    python tools/test_all.py --dir DIR       # нестандартный каталог тестов (смоук/фикстуры)
    python tools/test_all.py --json          # машиночитаемый отчёт (schema test_all.v1)

exit 0 — все запущенные зелёные (и pytest зелёный при --with-pytest); exit 1 — есть красные.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

from _ioutil import configure_output
from _cli import help_guard

configure_output()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_TESTS_DIR = os.path.join(HERE, "tests")
SCHEMA = "test_all.v1"
DEFAULT_TIMEOUT = 300  # сек на один скрипт; тяжёлые (fencing/race) укладываются с запасом


def discover(tests_dir, name_filter=None):
    """(runnable, skipped): test_*.py каталога, разделённые по наличию __main__-блока.

    Самозапускающийся скрипт определяем по литералу `if __name__ ==` в тексте —
    тот же дешёвый текстовый признак, что использует аудит (64 скрипта с run()).
    Файл без него под прямым запуском молча выйдет 0, не проверив ничего, —
    показывать такой «зелёным» нельзя, поэтому он уходит в skip (его гоняет pytest).
    """
    runnable, skipped = [], []
    for path in sorted(glob.glob(os.path.join(tests_dir, "test_*.py"))):
        base = os.path.basename(path)
        if name_filter and name_filter not in base:
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            text = ""
        if "if __name__ ==" in text:
            runnable.append(path)
        else:
            skipped.append(path)
    return runnable, skipped


def run_one(path, timeout):
    """Один скрипт → dict {file, rc, seconds, tail}. Паттерн запуска — как merge_gate/_run:
    sys.executable + PYTHONUTF8, capture, stdin=DEVNULL (фикс зависания на Windows)."""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    started = time.time()
    try:
        p = subprocess.run(
            [sys.executable, path], cwd=ROOT, env=env,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", stdin=subprocess.DEVNULL, timeout=timeout,
        )
        rc = p.returncode
        out = ((p.stdout or "") + (p.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        rc = 124
        out = "(timeout %ds)" % timeout
    return {
        "file": os.path.basename(path),
        "rc": rc,
        "seconds": round(time.time() - started, 1),
        "tail": "\n".join(out.splitlines()[-5:]),
    }


def run_pytest(tests_dir):
    """Ступень 1 (--with-pytest): pytest -q по каталогу; (rc, tail)."""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        [sys.executable, "-m", "pytest", tests_dir, "-q"], cwd=ROOT, env=env,
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL,
    )
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    return p.returncode, "\n".join(out.splitlines()[-5:])


def main(argv=None):
    help_guard(__doc__)
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--dir", default=DEFAULT_TESTS_DIR)
    ap.add_argument("--filter", default=None)
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--with-pytest", action="store_true", dest="with_pytest")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    tests_dir = os.path.abspath(args.dir)
    if not os.path.isdir(tests_dir):
        print("test_all: каталог тестов не найден: %s" % tests_dir)
        return 2
    runnable, skipped = discover(tests_dir, args.filter)

    if args.list:
        for p in runnable:
            print("run  %s" % os.path.basename(p))
        for p in skipped:
            print("skip %s (pytest-only: нет __main__)" % os.path.basename(p))
        print("ПЛАН test_all: run=%d skip=%d dir=%s" % (len(runnable), len(skipped), tests_dir))
        return 0

    pytest_rc = None
    pytest_tail = ""
    if args.with_pytest:
        pytest_rc, pytest_tail = run_pytest(tests_dir)
        if not args.as_json:
            print("[%s] ступень 1: pytest -q %s (rc=%d)" % (
                "OK " if pytest_rc == 0 else "RED", tests_dir, pytest_rc))
            if pytest_rc != 0:
                print(pytest_tail)

    results = []
    for path in runnable:
        res = run_one(path, args.timeout)
        results.append(res)
        if not args.as_json:
            mark = "OK " if res["rc"] == 0 else "RED"
            print("[%s] %-45s rc=%-3d %5.1fs" % (mark, res["file"], res["rc"], res["seconds"]))
            if res["rc"] != 0:
                print("      " + res["tail"].replace("\n", "\n      "))

    fails = [r for r in results if r["rc"] != 0]
    ok = len(results) - len(fails)
    red = bool(fails) or (pytest_rc not in (None, 0))
    if args.as_json:
        print(json.dumps({
            "schema": SCHEMA, "dir": tests_dir,
            "ok": ok, "fail": len(fails), "skip": len(skipped),
            "pytest_rc": pytest_rc,
            "failed_files": [r["file"] for r in fails],
            "results": results,
        }, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("ИТОГ test_all: ok=%d fail=%d skip=%d%s" % (
            ok, len(fails), len(skipped),
            "" if pytest_rc is None else " pytest_rc=%d" % pytest_rc))
        if fails:
            print("Красные: " + ", ".join(r["file"] for r in fails))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
