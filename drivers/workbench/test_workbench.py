#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты workbench.db (SQLite) — T-052."""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workbench as wb


def run():
    d = tempfile.mkdtemp(prefix="wb_test_")
    db = os.path.join(d, "workbench.db")
    conn = None
    ok = True
    try:
        conn = wb.init(db)

        id1 = wb.add_document(conn, "local", "a.py", type="file", lang=".py", risk="low")
        id1b = wb.add_document(conn, "local", "a.py", type="file", lang=".py", risk="high")
        assert id1 == id1b, "upsert создал дубликат вместо обновления"
        wb.add_document(conn, "local", "b.txt", type="file", lang=".txt", risk="low")

        assert len(wb.query_documents(conn)) == 2, "ожидалось 2 документа"
        assert wb.query_documents(conn, risk="high")[0]["path"] == "a.py", "upsert не обновил risk"
        assert len(wb.query_documents(conn, text="b.txt")) == 1, "поиск по тексту не работает"

        wb.log(conn, "Claude", "done", "T-052", "ok")
        au = wb.audit(conn, agent="Claude")
        assert len(au) == 1 and au[0]["action"] == "done", "audit_log не пишется"

        rep = {"path": "/r", "structure": ["x.py", "y.sh"],
               "risks": [{"file": "y.sh", "severity": "medium"}]}
        n = wb.ingest_repo(conn, rep, source="repo1")
        assert n == 2, "ingest_repo не занёс файлы"
        assert wb.query_documents(conn, risk="medium")[0]["path"].endswith("y.sh"), "риск из отчёта не перенёсся"

        print("TESTS OK docs=%d audit=%d ingested=%d" % (len(wb.query_documents(conn)), len(au), n))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        if conn:
            conn.close()
        shutil.rmtree(d, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
