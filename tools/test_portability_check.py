#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.test_portability_check
# TYPE: test
# DOMAIN: core.portability
# DEPTH_LEVEL: 2
# SUMMARY: Проверяет helper-функции portability_check без тяжёлого git-archive acceptance-прогона.
# ==========================================
"""Тест portability_check.py — чистые хелперы (без тяжёлого git-archive прогона)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import portability_check as pc

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []

    # _errors: только ERROR/✗ строки
    errs = pc._errors("ERROR: артефакт нет\nOK=12 WARN=0\n✗ что-то\nобычная строка")
    if errs != ["ERROR: артефакт нет", "✗ что-то"]:
        fails.append("_errors неверно вычленил: %s" % errs)

    # _tail: последние n строк
    if pc._tail("a\nb\nc\nd", 2) != "c\nd":
        fails.append("_tail != последние 2")

    # HOST_RE: ловит абсолютный хост-путь, НЕ относительный
    if not pc.HOST_RE.search('path = "C:/Users/bob/repo"'):
        fails.append("HOST_RE не поймал C:/Users")
    if not pc.HOST_RE.search("p = '/home/bob/x'"):
        fails.append("HOST_RE не поймал /home")
    if pc.HOST_RE.search('p = "tools/foo.py"'):
        fails.append("HOST_RE ложно поймал относительный путь")

    # scan_hardcoded: список, себя не флагует (комментарии-примеры исключены)
    hits = pc.scan_hardcoded()
    if not isinstance(hits, list):
        fails.append("scan_hardcoded не список")
    if any("portability_check.py" in h for h in hits):
        fails.append("scan_hardcoded флагует сам себя")

    # BOOTSTRAP документирован (для отчёта свежего clone)
    if not pc.BOOTSTRAP or pc.BOOTSTRAP[0][0] != "pipeline.py":
        fails.append("BOOTSTRAP не включает pipeline.py snapshot")

    if fails:
        print("FAIL test_portability_check:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_portability_check: _errors + _tail + HOST_RE + scan_hardcoded + BOOTSTRAP")


if __name__ == "__main__":
    main()
