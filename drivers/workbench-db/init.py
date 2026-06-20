#!/usr/bin/env python3
"""Workbench DB init — создание и миграция SQLite БД."""

import sqlite3
import os
import sys
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DEFAULT_DB = Path(__file__).parent / "workbench.db"


def init_db(db_path=None):
    """Создать или обновить БД по schema.sql."""
    db = db_path or DEFAULT_DB
    db = Path(db)
    
    # Ensure parent exists
    db.parent.mkdir(parents=True, exist_ok=True)
    
    # Read schema
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    conn = sqlite3.connect(str(db))
    conn.executescript(schema)
    conn.commit()
    
    # Check version
    cur = conn.execute("SELECT value FROM __meta__ WHERE key = 'schema_version'")
    row = cur.fetchone()
    version = row[0] if row else 'unknown'
    
    conn.close()
    print(f"Workbench DB initialized: {db} (schema v{version})")
    return str(db)


def main():
    db = sys.argv[1] if len(sys.argv) > 1 else None
    init_db(db)


if __name__ == "__main__":
    main()
