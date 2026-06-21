#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты workbench.db (SQLite) — T-052."""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import workbench as wb
from test_tmp import make_temp_dir


def run():
    d = make_temp_dir("wb_test_")
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
        assert len(wb.query_documents(conn, limit=5000)) == 2, "limit cap сломал выборку"

        wb.log(conn, "Claude", "done", "T-052", "ok")
        au = wb.audit(conn, agent="Claude")
        assert len(au) == 1 and au[0]["action"] == "done", "audit_log не пишется"

        rep = {"path": "/r", "structure": ["x.py", "y.sh"],
               "risks": [{"file": "y.sh", "severity": "medium"}]}
        n = wb.ingest_repo(conn, rep, source="repo1")
        assert n == 2, "ingest_repo не занёс файлы"
        assert wb.query_documents(conn, risk="medium")[0]["path"].endswith("y.sh"), "риск из отчёта не перенёсся"

        rep_big = {"structure": ["a", "b", "c"], "risks": []}
        assert wb.ingest_repo(conn, rep_big, source="repo2", max_documents=2) == 2, "max_documents не ограничивает ingest"

        inside = wb.resolve_db_path("inside.db", base_dir=d)
        assert str(inside).startswith(d), "relative db path не резолвится внутри base_dir"
        try:
            wb.resolve_db_path(os.path.join(os.path.dirname(d), "outside.db"), base_dir=d)
            assert False, "base_dir не ограничивает путь БД"
        except wb.PathAccessError:
            pass
        try:
            wb.resolve_db_path("not-db.txt", base_dir=d)
            assert False, "suffix check не сработал"
        except ValueError:
            pass

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
