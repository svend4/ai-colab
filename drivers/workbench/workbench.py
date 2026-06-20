#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
workbench.db (SQLite) — слой памяти L6 (T-052), реализация схемы T-031.

Чистая stdlib (`sqlite3`). Таблицы `documents` (корпус) и `audit_log` (журнал
действий агентов). Драйверы-инвентаризаторы (files/repo-runner) кладут сюда записи,
конвейер — события; агенты делают повторяемый поиск/отчётность.

CLI:
    python workbench.py init <db>
    python workbench.py list <db> [--type T] [--risk R] [--text S]
    python workbench.py audit <db> [--agent A]
"""
import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path

DEFAULT_MAX_QUERY_LIMIT = 1000
DEFAULT_MAX_INGEST_DOCUMENTS = 1000
ALLOWED_DB_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  path TEXT NOT NULL,
  type TEXT,
  lang TEXT,
  summary TEXT,
  size_bytes INTEGER DEFAULT 0,
  risk TEXT DEFAULT 'low',
  source_last_verified TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(source, path)
);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
CREATE INDEX IF NOT EXISTS idx_documents_risk ON documents(risk);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  agent TEXT,
  action TEXT,
  target TEXT,
  detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_log(agent);
"""


class PathAccessError(ValueError):
    pass


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def resolve_db_path(db_path, base_dir=None):
    if base_dir is None:
        resolved = Path(db_path).expanduser().resolve()
    else:
        base = Path(base_dir).expanduser().resolve()
        raw_path = Path(db_path).expanduser()
        resolved = (raw_path if raw_path.is_absolute() else base / raw_path).resolve()
        if not _is_relative_to(resolved, base):
            raise PathAccessError(f"db path is outside allowed root: {resolved}")
    if resolved.suffix.lower() not in ALLOWED_DB_SUFFIXES:
        raise ValueError(f"unsupported db suffix: {resolved.suffix}")
    return resolved


def _bounded_limit(limit, max_limit=DEFAULT_MAX_QUERY_LIMIT):
    value = int(limit)
    if value <= 0:
        raise ValueError("limit must be positive")
    return min(value, max_limit)


def connect(db_path, base_dir=None):
    resolved = resolve_db_path(db_path, base_dir=base_dir)
    conn = sqlite3.connect(str(resolved))
    conn.row_factory = sqlite3.Row
    return conn


def init(db_path, base_dir=None):
    conn = connect(db_path, base_dir=base_dir)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def add_document(conn, source, path, type=None, lang=None, summary=None,
                 size_bytes=0, risk="low", source_last_verified=None):
    conn.execute(
        """INSERT INTO documents(source,path,type,lang,summary,size_bytes,risk,source_last_verified,created_at)
           VALUES(?,?,?,?,?,?,?,?,?)
           ON CONFLICT(source,path) DO UPDATE SET
             type=excluded.type, lang=excluded.lang, summary=excluded.summary,
             size_bytes=excluded.size_bytes, risk=excluded.risk,
             source_last_verified=excluded.source_last_verified""",
        (source, path, type, lang, summary, size_bytes, risk, source_last_verified, _now()),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM documents WHERE source=? AND path=?", (source, path)).fetchone()
    return row["id"]


def query_documents(conn, type=None, risk=None, text=None, limit=100):
    limit = _bounded_limit(limit)
    q = "SELECT * FROM documents WHERE 1=1"
    p = []
    if type:
        q += " AND type=?"; p.append(type)
    if risk:
        q += " AND risk=?"; p.append(risk)
    if text:
        q += " AND (path LIKE ? OR summary LIKE ?)"; p += ["%" + text + "%", "%" + text + "%"]
    q += " ORDER BY id LIMIT ?"; p.append(limit)
    return [dict(r) for r in conn.execute(q, p).fetchall()]


def log(conn, agent, action, target=None, detail=None):
    conn.execute("INSERT INTO audit_log(ts,agent,action,target,detail) VALUES(?,?,?,?,?)",
                 (_now(), agent, action, target, detail))
    conn.commit()


def audit(conn, agent=None, limit=50):
    limit = _bounded_limit(limit)
    if agent:
        rows = conn.execute("SELECT * FROM audit_log WHERE agent=? ORDER BY id DESC LIMIT ?", (agent, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def ingest_repo(conn, scan_report, source="repo", verified=None, max_documents=DEFAULT_MAX_INGEST_DOCUMENTS):
    """Занести файлы из отчёта repo-runner.scan_repo в documents (по риску из отчёта)."""
    max_documents = _bounded_limit(max_documents, DEFAULT_MAX_INGEST_DOCUMENTS)
    risks = {r.get("file"): r.get("severity", "medium") for r in scan_report.get("risks", [])}
    n = 0
    for rel in scan_report.get("structure", []):
        if n >= max_documents:
            break
        add_document(conn, source, source + ":" + rel, type="file",
                     lang=os.path.splitext(rel)[1], risk=risks.get(rel, "low"),
                     source_last_verified=verified)
        n += 1
    return n


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    cmd, db = a[0], a[1]
    base_dir = os.environ.get("WORKBENCH_BASE") or os.getcwd()

    def opt(name):
        return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else None

    try:
        conn = init(db, base_dir=base_dir)
        if cmd == "init":
            print(json.dumps({"db": str(resolve_db_path(db, base_dir=base_dir)), "ok": True}))
            return 0
        if cmd == "list":
            print(json.dumps(query_documents(conn, type=opt("--type"), risk=opt("--risk"),
                                             text=opt("--text"), limit=opt("--limit") or 100),
                             ensure_ascii=False, indent=2))
            return 0
        if cmd == "audit":
            print(json.dumps(audit(conn, agent=opt("--agent"), limit=opt("--limit") or 50),
                             ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
