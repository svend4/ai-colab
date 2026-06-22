#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/top.py (T-138)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import top


def run():
    rows = top.button_rows()
    ids = {r["id"] for r in rows}
    assert "health" in ids, ids
    assert "take-task" in ids, ids
    assert "knowledge-report" in ids, ids
    assert "report-diff" in ids, ids
    assert "cohort-board" in ids, ids
    assert "variants" in ids, ids
    assert "merge-gate" in ids, ids
    assert "work-mode" in ids, ids
    assert "synthesis-helper" in ids, ids
    assert any(r["audience"] == "human" for r in rows), rows
    assert any(r["audience"] == "agent" for r in rows), rows
    rendered = top.format_buttons(rows)
    assert "Top command buttons" in rendered, rendered
    assert "python tools/top.py health" in rendered, rendered
    assert "python tools/top.py report-diff" in rendered, rendered
    assert "python tools/top.py work-mode" in rendered, rendered
    parser = top.build_parser()
    args = parser.parse_args(["cycle", "codex"])
    assert args.cmd == "cycle" and args.agent == "codex", args
    kargs = parser.parse_args(["knowledge", "docs", "--db", "tmp-work/x.db", "--query", "pipeline"])
    assert kargs.cmd == "knowledge" and kargs.db == "tmp-work/x.db", kargs
    wargs = parser.parse_args(["work-mode", "codex", "T-144", "--parallel"])
    assert wargs.cmd == "work-mode" and top._work_mode_choice(wargs) == "worktree", wargs
    sargs = parser.parse_args(["work-mode", "codex", "T-144", "--mode", "shared"])
    assert top._work_mode_choice(sargs) == "shared", sargs
    print("TESTS OK top: buttons/cycle/work-mode parser")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)