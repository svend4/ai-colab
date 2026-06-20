#!/usr/bin/env python3
"""Workbench DB query — базовые операции с БД."""

import sqlite3
import json
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "workbench.db"


def _conn(db_path=None):
    db = db_path or DEFAULT_DB
    return sqlite3.connect(str(db))


# --- documents ---

def insert_document(source, path, doc_type, lang=None, summary=None,
                    size_bytes=None, risk=None, source_last_verified=None,
                    db_path=None):
    conn = _conn(db_path)
    conn.execute("""
        INSERT OR REPLACE INTO documents
        (source, path, type, lang, summary, size_bytes, risk, source_last_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (source, path, doc_type, lang, summary, size_bytes, risk, source_last_verified))
    conn.commit()
    doc_id = conn.execute("SELECT id FROM documents WHERE source=? AND path=?", (source, path)).fetchone()[0]
    conn.close()
    return doc_id


def search_documents(query, db_path=None):
    """Search by path or summary using LIKE (fallback if FTS5 unavailable)."""
    conn = _conn(db_path)
    conn.row_factory = sqlite3.Row
    pattern = f"%{query}%"
    rows = conn.execute("""
        SELECT * FROM documents
        WHERE path LIKE ? OR summary LIKE ?
        ORDER BY created_at DESC
    """, (pattern, pattern)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_documents(source=None, doc_type=None, risk=None, db_path=None):
    conn = _conn(db_path)
    conn.row_factory = sqlite3.Row
    sql = "SELECT * FROM documents WHERE 1=1"
    params = []
    if source:
        sql += " AND source = ?"
        params.append(source)
    if doc_type:
        sql += " AND type = ?"
        params.append(doc_type)
    if risk:
        sql += " AND risk = ?"
        params.append(risk)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- audit_log ---

def log_event(agent, action, target=None, detail=None, db_path=None):
    conn = _conn(db_path)
    conn.execute("""
        INSERT INTO audit_log (agent, action, target, detail)
        VALUES (?, ?, ?, ?)
    """, (agent, action, target, detail))
    conn.commit()
    conn.close()


def get_audit(agent=None, action=None, limit=50, db_path=None):
    conn = _conn(db_path)
    conn.row_factory = sqlite3.Row
    sql = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    if agent:
        sql += " AND agent = ?"
        params.append(agent)
    if action:
        sql += " AND action = ?"
        params.append(action)
    sql += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- drivers ---

def upsert_driver(driver_id, name, level, mode, status, db_path=None):
    conn = _conn(db_path)
    conn.execute("""
        INSERT INTO drivers (id, name, level, mode, status, last_run, run_count)
        VALUES (?, ?, ?, ?, ?, datetime('now'), 1)
        ON CONFLICT(id) DO UPDATE SET
            last_run = datetime('now'),
            run_count = run_count + 1
    """, (driver_id, name, level, mode, status))
    conn.commit()
    conn.close()


def get_driver_stats(driver_id, db_path=None):
    conn = _conn(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


if __name__ == "__main__":
    # Demo
    db = DEFAULT_DB
    print("Demo workbench DB queries")
    
    # Init if not exists
    from init import init_db
    init_db(db)
    
    # Insert test document
    doc_id = insert_document("local", "/test/file.md", "file", 
                             lang="Markdown", summary="Test doc", 
                             size_bytes=1024, risk="low", db_path=db)
    print(f"Inserted document: {doc_id}")
    
    # Search
    results = search_documents("test", db_path=db)
    print(f"Search results: {len(results)}")
    
    # Log event
    log_event("Novax", "inventory", "documents:1", "Test audit", db_path=db)
    
    # Get audit
    audit = get_audit(limit=10, db_path=db)
    print(f"Audit entries: {len(audit)}")
    
    print("Demo complete.")
