#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_knowledge
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_knowledge.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест L6 knowledge workflow (tools/knowledge.py): ingest → query + redaction в summary."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
from pathlib import Path

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import knowledge as kn
from test_tmp import temp_dir  # workspace-safe temp под ROOT/tmp-work (внутри allowed-root)


def run():
    ok = True
    db = os.path.join(ROOT, "logs", "_kn_test.db")
    os.makedirs(os.path.dirname(db), exist_ok=True)  # logs/ может отсутствовать в чистом checkout
    try:
        with temp_dir("kn_corpus_") as corpus:
            with open(os.path.join(corpus, "a.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("# Заголовок\nтекст\n")
            with open(os.path.join(corpus, "b.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("token=SUPERSECRETXYZ\nостальное\n")  # секрет в первой строке
            with open(os.path.join(corpus, "c.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("# First only\n\nbody has PortalNeedle for content indexing\n")

            n = kn.build(db, corpus)
            assert n == 3, n

            conn = kn.wb.init(db, base_dir=ROOT)
            try:
                docs = kn.wb.query_documents(conn, limit=100)
                assert len(docs) == 3, docs
                types = {d["type"] for d in docs}
                assert types == {"md", "txt"}, types
                # redaction: секрет из первой строки b.txt не должен попасть в summary
                joined = " ".join((d.get("summary") or "") for d in docs)
                assert "SUPERSECRETXYZ" not in joined, "секрет утёк в summary: %r" % joined
                # запрос по тексту (LIKE)
                hits = kn.wb.query_documents(conn, text="Заголовок", limit=10)
                assert any(h["type"] == "md" for h in hits), hits
                # FTS5 ранжированный поиск (build уже построил kn_fts)
                fts = kn.fts_search(conn, "Заголовок", limit=5)
                assert any(h["type"] == "md" for h in fts), "FTS5 не нашёл md: %s" % fts
                deep = kn.fts_search(conn, "PortalNeedle", limit=5)
                assert any("c.md" in h.get("path", "") for h in deep), "FTS5 не нашёл content body: %s" % deep
            finally:
                conn.close()

            # отчёт строится без ошибок
            rep = kn.report(corpus, db=os.path.join(ROOT, "logs", "_kn_test2.db"), query_text="текст")
            assert "Knowledge report" in rep and "Состав по типам" in rep, rep[:200]
            assert isinstance(rep, str) and rep.startswith("# Knowledge report"), rep[:80]

            # report --out: запись в repo-local Markdown не меняет строковый report/stdout-контракт
            out_path = os.path.join(corpus, "knowledge-report-test.md")
            written = kn.write_report(rep, out_path)
            assert written == Path(out_path).resolve(), written
            saved = Path(out_path).read_text(encoding="utf-8")
            assert saved == rep + "\n", saved[:120]

            # write-path safety: нельзя писать вне repo root и нельзя писать не-Markdown artifact
            outside = Path(ROOT).resolve().parent / "knowledge-report-outside.md"
            try:
                kn.write_report(rep, outside)
                assert False, "write_report разрешил путь вне repo root"
            except ValueError as exc:
                assert "outside repo root" in str(exc), exc

            try:
                kn.write_report(rep, os.path.join(corpus, "knowledge-report.txt"))
                assert False, "write_report разрешил не-Markdown расширение"
            except ValueError as exc:
                assert "unsupported report suffix" in str(exc), exc

            print("TESTS OK knowledge: docs=%d types=%s redaction/report-out ok" % (n, sorted(types)))
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
