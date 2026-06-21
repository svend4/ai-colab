#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Top command panel (T-138) — one entrypoint for humans and agents at the pyramid top.

This tool groups existing low-level commands into repeatable scenarios. It does not replace
pipeline/validate/knowledge/drivers; it makes them easier to call consistently.

    python tools/top.py buttons                  # human/agent command groups
    python tools/top.py status [agent]           # quick state: git + pipeline + drift
    python tools/top.py health                   # validation/generator/capability checks
    python tools/top.py agent-start <agent>      # onboard + current state
    python tools/top.py take <agent>             # side effect: pipeline next
    python tools/top.py snapshot                 # side effect: regenerate derived snapshots
    python tools/top.py knowledge <corpus> [--query TEXT] [--out reports/x.md]
    python tools/top.py cycle <agent>            # print safe work cycle template
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
MAX_LINES = 140


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_output()


_BUTTONS = [
    {
        "id": "start-human",
        "audience": "human",
        "command": "python tools/top.py buttons",
        "does": "Показать верхнюю панель сценариев и безопасных команд.",
        "effect": "read-only",
    },
    {
        "id": "start-agent",
        "audience": "agent",
        "command": "python tools/top.py agent-start <agent>",
        "does": "Подключить агента: onboarding, конвейер, дрейф, активные задачи.",
        "effect": "read-only",
    },
    {
        "id": "status",
        "audience": "both",
        "command": "python tools/top.py status [agent]",
        "does": "Быстро увидеть git status, pipeline status и drift_check.",
        "effect": "read-only",
    },
    {
        "id": "health",
        "audience": "both",
        "command": "python tools/top.py health",
        "does": "Проверить канон: validate, generate --check, capabilities, driver catalog.",
        "effect": "read-only",
    },
    {
        "id": "take-task",
        "audience": "agent",
        "command": "python tools/top.py take <agent>",
        "does": "Атомарно взять следующую задачу из общего котла.",
        "effect": "writes claim/status",
    },
    {
        "id": "snapshot",
        "audience": "agent",
        "command": "python tools/top.py snapshot",
        "does": "Обновить производные снимки: capabilities, drivers catalog, generated indexes, pipeline.",
        "effect": "writes generated files",
    },
    {
        "id": "knowledge-report",
        "audience": "both",
        "command": "python tools/top.py knowledge <corpus> --query <term> --out reports/<name>.md",
        "does": "Собрать knowledge-отчёт по корпусу через text_extract + FTS/report.",
        "effect": "writes report if --out",
    },
    {
        "id": "work-cycle",
        "audience": "agent",
        "command": "python tools/top.py cycle <agent>",
        "does": "Показать безопасный цикл работы агента с claim, проверками и отчётом.",
        "effect": "read-only",
    },
]


def button_rows():
    return list(_BUTTONS)


def format_buttons(rows=None):
    rows = rows or button_rows()
    out = [
        "# Top command buttons",
        "",
        "| ID | Для | Команда | Эффект | Что делает |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        out.append("| {id} | {audience} | `{command}` | {effect} | {does} |".format(**row))
    return "\n".join(out)


def _tool(script, *args):
    return [PY, os.path.join(ROOT, "tools", script), *args]


def _driver(script, *args):
    return [PY, os.path.join(ROOT, "drivers", script), *args]


def _run(label, cmd, timeout=45, fail_ok=False):
    print("\n===== %s =====" % label)
    printable = " ".join(cmd)
    print(printable)
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        text = ((p.stdout or "") + (p.stderr or "")).strip()
        if text:
            lines = text.splitlines()
            for line in lines[:MAX_LINES]:
                print(line)
            if len(lines) > MAX_LINES:
                print("... (%d more lines)" % (len(lines) - MAX_LINES))
        print("EXIT %d" % p.returncode)
        return 0 if fail_ok else p.returncode
    except subprocess.TimeoutExpired as exc:
        print("TIMEOUT after %ss: %s" % (timeout, printable))
        if exc.stdout:
            print(str(exc.stdout)[:4000])
        if exc.stderr:
            print(str(exc.stderr)[:4000])
        return 0 if fail_ok else 124


def cmd_buttons(args):
    rows = button_rows()
    if args.json:
        print(json.dumps({"buttons": rows}, ensure_ascii=False, indent=2))
    else:
        print(format_buttons(rows))
    return 0


def cmd_status(args):
    rc = 0
    rc = max(rc, _run("git status", ["git", "status", "--short", "--untracked-files=all"], timeout=20, fail_ok=True))
    rc = max(rc, _run("pipeline status", _tool("pipeline.py", "status"), timeout=30, fail_ok=True))
    rc = max(rc, _run("drift check", _tool("drift_check.py"), timeout=45, fail_ok=True))
    if args.agent:
        rc = max(rc, _run("pipeline mine", _tool("pipeline.py", "mine", args.agent), timeout=20, fail_ok=True))
    return rc


def cmd_health(_args):
    rc = 0
    for label, cmd in [
        ("validate", _tool("validate.py")),
        ("generate --check", _tool("generate.py", "--check")),
        ("capabilities --check", _tool("capabilities.py", "--check")),
        ("drivers catalog --check", _tool("drivers_catalog.py", "--check")),
    ]:
        step = _run(label, cmd, timeout=60)
        if step != 0:
            rc = step
    _run("drift check (warning layer)", _tool("drift_check.py"), timeout=60, fail_ok=True)
    return rc


def cmd_agent_start(args):
    rc = _run("onboard", _tool("onboard.py", args.agent), timeout=60)
    _run("top status", [PY, os.path.join(ROOT, "tools", "top.py"), "status", args.agent], timeout=90, fail_ok=True)
    return rc


def cmd_take(args):
    return _run("pipeline next", _tool("pipeline.py", "next", args.agent), timeout=45)


def cmd_snapshot(_args):
    rc = 0
    for label, cmd in [
        ("capabilities snapshot", _tool("capabilities.py", "snapshot")),
        ("drivers catalog", _tool("drivers_catalog.py")),
        ("generate", _tool("generate.py")),
        ("pipeline snapshot", _tool("pipeline.py", "snapshot")),
    ]:
        step = _run(label, cmd, timeout=60)
        if step != 0:
            rc = step
    return rc


def cmd_knowledge(args):
    cmd = _tool("knowledge.py", "report", args.corpus)
    if args.query:
        cmd += ["--query", args.query]
    if args.out:
        cmd += ["--out", args.out]
    return _run("knowledge report", cmd, timeout=90)


def cmd_cycle(args):
    agent = args.agent
    print("# Safe agent work cycle for %s" % agent)
    print("")
    print("1. `python tools/top.py status %s`" % agent)
    print("2. `python tools/top.py take %s`  # save claim_id" % agent)
    print("3. inspect task + related docs")
    print("4. make scoped edits; write outbox/topic rationale")
    print("5. `python tools/top.py health`")
    print("6. `python tools/pipeline.py done %s <T-id> --claim <claim_id> --report \"...\"`" % agent)
    print("7. `python tools/top.py snapshot`")
    print("8. commit with `tools/commit_lock.py` + explicit `git add <files>`")
    print("")
    print("Rule: if the decision is architectural or affects people/process, create a proposed decision and leave the task blocked for Stefan/integrator approval.")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Top command panel for humans and agents.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("buttons", help="show command groups / button candidates")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_buttons)

    p = sub.add_parser("status", help="quick state: git + pipeline + drift")
    p.add_argument("agent", nargs="?")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("health", help="validate generated state and capability indexes")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("agent-start", help="onboard an agent")
    p.add_argument("agent")
    p.set_defaults(func=cmd_agent_start)

    p = sub.add_parser("take", help="take next pipeline task; writes claim/status")
    p.add_argument("agent")
    p.set_defaults(func=cmd_take)

    p = sub.add_parser("snapshot", help="regenerate derived snapshots")
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("knowledge", help="run knowledge report")
    p.add_argument("corpus")
    p.add_argument("--query")
    p.add_argument("--out")
    p.set_defaults(func=cmd_knowledge)

    p = sub.add_parser("cycle", help="print safe agent work cycle")
    p.add_argument("agent")
    p.set_defaults(func=cmd_cycle)

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