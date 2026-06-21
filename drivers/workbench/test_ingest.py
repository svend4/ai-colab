#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end тест сквозного потока (T-053): скан → workbench.db → поиск."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import ingest
import workbench as wb
from test_tmp import make_temp_dir


def run():
    d = make_temp_dir("ingest_test_")
    repo = os.path.join(d, "repo")
    os.makedirs(repo)
    with open(os.path.join(repo, "x.py"), "w", encoding="utf-8") as f:
        f.write("print(1)\n")
    with open(os.path.join(repo, "run.sh"), "w", encoding="utf-8") as f:
        f.write("echo hi\n")  # repo-runner помечает .sh как risk=medium
    db = os.path.join(d, "wb.db")
    ok = True
    try:
        n = ingest.ingest_repo_path(db, repo, agent="test")
        assert n >= 2, "ingest не занёс файлы: %s" % n

        docs = ingest.query(db)
        assert any(doc["path"].endswith("x.py") for doc in docs), "x.py не в базе"

        risky = ingest.query(db, risk="medium")
        assert any(doc["path"].endswith("run.sh") for doc in risky), "риск run.sh не перенёсся в память"

        conn = wb.init(db)
        au = wb.audit(conn, agent="test")
        conn.close()
        assert au and au[0]["action"] == "ingest_repo", "audit потока не записан"

        db2 = "limited.db"
        n2 = ingest.ingest_repo_path(db2, repo, agent="test", db_base=d, source_base=d, max_files=1)
        assert n2 == 1, "max_files не ограничивает ingest_repo_path"
        assert len(ingest.query(db2, db_base=d)) == 1, "query с db_base не читает ограниченную базу"

        try:
            ingest.ingest_repo_path(os.path.join(d, "outside.db"), repo, db_base=repo, source_base=d)
            assert False, "db_base не ограничивает путь БД"
        except ingest.PathAccessError:
            pass

        print("TESTS OK ingested=%d docs=%d risky=%d audit=%d" % (n, len(docs), len(risky), len(au)))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
