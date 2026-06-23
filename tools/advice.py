#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advice activator (TBD) - show existing repo advice that is applicable now.

This is not a new policy engine. It connects current symptoms from existing
 tools (`friction.py`, `assurance.py`) to already documented advice and prints
 the command that activates that advice in the working cycle.

CLI:
    python tools/advice.py current <agent> [T-id] [--parallel] [--hot-files] [--json]
"""
import argparse
import json
import os
import sys
from _ioutil import configure_output

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import assurance
import friction

configure_output()

WORKTREE_FIDS = {"F-006", "F-007", "F-011", "F-013", "F-015", "F-020"}

def _task(task):
    return task or "<T-id>"

def _warn_or_fail_ids(friction_payload):
    ids = []
    for ch in friction_payload.get("checks", []):
        if ch.get("status") in {"warn", "fail"}:
            ids.append(ch.get("id"))
    return [i for i in ids if i]

def _checks_by_id(friction_payload):
    out = {}
    for ch in friction_payload.get("checks", []):
        out.setdefault(ch.get("id"), []).append(ch)
    return out

def _assurance_findings(assurance_results):
    findings = []
    for sec in assurance_results:
        for f in sec.get("findings", []):
            findings.append({
                "section": sec.get("name"),
                "level": f.get("level"),
                "msg": f.get("msg"),
                "where": f.get("where"),
            })
    return findings

def _item(aid, priority, title, why_now, sources, activate, evidence=None):
    return {
        "id": aid,
        "priority": priority,
        "title": title,
        "why_now": why_now,
        "sources": sources,
        "activate": activate,
        "evidence": evidence or [],
    }

def advice_from_signals(agent, task, friction_payload, assurance_results,
                        parallel=False, hot_files=False):
    """Pure advice router: current symptoms -> existing advice -> activation command."""
    tid = _task(task)
    warn_ids = set(_warn_or_fail_ids(friction_payload))
    checks = _checks_by_id(friction_payload)
    assurance_finds = _assurance_findings(assurance_results)
    advice = []

    advice.append(_item(
        "A-001",
        "baseline",
        "Run task-scoped instruction preflight",
        "Every non-trivial task should start by selecting applicable instructions, not by memory.",
        ["docs/instruction-assurance.md", "tools/instructions.py", "tools/top.py"],
        ["python tools/top.py instruction-preflight %s %s" % (agent, tid)],
    ))

    if warn_ids:
        evidence = sorted(warn_ids)
        advice.append(_item(
            "A-002",
            "high",
            "Apply friction recipes before repeating a manual workaround",
            "friction.py reports active warnings/failures; the recipes already exist.",
            ["docs/friction-playbook.md", "docs/friction-ledger.md", "tools/friction.py"],
            ["python tools/top.py friction"] +
            ["python tools/friction.py recipe %s" % fid for fid in evidence[:5]],
            evidence=evidence,
        ))

    if parallel or hot_files or (warn_ids & WORKTREE_FIDS):
        reasons = []
        if parallel:
            reasons.append("parallel work requested")
        if hot_files:
            reasons.append("hot files are planned")
        reasons.extend(sorted(warn_ids & WORKTREE_FIDS))
        flags = []
        if parallel:
            flags.append("--parallel")
        if hot_files:
            flags.append("--hot-files")
        if warn_ids:
            flags.append("--dirty-mainline")
        advice.append(_item(
            "A-003",
            "high",
            "Activate Level 0/Level 1 work-mode decision",
            "The repository already knows when shared-tree work is risky; make the choice explicit.",
            ["docs/parallel-work-policy.md", "docs/commit-stream-policy.md", "tools/top.py", "tools/flow.py"],
            [("python tools/top.py work-mode %s %s %s" % (agent, tid, " ".join(flags))).rstrip()],
            evidence=reasons,
        ))

    if "F-004" in warn_ids:
        advice.append(_item(
            "A-004",
            "medium",
            "Use project temp helpers instead of stdlib tempfile",
            "The advice exists because this Windows runtime can create temp dirs that cannot be written.",
            ["docs/friction-playbook.md", "drivers/test_tmp.py", "tools/friction.py"],
            ["python tools/friction.py recipe F-004"],
            evidence=[e for ch in checks.get("F-004", []) for e in ch.get("evidence", [])[:3]],
        ))

    if "F-009" in warn_ids:
        advice.append(_item(
            "A-005",
            "medium",
            "Do not let placeholder tasks enter normal execution",
            "Placeholder-gating advice exists and is currently relevant to the pipeline.",
            ["docs/pipeline-placeholder-gating.md", "tools/pipeline.py", "tools/friction.py"],
            ["python tools/pipeline.py status", "python tools/friction.py recipe F-009"],
            evidence=[e for ch in checks.get("F-009", []) for e in ch.get("evidence", [])[:4]],
        ))

    if assurance_finds:
        top = assurance_finds[:5]
        advice.append(_item(
            "A-006",
            "high",
            "Close instruction-assurance findings, not just document them",
            "assurance.py found gaps where instructions/evidence exist as a concept but are not fully applied.",
            ["docs/instruction-assurance.md", "tools/assurance.py", "tools/instructions.py"],
            ["python tools/top.py assurance all", "python tools/top.py assurance all --json"],
            evidence=["%s: %s" % (f.get("section"), f.get("msg")) for f in top],
        ))

    return {
        "agent": agent,
        "task": task,
        "friction_recommendation": friction_payload.get("recommendation"),
        "warn_or_fail_ids": sorted(warn_ids),
        "assurance_findings": assurance_finds,
        "advice": advice,
    }

def collect_current(args):
    fargs = argparse.Namespace(
        agent=args.agent,
        task=args.task,
        files=[],
        temp_probe=args.temp_probe,
        stream_max_age_days=args.stream_max_age_days,
    )
    friction_payload = friction.status_payload(fargs)
    assurance_results = assurance.run("all", ROOT, args.max_age)
    return advice_from_signals(
        args.agent,
        args.task,
        friction_payload,
        assurance_results,
        parallel=args.parallel,
        hot_files=args.hot_files,
    )

def render(payload):
    lines = [
        "# Advice activator",
        "",
        "agent: `%s`" % payload["agent"],
        "task: `%s`" % _task(payload.get("task")),
        "friction: %s" % payload.get("friction_recommendation"),
        "",
        "| ID | Priority | Advice already exists | Activate |",
        "|---|---|---|---|",
    ]
    for item in payload["advice"]:
        activate = "<br>".join("`%s`" % cmd for cmd in item.get("activate", []))
        lines.append("| {id} | {priority} | {title} | {activate} |".format(
            id=item["id"],
            priority=item["priority"],
            title=item["title"],
            activate=activate,
        ))
    lines.extend(["", "## Evidence"])
    for item in payload["advice"]:
        if not item.get("evidence"):
            continue
        lines.append("")
        lines.append("### %s" % item["id"])
        for ev in item["evidence"][:8]:
            lines.append("- %s" % ev)
    lines.extend([
        "",
        "Rule: advice that repeats twice should become a friction recipe; advice that blocks commits should become a gate.",
    ])
    return "\n".join(lines)

def cmd_current(args):
    payload = collect_current(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(payload))
    return 0

def build_parser():
    parser = argparse.ArgumentParser(description="Activate existing repo advice against current symptoms.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("current", help="show applicable advice for current state")
    p.add_argument("agent")
    p.add_argument("task", nargs="?")
    p.add_argument("--parallel", action="store_true")
    p.add_argument("--hot-files", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--temp-probe", action="store_true", help="also run friction temp probe")
    p.add_argument("--stream-max-age-days", type=int, default=7)
    p.add_argument("--max-age", type=int, default=90)
    p.set_defaults(func=cmd_current)

    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())