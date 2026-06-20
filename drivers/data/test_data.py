#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты data driver (read-only CSV/TSV)."""
import os
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data_driver as dd


def run():
    d = tempfile.mkdtemp(prefix="data_test_")
    csvp = os.path.join(d, "t.csv")
    with open(csvp, "w", encoding="utf-8", newline="") as f:
        f.write("name,age,city\nAlice,30,NY\nBob,,LA\n")
    os.makedirs(os.path.join(d, "sub"))
    with open(os.path.join(d, "sub", "u.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("a\tb\n1\t2\n")
    ok = True
    try:
        tables = dd.list_tables(d)
        assert sorted(tables) == ["sub/u.tsv", "t.csv"], tables

        assert dd.columns(csvp) == ["name", "age", "city"], "columns неверны"

        h = dd.head(csvp, n=1)
        assert len(h) == 1 and h[0]["name"] == "Alice" and h[0]["city"] == "NY", h

        s = dd.summarize(csvp)
        assert s["rows"] == 2, s
        assert s["non_empty"]["age"] == 1, "пустая ячейка age не учтена"  # Bob age пуст

        try:
            dd.columns(csvp, base_dir=os.path.join(d, "sub"))
            assert False, "base_dir не ограничивает выход за allowed-root"
        except dd.PathAccessError:
            pass

        print("TESTS OK tables=%d cols=%d rows=%d" % (len(tables), len(dd.columns(csvp)), s["rows"]))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
