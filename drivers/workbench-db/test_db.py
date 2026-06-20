#!/usr/bin/env python3
"""Tests for workbench-db."""

import tempfile
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from init import init_db
from query import insert_document, search_documents, list_documents, log_event, get_audit, upsert_driver, get_driver_stats


def test_init():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        init_db(db)
        assert os.path.exists(db)
        print("PASS: init")


def test_insert_and_search():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        init_db(db)
        
        doc_id = insert_document("local", "/test/file.md", "file",
                                   lang="Markdown", summary="Test document",
                                   size_bytes=2048, risk="medium", db_path=db)
        assert doc_id is not None
        
        results = search_documents("Test", db_path=db)
        assert len(results) == 1
        assert results[0]["path"] == "/test/file.md"
        print("PASS: insert_and_search")


def test_list_by_risk():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        init_db(db)
        
        insert_document("local", "/a.md", "file", risk="low", db_path=db)
        insert_document("svend4", "/b.md", "file", risk="high", db_path=db)
        
        high = list_documents(risk="high", db_path=db)
        assert len(high) == 1
        assert high[0]["source"] == "svend4"
        print("PASS: list_by_risk")


def test_audit_log():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        init_db(db)
        
        log_event("Novax", "claim", "T-024", "Started task", db_path=db)
        log_event("Novax", "done", "T-024", "Completed", db_path=db)
        
        audit = get_audit(agent="Novax", db_path=db)
        assert len(audit) == 2
        actions = {a["action"] for a in audit}
        assert "claim" in actions
        assert "done" in actions
        print("PASS: audit_log")


def test_driver_stats():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        init_db(db)
        
        upsert_driver("repo-runner", "Repo Runner", "L1", "read-only", "ready", db_path=db)
        upsert_driver("repo-runner", "Repo Runner", "L1", "read-only", "ready", db_path=db)
        
        stats = get_driver_stats("repo-runner", db_path=db)
        assert stats["run_count"] == 2
        print("PASS: driver_stats")


if __name__ == "__main__":
    test_init()
    test_insert_and_search()
    test_list_by_risk()
    test_audit_log()
    test_driver_stats()
    print("\nAll tests passed!")
