#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты RAG-поиска v1 (TF-IDF keyword-rank) над workbench.db."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import workbench as wb
import search
from test_tmp import make_temp_dir


def run():
    d = make_temp_dir("search_test_")
    db = os.path.join(d, "wb.db")
    ok = True
    try:
        conn = wb.init(db)
        wb.add_document(conn, "s", "a.py", summary="database sqlite query engine")
        wb.add_document(conn, "s", "b.py", summary="network http client requests")
        wb.add_document(conn, "s", "c.md", summary="readme documentation guide")
        conn.close()

        res = search.rank(db, "sqlite database", limit=5)
        assert res and res[0]["path"] == "a.py", res
        assert all("score" in r for r in res), "нет score"

        assert search.rank(db, "zzzznomatch") == [], "нерелевантный запрос дал результат"

        print("TESTS OK hits=%d top=%s" % (len(res), res[0]["path"]))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
