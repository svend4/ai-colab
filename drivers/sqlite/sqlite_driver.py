#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sqlite driver (L2, read-only) — инспекция и запрос произвольных SQLite-БД.

Безопасный доступ к таблицам/схеме/строкам любой `.db`/`.sqlite` внутри allowed-root.
Дополняет `data` (CSV/TSV) для реального источника — SQLite-баз приложений.

Защита (несколько уровней):
- БД открывается строго read-only на уровне СУБД: `sqlite3.connect("file:...?mode=ro", uri=True)` —
  любые записи/DDL невозможны;
- allowed-root confinement + whitelist суффиксов (`.db/.sqlite/.sqlite3`);
- имя таблицы валидируется по реальному списку таблиц (нет SQL-инъекции через идентификатор);
- `query` принимает только одиночный `SELECT`/`WITH`; лимит строк; redaction секретов в ячейках;
- busy/timeout, чтобы не зависнуть.

CLI:
    python sqlite_driver.py tables <db>
    python sqlite_driver.py schema <db> <table>
    python sqlite_driver.py head   <db> <table> [--n N]
    python sqlite_driver.py query  <db> "SELECT ..."
"""
import os
import re
import sys
import json
import sqlite3
from pathlib import Path

_DRIVERS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _DRIVERS not in sys.path:
    sys.path.insert(0, _DRIVERS)
from redaction import redact  # общий redaction-хелпер драйверов

DEFAULT_MAX_ROWS = 100
MAX_ROWS = 1000
ALLOWED_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
CONNECT_TIMEOUT = 5.0


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


class PathAccessError(ValueError):
    pass


class QueryNotAllowed(ValueError):
    pass


def _resolve(db_path, base_dir=None):
    if base_dir is None:
        p = Path(db_path).expanduser().resolve()
    else:
        base = Path(base_dir).expanduser().resolve()
        raw = Path(db_path).expanduser()
        p = (raw if raw.is_absolute() else base / raw).resolve()
        try:
            p.relative_to(base)
        except ValueError:
            raise PathAccessError("db path is outside allowed root: %s" % p)
    if p.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("unsupported db suffix: %s" % p.suffix)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    return p


def _connect_ro(db_path, base_dir=None):
    """Открыть БД строго read-only (mode=ro на уровне СУБД)."""
    p = _resolve(db_path, base_dir)
    uri = "file:%s?mode=ro" % p.as_uri()[len("file:"):]
    conn = sqlite3.connect(uri, uri=True, timeout=CONNECT_TIMEOUT)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(db_path, base_dir=None):
    conn = _connect_ro(db_path, base_dir)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [r["name"] for r in rows]
    finally:
        conn.close()


def _check_table(conn, table):
    names = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view')").fetchall()}
    if table not in names:
        raise ValueError("no such table: %s" % table)
    return table


def table_schema(db_path, table, base_dir=None):
    conn = _connect_ro(db_path, base_dir)
    try:
        _check_table(conn, table)
        # table уже проверена по whitelist реальных имён → безопасно подставить в PRAGMA
        cols = conn.execute('PRAGMA table_info("%s")' % table.replace('"', '""')).fetchall()
        return [{"name": c["name"], "type": c["type"], "notnull": c["notnull"],
                 "pk": c["pk"]} for c in cols]
    finally:
        conn.close()


def _redact_row(row):
    return {k: (redact(v) if isinstance(v, str) else v) for k, v in dict(row).items()}


def table_head(db_path, table, n=DEFAULT_MAX_ROWS, base_dir=None):
    conn = _connect_ro(db_path, base_dir)
    try:
        _check_table(conn, table)
        n = max(1, min(int(n), MAX_ROWS))
        rows = conn.execute('SELECT * FROM "%s" LIMIT %d' % (table.replace('"', '""'), n)).fetchall()
        return [_redact_row(r) for r in rows]
    finally:
        conn.close()


_SELECT_RE = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


def query(db_path, sql, base_dir=None, max_rows=DEFAULT_MAX_ROWS):
    """Выполнить одиночный read-only SELECT/WITH. Записи невозможны (mode=ro), плюс guard по типу."""
    stripped = sql.strip().rstrip(";")
    if ";" in stripped:
        raise QueryNotAllowed("only a single statement is allowed")
    if not _SELECT_RE.match(stripped):
        raise QueryNotAllowed("only SELECT/WITH queries are allowed")
    conn = _connect_ro(db_path, base_dir)
    try:
        n = max(1, min(int(max_rows), MAX_ROWS))
        cur = conn.execute(stripped)
        rows = cur.fetchmany(n)
        return [_redact_row(r) for r in rows]
    finally:
        conn.close()


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        base_dir = a[a.index("--base") + 1] if "--base" in a else None
        n = int(a[a.index("--n") + 1]) if "--n" in a else DEFAULT_MAX_ROWS
        if cmd == "tables":
            print(json.dumps(list_tables(a[1], base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "schema" and len(a) > 2:
            print(json.dumps(table_schema(a[1], a[2], base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "head" and len(a) > 2:
            print(json.dumps(table_head(a[1], a[2], n=n, base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "query" and len(a) > 2:
            print(json.dumps(query(a[1], a[2], base_dir=base_dir, max_rows=n), ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
