#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge workflow (L6) — ingest → query → report на локальном корпусе.

Практический сценарий «обрабатывать/отвечать по большому объёму информации» поверх
L6-памяти (`workbench.db`): сканирует корпус драйвером `files` (с redaction секретов в
summary), заносит документы в SQLite-память, считает состав по типам/рискам и отвечает на
запрос — выдаёт markdown-отчёт. Без vector/RAG (по D-010 — до реального спроса).

Использует уже готовые движки (`files`, `workbench`); это «слой сценария» над ними,
дополняющий низкоуровневый `drivers/workbench/ingest.py`.

Поиск: `query` — простой LIKE; `search` — ранжированный полнотекстовый (FTS5 + bm25), с
fallback на LIKE, если sqlite собран без FTS5.

CLI:
    python tools/knowledge.py report <корпус> [--db logs/knowledge.db] [--query ТЕКСТ] [--out reports/name.md]
    python tools/knowledge.py query  <db> <текст>     # LIKE
    python tools/knowledge.py search <db> <текст>     # FTS5, ранжировано
"""
import os
import sys
import sqlite3
import importlib.util
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS = os.path.join(ROOT, "drivers")
DEFAULT_DB = "logs/knowledge.db"
MAX_FILES = 1000
ALLOWED_REPORT_SUFFIXES = {".md", ".markdown"}


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DRIVERS, *parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _arg_value(args, name, default=None):
    if name not in args:
        return default
    pos = args.index(name) + 1
    if pos >= len(args):
        raise ValueError("missing value for %s" % name)
    return args[pos]


def _is_relative_to(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def resolve_report_path(out_path):
    raw = Path(out_path).expanduser()
    root = Path(ROOT).resolve()
    resolved = (raw if raw.is_absolute() else root / raw).resolve()
    if not _is_relative_to(resolved, root):
        raise ValueError("report path is outside repo root: %s" % resolved)
    if resolved.suffix.lower() not in ALLOWED_REPORT_SUFFIXES:
        raise ValueError("unsupported report suffix: %s" % resolved.suffix)
    return resolved


def write_report(text, out_path):
    resolved = resolve_report_path(out_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text + "\n", encoding="utf-8", newline="\n")
    return resolved


wb = _load("kn_wb", "workbench", "workbench.py")
fd = _load("kn_files", "files", "files_driver.py")


def _first_line(rel, base):
    try:
        text = fd.read_file(os.path.join(base, rel) if not os.path.isabs(rel) else rel,
                            base_dir=base, redact=True).get("text", "")
        for line in text.splitlines():
            if line.strip():
                return line.strip()[:140]
    except Exception:
        pass
    return ""


def build(db, corpus, agent="knowledge"):
    """Сканирует корпус → заносит документы (с redacted summary) в память. Возвращает N."""
    conn = wb.init(db, base_dir=ROOT)
    try:
        src = "knowledge:" + os.path.basename(os.path.normpath(corpus))
        n = 0
        for rel in fd.list_files(corpus, max_files=MAX_FILES, base_dir=ROOT):
            ext = os.path.splitext(rel)[1].lstrip(".") or "file"
            wb.add_document(conn, src, src + ":" + rel, type=ext, lang=ext,
                            summary=_first_line(os.path.join(corpus, rel), ROOT))
            n += 1
        _build_fts(conn)  # полнотекстовый индекс для ранжированного поиска (FTS5)
        wb.log(conn, agent, "knowledge_build", corpus, "docs=%d" % n)
        return n
    finally:
        conn.close()


def _build_fts(conn):
    """Построить FTS5-индекс по documents (path+summary). Возвращает True, если FTS5 доступен."""
    try:
        conn.execute("DROP TABLE IF EXISTS kn_fts")
        conn.execute("CREATE VIRTUAL TABLE kn_fts USING fts5(doc_id UNINDEXED, path, summary)")
        rows = conn.execute("SELECT id, path, summary FROM documents").fetchall()
        conn.executemany(
            "INSERT INTO kn_fts(doc_id, path, summary) VALUES (?,?,?)",
            [(r["id"], r["path"], r["summary"] or "") for r in rows],
        )
        conn.commit()
        return True
    except sqlite3.OperationalError:
        return False  # сборка sqlite без FTS5 → поиск откатится на LIKE


def fts_search(conn, query, limit=10):
    """Ранжированный полнотекстовый поиск (FTS5 + bm25); fallback на LIKE через workbench.

    Запрос оборачивается в FTS5-фразу (кавычки), чтобы пунктуация не ломала синтаксис MATCH.
    """
    phrase = '"%s"' % str(query).replace('"', "")
    try:
        rows = conn.execute(
            "SELECT d.path AS path, d.type AS type, d.summary AS summary, bm25(kn_fts) AS rank "
            "FROM kn_fts f JOIN documents d ON d.id = f.doc_id "
            "WHERE kn_fts MATCH ? ORDER BY rank LIMIT ?",
            (phrase, int(limit)),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return wb.query_documents(conn, text=query, limit=limit)


def _counts(docs, field):
    out = {}
    for d in docs:
        k = d.get(field) or "(none)"
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def report(corpus, db=DEFAULT_DB, query_text=None):
    n = build(db, corpus)
    conn = wb.init(db, base_dir=ROOT)
    try:
        docs = wb.query_documents(conn, limit=1000)
        by_type = _counts(docs, "type")
        by_risk = _counts(docs, "risk")
        hits = fts_search(conn, query_text, limit=10) if query_text else []
    finally:
        conn.close()

    out = []
    out.append("# Knowledge report — %s" % corpus)
    out.append("")
    out.append("- Корпус: `%s` — занесено документов: **%d**" % (corpus, n))
    out.append("- База памяти: `%s` (L6 workbench.db, запрашиваемая)" % db)
    out.append("")
    out.append("## Состав по типам")
    out.append("| Тип | Документов |")
    out.append("|---|---|")
    for k, v in by_type.items():
        out.append("| %s | %d |" % (k, v))
    out.append("")
    out.append("## Состав по рискам")
    out.append("| Риск | Документов |")
    out.append("|---|---|")
    for k, v in by_risk.items():
        out.append("| %s | %d |" % (k, v))
    if query_text is not None:
        out.append("")
        out.append("## Запрос: «%s» — %d совпадений (ранжировано, FTS5)" % (query_text, len(hits)))
        out.append("| Документ | Тип | Summary |")
        out.append("|---|---|---|")
        for d in hits:
            out.append("| %s | %s | %s |" % (d.get("path"), d.get("type"), (d.get("summary") or "")[:60]))
    out.append("")
    out.append("_Запросить позже: `python tools/knowledge.py query %s \"<текст>\"`_" % db)
    return "\n".join(out)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        if cmd == "report" and len(a) > 1:
            db = _arg_value(a, "--db", DEFAULT_DB)
            q = _arg_value(a, "--query")
            out_path = _arg_value(a, "--out")
            text = report(a[1], db=db, query_text=q)
            if out_path:
                write_report(text, out_path)
            print(text)
            return 0
        if cmd == "query" and len(a) > 2:
            conn = wb.init(a[1], base_dir=ROOT)
            try:
                hits = wb.query_documents(conn, text=a[2], limit=20)
            finally:
                conn.close()
            for d in hits:
                print("%-40s %-6s %s" % (d.get("path"), d.get("type"), (d.get("summary") or "")[:60]))
            print("(%d совпадений, LIKE)" % len(hits))
            return 0
        if cmd == "search" and len(a) > 2:
            conn = wb.init(a[1], base_dir=ROOT)
            try:
                _build_fts(conn)
                hits = fts_search(conn, a[2], limit=20)
            finally:
                conn.close()
            for d in hits:
                print("%-40s %-6s %s" % (d.get("path"), d.get("type"), (d.get("summary") or "")[:60]))
            print("(%d совпадений, ранжировано FTS5)" % len(hits))
            return 0
    except Exception as exc:
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
