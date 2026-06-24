#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_advice
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_advice.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Tests for tools/advice.py."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import advice


def run():
    friction_payload = {
        "recommendation": "LEVEL 1 OR SELECTIVE-ADD",
        "checks": [
            {"id": "F-006", "status": "warn", "evidence": [" M tools/top.py"]},
            {"id": "F-004", "status": "warn", "evidence": ["tmp-work", "PermissionError"]},
            {"id": "F-011", "status": "ok", "evidence": []},
        ],
    }
    assurance_results = [
        {"name": "applied-evidence", "findings": [
            {"level": "medium", "msg": "T-180: weak evidence", "where": "queues/done/T-180.done.md"}
        ]},
        {"name": "currency", "findings": []},
    ]
    payload = advice.advice_from_signals(
        "codex", "T-188", friction_payload, assurance_results, parallel=True, hot_files=True)
    ids = {item["id"] for item in payload["advice"]}
    assert "A-001" in ids, ids
    assert "A-002" in ids, ids
    assert "A-003" in ids, ids
    assert "A-004" in ids, ids
    assert "A-006" in ids, ids
    assert "--parallel" in payload["advice"][2]["activate"][0], payload["advice"][2]

    quiet = advice.advice_from_signals(
        "codex",
        None,
        {"recommendation": "LEVEL 0 OK", "checks": [{"id": "F-006", "status": "ok"}]},
        [],
    )
    assert [item["id"] for item in quiet["advice"]] == ["A-001"], quiet
    text = advice.render(payload)
    assert "Advice activator" in text and "A-003" in text, text
    print("TESTS OK advice: pure routing/render")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)