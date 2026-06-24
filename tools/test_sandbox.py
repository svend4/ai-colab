#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_sandbox
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_sandbox.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест external-source intake (tools/sandbox.py) — read-only, без запуска кода."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sandbox as sb


def run():
    sid = "_sbtest"
    manifest = os.path.join(sb.INBOX, "%s.md" % sid)
    report = os.path.join(sb.REPORTS, "%s-inventory.md" % sid)
    ok = True
    try:
        r = sb.intake(sid, os.path.join(ROOT, "data", "fixtures"), note="тест intake")
        assert os.path.exists(r["manifest"]) and os.path.exists(r["report"]), r
        assert sid in sb.list_sources(), sb.list_sources()
        rep = open(report, encoding="utf-8").read()
        assert "Inventory:" in rep and "read-only" in rep, rep[:200]
        man = open(manifest, encoding="utf-8").read()
        assert "type: external-source" in man and "status: quarantine" in man, man[:200]
        print("TESTS OK sandbox: intake %s (files=%s, risks=%d, read-only)" % (sid, r["files"], r["risks"]))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        for p in (manifest, report):
            try:
                os.remove(p)
            except OSError:
                pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
