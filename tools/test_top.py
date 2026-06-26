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
import shutil
import io
import contextlib

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
    assert "butterfly-synthesis" in ids, ids
    assert "advice-activator" in ids, ids
    assert "instruction-preflight" in ids, ids
    assert "take-task" in ids, ids
    assert "knowledge-report" in ids, ids
    assert "repo-search" in ids, ids
    assert "variant-start" in ids, ids
    assert "variant-batch" in ids, ids
    assert "draft-code" in ids, ids
    assert "info-draft" in ids, ids
    assert "report-diff" in ids, ids
    assert "question-tree" in ids, ids
    assert "cohort-board" in ids, ids
    assert "conveyor-status" in ids, ids
    assert "conveyor-recover" in ids, ids
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
    assert "python tools/top.py butterfly" in rendered, rendered
    assert "python tools/top.py advice" in rendered, rendered
    assert "python tools/top.py agent-start <agent> [--task T-id] [--context" in rendered, rendered
    assert "python tools/top.py instruction-preflight" in rendered, rendered
    assert "python tools/top.py repo-search" in rendered, rendered
    assert "python tools/top.py variant-start" in rendered, rendered
    assert "python tools/top.py variant-batch" in rendered, rendered
    assert "python tools/top.py draft-code" in rendered, rendered
    assert "python tools/top.py info-draft" in rendered, rendered
    assert "python tools/top.py report-diff" in rendered, rendered
    assert "python tools/top.py question-tree" in rendered, rendered
    assert "--action-plan" in rendered, rendered
    assert "python tools/top.py conveyor" in rendered, rendered
    assert "python tools/top.py conveyor-recover" in rendered, rendered
    assert "python tools/top.py work-mode" in rendered, rendered
    assert "python tools/top.py subagent-handoff" in rendered, rendered
    assert "python tools/top.py cauldron-lanes" in rendered, rendered
    assert "python tools/top.py synthesize-docs" in rendered, rendered
    assert "--ready-only" in rendered, rendered
    parser = top.build_parser()
    fargs = parser.parse_args(["friction", "--json"])
    assert fargs.cmd == "friction" and fargs.json, fargs
    bargs = parser.parse_args(["butterfly", "--seed", "codex", "--json", "--apply-graph", "--apply-topic"])
    assert bargs.cmd == "butterfly" and bargs.seed == "codex" and bargs.json and bargs.apply_graph and bargs.apply_topic, bargs
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
    vargs = parser.parse_args(["variant-start", "codex", "parallel", "policy", "--task", "T-254", "--reason", "smoke", "--json", "--no-search", "--no-preflight", "--stream-root", "tmp-work/top-variant-test"])
    assert vargs.cmd == "variant-start" and vargs.agent == "codex" and vargs.topic == ["parallel", "policy"] and vargs.task == "T-254" and vargs.reason == "smoke" and vargs.json and vargs.no_search, vargs
    snargs = parser.parse_args(["variant-start", "codex", "parallel", "policy", "--search-now", "--no-preflight"])
    assert snargs.cmd == "variant-start" and snargs.search_now and not snargs.no_search, snargs
    vbargs = parser.parse_args(["variant-batch", "batch", "topic", "--agents", "codex,mavis", "--task", "T-259", "--quorum", "2", "--batch-id", "smoke", "--stream-root", "tmp-work/top-variant-batch-test", "--json"])
    assert vbargs.cmd == "variant-batch" and vbargs.topic == ["batch", "topic"] and vbargs.agents == ["codex,mavis"] and vbargs.task == "T-259" and vbargs.quorum == 2 and vbargs.batch_id == "smoke" and vbargs.json, vbargs
    dcargs = parser.parse_args(["draft-code", "list", "--root", "tmp-work/top-draft-code-test", "--json"])
    assert dcargs.cmd == "draft-code" and dcargs.draft_args == ["list", "--root", "tmp-work/top-draft-code-test", "--json"], dcargs
    idargs = parser.parse_args(["info-draft", "list", "--root", "tmp-work/top-info-draft-test", "--json"])
    assert idargs.cmd == "info-draft" and idargs.info_args == ["list", "--root", "tmp-work/top-info-draft-test", "--json"], idargs
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            parser.parse_args(["variant-start", "codex", "parallel", "policy", "--no-search", "--search-now"])
        raise AssertionError("variant-start accepted conflicting search flags")
    except SystemExit:
        pass

    butterfly_root = os.path.join(ROOT, "tmp-work", "top-butterfly-test")
    shutil.rmtree(butterfly_root, ignore_errors=True)
    butterfly_source = os.path.join(butterfly_root, "outbox")
    butterfly_index = os.path.join(butterfly_root, "indexes")
    os.makedirs(butterfly_source, exist_ok=True)
    os.makedirs(butterfly_index, exist_ok=True)
    butterfly_graph = os.path.join(butterfly_index, "cauldron_graph.json")
    butterfly_out = os.path.join(butterfly_root, "topics", "alchemy.md")
    with open(os.path.join(butterfly_source, "report.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Report\n\nНовый dry-run атом для верхней панели и безопасной сверки котла.\n")
    with open(butterfly_graph, "w", encoding="utf-8", newline="\n") as f:
        json.dump([
            {"hash": "a1", "source_file": "seed.md", "content": "Первый существующий атом для синтеза верхнего слоя."},
            {"hash": "b2", "source_file": "seed.md", "content": "Второй существующий атом описывает безопасный dry-run."},
            {"hash": "c3", "source_file": "seed.md", "content": "Третий существующий атом задает границу apply-флага."},
        ], f, ensure_ascii=False)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "butterfly",
                        "--source-dir", butterfly_source,
                        "--graph", butterfly_graph,
                        "--out", butterfly_out,
                        "--seed", "codex",
                        "--created-at", "2026-06-26T00:00:00",
                        "--json"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    butterfly_payload = json.loads(p.stdout)
    assert butterfly_payload["schema"] == "top_butterfly.v1" and butterfly_payload["mutates"] is False, butterfly_payload
    assert butterfly_payload["graph"]["payload"]["mode"] == "dry-run", butterfly_payload
    assert butterfly_payload["alchemy"]["payload"]["mode"] == "dry-run", butterfly_payload
    assert not os.path.exists(butterfly_out), butterfly_payload
    shutil.rmtree(butterfly_root, ignore_errors=True)
    qtargs = parser.parse_args(["question-tree", "topics/information-refactoring-question-tree-2026-06-25.md", "--category", "open", "--action-plan", "--json", "--limit", "5"])
    assert qtargs.cmd == "question-tree" and qtargs.category == "open" and qtargs.action_plan and qtargs.json and qtargs.limit == 5, qtargs
    qcmd = top._question_tree_cmd(qtargs.path, qtargs.category, qtargs.json, qtargs.limit, qtargs.action_plan)
    assert "question_tree.py" in qcmd[1] and "--action-plan" in qcmd and "--category" in qcmd and "--json" in qcmd, qcmd
    cvargs = parser.parse_args(["conveyor", "--target", "2", "--idle", "10", "--json"])
    assert cvargs.cmd == "conveyor" and cvargs.target == 2 and cvargs.idle == 10 and cvargs.json, cvargs
    crargs = parser.parse_args(["conveyor-recover", "--limit", "3", "--json"])
    assert crargs.cmd == "conveyor-recover" and crargs.limit == 3 and crargs.json, crargs
    crcmd = top._conveyor_recover_cmd(limit=3, json_output=True)
    assert crcmd[-5:] == [os.path.join(ROOT, "tools", "conveyor.py"), "recover", "--json", "--limit", "3"] or ("recover" in crcmd and "--json" in crcmd and "--limit" in crcmd), crcmd
    assert not any(part in crcmd for part in ["land", "ship", "dismiss", "launch", "tick"]), crcmd
    clargs = parser.parse_args(["cauldron-lanes", "architecture-core", "--json", "--ready-only"])
    assert clargs.cmd == "cauldron-lanes" and clargs.topic == "architecture-core" and clargs.json and clargs.ready_only, clargs
    sdargs = parser.parse_args(["synthesize-docs", "architecture-core", "--with-streams", "--ready-only", "--out", "docs/x.md"])
    assert sdargs.cmd == "synthesize-docs" and sdargs.with_streams and sdargs.ready_only and sdargs.out == "docs/x.md", sdargs
    hargs = parser.parse_args(["subagent-handoff", "mavis", "T-200", "parallel", "policy", "--worktree"])
    assert hargs.cmd == "subagent-handoff" and hargs.agent == "mavis" and hargs.task == "T-200" and hargs.context == ["parallel", "policy"] and hargs.worktree and not hargs.json, hargs
    hjargs = parser.parse_args(["subagent-handoff", "mavis", "T-200", "parallel", "policy", "--worktree", "--json"])
    assert hjargs.cmd == "subagent-handoff" and hjargs.json, hjargs
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "subagent-handoff", "mavis", "T-200", "parallel", "policy", "--worktree", "--json"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    payload = json.loads(p.stdout)
    assert payload["schema"] == "subagent_launch_plan.v1" and payload["task"] == "T-200", payload

    variant_root = os.path.join(ROOT, "tmp-work", "top-variant-test")
    shutil.rmtree(variant_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "variant-start", "codex", "variant", "start", "smoke", "--reason", "smoke", "--json", "--no-search", "--no-preflight", "--stream-root", "tmp-work/top-variant-test"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    vp = json.loads(p.stdout)
    assert vp["schema"] == "top_variant_start.v1" and vp["mutates"] is True, vp
    assert vp["stream"]["id"] and vp["stream"]["relpath"].startswith("tmp-work/top-variant-test/"), vp
    assert os.path.exists(vp["stream"]["path"]), vp
    assert vp["repo_search"]["skipped"] and not vp["repo_search"]["deferred"], vp
    assert not any(cmd.startswith("python tools\\\\top.py repo-search") for cmd in vp["next_commands"]), vp
    assert any("independent_first.py check" in cmd for cmd in vp["next_commands"]), vp
    assert any("ready-for-synthesis" in cmd for cmd in vp["next_commands"]), vp
    shutil.rmtree(variant_root, ignore_errors=True)

    defer_root = os.path.join(ROOT, "tmp-work", "top-variant-defer-test")
    shutil.rmtree(defer_root, ignore_errors=True)

    draft_root = os.path.join(ROOT, "tmp-work", "top-draft-code-test")
    shutil.rmtree(draft_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "draft-code", "list", "--root", "tmp-work/top-draft-code-test", "--json"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    dp = json.loads(p.stdout)
    assert dp["schema"] == "draft_code_list.v1" and dp["drafts"] == [], dp
    shutil.rmtree(draft_root, ignore_errors=True)
    info_root = os.path.join(ROOT, "tmp-work", "top-info-draft-test")
    shutil.rmtree(info_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "info-draft", "list", "--root", "tmp-work/top-info-draft-test", "--json"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    ip = json.loads(p.stdout)
    assert ip["schema"] == "info_draft_list.v1" and ip["drafts"] == [], ip
    shutil.rmtree(info_root, ignore_errors=True)
    batch_root = os.path.join(ROOT, "tmp-work", "top-variant-batch-test")
    shutil.rmtree(batch_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "variant-batch", "variant", "batch", "smoke", "--agents", "codex,mavis", "--task", "T-259", "--batch-id", "smoke", "--json", "--stream-root", "tmp-work/top-variant-batch-test"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    bp = json.loads(p.stdout)
    assert bp["schema"] == "top_variant_batch.v1" and bp["mutates"] is True, bp
    assert bp["batch_id"] == "smoke" and bp["agents"] == ["codex", "mavis"], bp
    assert bp["phase"] == "draft" and bp["missing_agents"] == ["codex", "mavis"], bp
    assert bp["manifest"]["relpath"].startswith("tmp-work/top-variant-batch-test/variant-batch-smoke/_batches/"), bp
    assert os.path.exists(bp["manifest"]["path"]), bp
    with open(bp["manifest"]["path"], encoding="utf-8") as f:
        bm = json.load(f)
    assert bm["schema"] == "top_variant_batch.v1" and bm["quorum"] == 2, bm
    assert all("variant-start" in cmd and "--no-preflight" in cmd for cmd in bp["per_agent_commands"]), bp
    assert any("cauldron-lanes" in cmd and "--ready-only" in cmd for cmd in bp["barrier_commands"]), bp
    created_streams = []
    for root, _dirs, files in os.walk(batch_root):
        for name in files:
            if name == "STREAM.md":
                created_streams.append(os.path.join(root, name))
    assert not created_streams, created_streams
    shutil.rmtree(batch_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "variant-start", "codex", "variant", "start", "defer", "--reason", "defer", "--json", "--no-preflight", "--stream-root", "tmp-work/top-variant-defer-test"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    dvp = json.loads(p.stdout)
    assert dvp["repo_search"]["skipped"] and dvp["repo_search"]["deferred"], dvp
    assert dvp["next_commands"][0].startswith("# edit "), dvp
    assert any("independent_first.py check" in cmd for cmd in dvp["next_commands"]), dvp
    assert any("repo-search" in cmd for cmd in dvp["next_commands"]), dvp
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "variant-start", "codex", "variant", "start", "text", "--reason", "text", "--no-preflight", "--stream-root", "tmp-work/top-variant-defer-test"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    assert "status: `deferred`" in p.stdout and "repo-search" in p.stdout, p.stdout
    shutil.rmtree(defer_root, ignore_errors=True)

    draft_root = os.path.join(ROOT, "tmp-work", "top-draft-code-test")
    shutil.rmtree(draft_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "draft-code", "list", "--root", "tmp-work/top-draft-code-test", "--json"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    dp = json.loads(p.stdout)
    assert dp["schema"] == "draft_code_list.v1" and dp["drafts"] == [], dp
    shutil.rmtree(draft_root, ignore_errors=True)
    info_root = os.path.join(ROOT, "tmp-work", "top-info-draft-test")
    shutil.rmtree(info_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "info-draft", "list", "--root", "tmp-work/top-info-draft-test", "--json"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    ip = json.loads(p.stdout)
    assert ip["schema"] == "info_draft_list.v1" and ip["drafts"] == [], ip
    shutil.rmtree(info_root, ignore_errors=True)
    batch_root = os.path.join(ROOT, "tmp-work", "top-variant-batch-test")
    shutil.rmtree(batch_root, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(HERE, "top.py"), "variant-batch", "variant", "batch", "smoke", "--agents", "codex,mavis", "--task", "T-259", "--batch-id", "smoke", "--json", "--stream-root", "tmp-work/top-variant-batch-test"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.stdout, p.stderr)
    bp = json.loads(p.stdout)
    assert bp["schema"] == "top_variant_batch.v1" and bp["mutates"] is True, bp
    assert bp["batch_id"] == "smoke" and bp["agents"] == ["codex", "mavis"], bp
    assert bp["phase"] == "draft" and bp["missing_agents"] == ["codex", "mavis"], bp
    assert bp["manifest"]["relpath"].startswith("tmp-work/top-variant-batch-test/variant-batch-smoke/_batches/"), bp
    assert os.path.exists(bp["manifest"]["path"]), bp
    with open(bp["manifest"]["path"], encoding="utf-8") as f:
        bm = json.load(f)
    assert bm["schema"] == "top_variant_batch.v1" and bm["quorum"] == 2, bm
    assert all("variant-start" in cmd and "--no-preflight" in cmd for cmd in bp["per_agent_commands"]), bp
    assert any("cauldron-lanes" in cmd and "--ready-only" in cmd for cmd in bp["barrier_commands"]), bp
    created_streams = []
    for root, _dirs, files in os.walk(batch_root):
        for name in files:
            if name == "STREAM.md":
                created_streams.append(os.path.join(root, name))
    assert not created_streams, created_streams
    shutil.rmtree(batch_root, ignore_errors=True)
    wargs = parser.parse_args(["work-mode", "codex", "T-144", "--parallel"])
    assert wargs.cmd == "work-mode" and top._work_mode_choice(wargs) == "worktree", wargs
    sargs = parser.parse_args(["work-mode", "codex", "T-144", "--mode", "shared"])
    assert top._work_mode_choice(sargs) == "shared", sargs
    print("TESTS OK top: buttons/cycle/take/work-mode/subagent-handoff/variant-start/variant-batch/conveyor/conveyor-recover/process-landed/assurance parser+json")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
