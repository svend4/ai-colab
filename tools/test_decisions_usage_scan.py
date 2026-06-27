#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест decisions_usage_scan.py — счётчик использования D-XXX (read-only).

In-process, точные утверждения (mutation-sensitive); пороги понижены для компактной фикстуры.
"""
import os
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
configure_output()
import decisions_usage_scan as dus


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def run():
    tmp_root = os.path.join(REPO_ROOT, "tmp-work")
    os.makedirs(tmp_root, exist_ok=True)
    root = tempfile.mkdtemp(prefix="dus_test_", dir=tmp_root)
    saved = (dus.ROOT, dus.THR_HI, dus.THR_LO)
    try:
        dus.ROOT, dus.THR_HI, dus.THR_LO = root, 3, 2
        # три решения; каждое упоминает себя в своём файле (1 файл)
        _w(os.path.join(root, "decisions", "D-001.md"), "---\nid: D-001\n---\n# one\n")
        _w(os.path.join(root, "decisions", "D-002.md"), "---\nid: D-002\n---\n# two\n")
        _w(os.path.join(root, "decisions", "D-003.md"), "---\nid: D-003\n---\n# three\n")
        # D-001: +2 файла → 3 (active); D-002: +1 файл → 2 (moderate); D-003: только свой → 1 (dead-weight)
        _w(os.path.join(root, "a.md"), "см. D-001\n")
        _w(os.path.join(root, "b.md"), "тоже D-001\n")
        _w(os.path.join(root, "c.md"), "и D-002\n")

        rows = {r["id"]: r for r in dus.scan()}
        assert rows["D-001"]["files"] == 3 and rows["D-001"]["status"] == "active", rows["D-001"]
        assert rows["D-002"]["files"] == 2 and rows["D-002"]["status"] == "moderate", rows["D-002"]
        assert rows["D-003"]["files"] == 1 and rows["D-003"]["status"] == "dead-weight", rows["D-003"]
        # --dead фильтр
        assert dus.main(["--dead"]) == 0

        print("TESTS OK decisions_usage_scan: active(3) · moderate(2) · dead-weight(1) · --dead")
        return 0
    finally:
        dus.ROOT, dus.THR_HI, dus.THR_LO = saved
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
