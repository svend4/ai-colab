#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест reconcile_state fix — partition derived/primary + dry-run не пишет (smoke на реальном репо)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reconcile_state as rs


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _report(items):
    return {"items": [{"severity": s, "code": c, "task": t, "message": m, "sources": []}
                      for (s, c, t, m) in items]}


def run():
    ok = True
    try:
        rep = _report([
            ("warning", "index-status-drift", "T-1", "index != tasks"),         # derived
            ("warning", "pipeline-snapshot-drift", "-", "snapshot разошёлся"),   # derived
            ("error", "marker-but-not-done", "T-2", "маркер есть, статус нет"),  # primary
            ("warning", "doing-no-claim", "T-3", "doing без claim"),             # primary
            ("info", "pipeline-json-missing", "-", "снимок не прочитан"),        # ни то ни другое
        ])
        derived, primary = rs._partition_fix(rep)
        dcodes = {it["code"] for it in derived}
        pcodes = {it["code"] for it in primary}
        assert dcodes == {"index-status-drift", "pipeline-snapshot-drift"}, dcodes
        assert pcodes == {"marker-but-not-done", "doing-no-claim"}, pcodes
        # info (pipeline-json-missing) не идёт ни в derived, ни в primary-отказ
        assert "pipeline-json-missing" not in dcodes and "pipeline-json-missing" not in pcodes

        # каждый derived-код имеет регенератор
        for c in rs.DERIVED_CODES:
            assert c in rs._REGEN and rs._REGEN[c][1], c

        # dry-run на реальном репо: не пишет файлов, не падает, exit в {0,1,2}
        outbox = os.path.join(rs.ROOT, "queues", "outbox")
        before = set(os.listdir(outbox)) if os.path.isdir(outbox) else set()
        rc = rs.cmd_fix(apply=False)
        after = set(os.listdir(outbox)) if os.path.isdir(outbox) else set()
        assert rc in (0, 1, 2), "exit-код: %s" % rc
        assert before == after, "dry-run НЕ должен писать в outbox: %s" % (after - before)

        print("TESTS OK reconcile fix: partition(derived/primary/info) + регенераторы + dry-run без записи")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
