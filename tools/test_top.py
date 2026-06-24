#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_top
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_top.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Tests for tools/top.py (T-138)."""
import os
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import top


def run():
    rows = top.button_rows()
    ids = {r["id"] for r in rows}
    assert "health" in ids, ids
    assert "friction-status" in ids, ids
    assert "assurance" in ids, ids
    assert "advice-activator" in ids, ids
    assert "instruction-preflight" in ids, ids
    assert "take-task" in ids, ids
    assert "knowledge-report" in ids, ids
    assert "repo-search" in ids, ids
    assert "report-diff" in ids, ids
    assert "cohort-board" in ids, ids
    assert "conveyor-status" in ids, ids
    assert "variants" in ids, ids
    assert "merge-gate" in ids, ids
    assert "work-mode" in ids, ids
    assert "subagent-handoff" in ids, ids
    assert "synthesis-helper" in ids, ids
    assert "cauldron-lanes" in ids, ids
    assert "synthesize-docs" in ids, ids
    assert any(r["audience"] == "human" for r in rows), rows
    assert any(r["audience"] == "agent" for r in rows), rows
    rendered = top.format_buttons(rows)
    assert "Top command buttons" in rendered, rendered
    assert "python tools/top.py health" in rendered, rendered
    assert "python tools/top.py friction" in rendered, rendered
    assert "python tools/top.py assurance" in rendered, rendered
    assert "python tools/top.py advice" in rendered, rendered
    assert "python tools/top.py agent-start <agent> [--task T-id] [--context" in rendered, rendered
    assert "python tools/top.py instruction-preflight" in rendered, rendered
    assert "python tools/top.py repo-search" in rendered, rendered
    assert "python tools/top.py report-diff" in rendered, rendered
    assert "python tools/top.py conveyor" in rendered, rendered
    assert "python tools/top.py work-mode" in rendered, rendered
    assert "python tools/top.py subagent-handoff" in rendered, rendered
    assert "python tools/top.py cauldron-lanes" in rendered, rendered
    assert "python tools/top.py synthesize-docs" in rendered, rendered
    parser = top.build_parser()
    fargs = parser.parse_args(["friction", "--json"])
    assert fargs.cmd == "friction" and fargs.json, fargs
    aargs = parser.parse_args(["assurance", "currency", "--json", "--max-age", "90"])
    assert aargs.cmd == "assurance" and aargs.section == "currency" and aargs.json and aargs.max_age == 90, aargs
    sargs = parser.parse_args(["assurance", "flow", "--strict"])
    assert sargs.cmd == "assurance" and sargs.section == "flow" and sargs.strict, sargs
    adv_args = parser.parse_args(["advice", "codex", "T-188", "--parallel", "--hot-files", "--json"])
    assert adv_args.cmd == "advice" and adv_args.agent == "codex" and adv_args.task == "T-188" and adv_args.parallel and adv_args.hot_files and adv_args.json, adv_args
    start_args = parser.parse_args(["agent-start", "codex", "--task", "T-188", "--context", "repo", "search", "--context-limit", "4"])
    assert start_args.cmd == "agent-start" and start_args.agent == "codex" and start_args.task == "T-188" and start_args.context == ["repo", "search"] and start_args.context_limit == 4, start_args
    ip_args = parser.parse_args(["instruction-preflight", "codex", "T-154", "--json"])
    assert ip_args.cmd == "instruction-preflight" and ip_args.agent == "codex" and ip_args.task == "T-154" and ip_args.json, ip_args
    take_args = parser.parse_args(["take", "codex", "T-152"])
    assert take_args.cmd == "take" and take_args.agent == "codex" and take_args.task == "T-152", take_args
    args = parser.parse_args(["cycle", "codex"])
    assert args.cmd == "cycle" and args.agent == "codex", args
    kargs = parser.parse_args(["knowledge", "docs", "--db", "tmp-work/x.db", "--query", "pipeline"])
    assert kargs.cmd == "knowledge" and kargs.db == "tmp-work/x.db", kargs
    rsargs = parser.parse_args(["repo-search", "parallel", "policy", "--limit", "3", "--json"])
    assert rsargs.cmd == "repo-search" and rsargs.query == ["parallel", "policy"] and rsargs.limit == 3 and rsargs.json, rsargs
    cvargs = parser.parse_args(["conveyor", "--target", "2", "--idle", "10", "--json"])
    assert cvargs.cmd == "conveyor" and cvargs.target == 2 and cvargs.idle == 10 and cvargs.json, cvargs
    clargs = parser.parse_args(["cauldron-lanes", "architecture-core", "--json"])
    assert clargs.cmd == "cauldron-lanes" and clargs.topic == "architecture-core" and clargs.json, clargs
    sdargs = parser.parse_args(["synthesize-docs", "architecture-core", "--with-streams", "--out", "docs/x.md"])
    assert sdargs.cmd == "synthesize-docs" and sdargs.with_streams and sdargs.out == "docs/x.md", sdargs
    hargs = parser.parse_args(["subagent-handoff", "mavis", "T-200", "parallel", "policy", "--worktree"])
    assert hargs.cmd == "subagent-handoff" and hargs.agent == "mavis" and hargs.task == "T-200" and hargs.context == ["parallel", "policy"] and hargs.worktree and not hargs.json, hargs
    hjargs = parser.parse_args(["subagent-handoff", "mavis", "T-200", "parallel", "policy", "--worktree", "--json"])
    assert hjargs.cmd == "subagent-handoff" and hjargs.json, hjargs
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "subagent-handoff", "mavis", "T-200", "parallel", "policy", "--worktree", "--json"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    payload = json.loads(p.stdout)
    assert payload["schema"] == "subagent_launch_plan.v1" and payload["task"] == "T-200", payload
    wargs = parser.parse_args(["work-mode", "codex", "T-144", "--parallel"])
    assert wargs.cmd == "work-mode" and top._work_mode_choice(wargs) == "worktree", wargs
    sargs = parser.parse_args(["work-mode", "codex", "T-144", "--mode", "shared"])
    assert top._work_mode_choice(sargs) == "shared", sargs
    print("TESTS OK top: buttons/cycle/take/work-mode/subagent-handoff/conveyor/process-landed/assurance parser+json")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)