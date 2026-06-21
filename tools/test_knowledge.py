#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест L6 knowledge workflow (tools/knowledge.py): ingest → query + redaction в summary."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import knowledge as kn
from test_tmp import temp_dir  # workspace-safe temp под ROOT/tmp-work (внутри allowed-root)


def run():
    ok = True
    db = os.path.join(ROOT, "logs", "_kn_test.db")
    try:
        with temp_dir("kn_corpus_") as corpus:
            with open(os.path.join(corpus, "a.md"), "w", encoding="utf-8") as f:
                f.write("# Заголовок\nтекст\n")
            with open(os.path.join(corpus, "b.txt"), "w", encoding="utf-8") as f:
                f.write("token=SUPERSECRETXYZ\nостальное\n")  # секрет в первой строке

            n = kn.build(db, corpus)
            assert n == 2, n

            conn = kn.wb.init(db, base_dir=ROOT)
            try:
                docs = kn.wb.query_documents(conn, limit=100)
                assert len(docs) == 2, docs
                types = {d["type"] for d in docs}
                assert types == {"md", "txt"}, types
                # redaction: секрет из первой строки b.txt не должен попасть в summary
                joined = " ".join((d.get("summary") or "") for d in docs)
                assert "SUPERSECRETXYZ" not in joined, "секрет утёк в summary: %r" % joined
                # запрос по тексту
                hits = kn.wb.query_documents(conn, text="Заголовок", limit=10)
                assert any(h["type"] == "md" for h in hits), hits
            finally:
                conn.close()

            # отчёт строится без ошибок
            rep = kn.report(corpus, db=os.path.join("logs", "_kn_test2.db"), query_text="текст")
            assert "Knowledge report" in rep and "Состав по типам" in rep, rep[:200]

            print("TESTS OK knowledge: docs=%d types=%s redaction ok" % (n, sorted(types)))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        for p in (db, os.path.join(ROOT, "logs", "_kn_test2.db")):
            try:
                os.remove(p)
            except OSError:
                pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
