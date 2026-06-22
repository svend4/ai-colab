#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instruction assurance preflight (T-154).

Read-only helper that tells a human/agent which repo instructions apply to the
current task and prints a short evidence template for the final report.

CLI:
    python tools/instructions.py manifest [--json]
    python tools/instructions.py preflight <agent> [T-id] [--json]
    python tools/instructions.py check-report <path>
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
try:
    from _canon import parse_front_matter
except ImportError:  # pragma: no cover - fallback for copied standalone use
    def parse_front_matter(text):
        return {}


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_output()

INSTRUCTIONS = [
    {
        "id": "agent-rules",
        "path": "AGENTS.md",
        "scope": "all",
        "why": "роли агентов, зоны записи, запрет переписывать чужую работу",
        "evidence": "указать, что зона записи и ограничения агента соблюдены",
    },
    {
        "id": "collab-protocol",
        "path": "PROTOCOL.md",
        "scope": "all",
        "why": "append-only полилог, D-003 обоснование правок, pipeline, streams, уровни папок",
        "evidence": "указать, где оставлен outbox/topic rationale и почему общие файлы менялись так",
    },
    {
        "id": "human-map",
        "path": "README.md",
        "scope": "onboarding",
        "why": "человеко-читаемая карта структуры workspace",
        "evidence": "не обязательно в каждом отчёте; достаточно для нового участника",
    },
    {
        "id": "agent-onboarding",
        "path": "docs/agent-onboarding.md",
        "scope": "onboarding",
        "why": "present-tense карта возможностей и ролей",
        "evidence": "если агент новый, указать, что использовал эту карту входа",
    },
    {
        "id": "top-manual",
        "path": "docs/top-agent-operating-manual.md",
        "scope": "all",
        "why": "операционная инструкция вершины пирамиды и рабочий цикл агента",
        "evidence": "сослаться на выбранный рабочий цикл и ограничения execute/read-only",
    },
    {
        "id": "top-buttons",
        "path": "docs/top-layer-command-groups.md",
        "scope": "all",
        "why": "единая панель команд, чтобы не помнить десятки отдельных сценариев",
        "evidence": "указать, какие top-команды были использованы или почему не нужны",
    },
    {
        "id": "pipeline-guide",
        "path": "docs/pipeline-operator-guide.md",
        "scope": "task",
        "why": "claim/done/fencing/snapshot и правило одной задачи за раз",
        "evidence": "указать claim_id или почему задача выполнялась без claim",
    },
    {
        "id": "friction-playbook",
        "path": "docs/friction-playbook.md",
        "scope": "all",
        "why": "повторяющиеся проблемы и рецепты: temp, encoding, dirty tree, stale indexes",
        "evidence": "перечислить F-id или рецепт, если он применялся",
    },
    {
        "id": "parallel-work-policy",
        "path": "docs/parallel-work-policy.md",
        "scope": "dirty-or-parallel",
        "why": "Level 0/Level 1, selective-add, foreign half-done, hot files",
        "evidence": "указать shared tree/worktree и почему выбран этот режим",
    },
    {
        "id": "commit-stream-policy",
        "path": "docs/commit-stream-policy.md",
        "scope": "commit-or-variant",
        "why": "commit-lock, selective-add, streams как полу-коммиты вариантов",
        "evidence": "указать, что staged был явный список файлов или создан stream",
    },
    {
        "id": "external-sandbox",
        "path": "docs/external-code-sandbox.md",
        "scope": "external-code",
        "why": "read-only intake внешних источников; execute закрыт до gate",
        "evidence": "указать, что внешний код не запускался или что использован sandbox intake",
    },
    {
        "id": "execute-preflight",
        "path": "docs/execute-sandbox-preflight.md",
        "scope": "external-code",
        "why": "условия до любого execute чужого кода",
        "evidence": "указать, что execute не включался без accepted decision",
    },
    {
        "id": "instruction-assurance",
        "path": "docs/instruction-assurance.md",
        "scope": "all",
        "why": "модель metadata -> preflight -> evidence -> gate",
        "evidence": "добавить блок Applied instructions в отчёт",
    },
]

BY_ID = {item["id"]: item for item in INSTRUCTIONS}
CORE_IDS = [
    "agent-rules",
    "collab-protocol",
    "top-manual",
    "top-buttons",
    "pipeline-guide",
    "friction-playbook",
    "instruction-assurance",
]
ONBOARDING_IDS = ["human-map", "agent-onboarding"]
DIRTY_IDS = ["parallel-work-policy", "commit-stream-policy"]
EXTERNAL_IDS = ["external-sandbox", "execute-preflight"]
VARIANT_IDS = ["commit-stream-policy", "parallel-work-policy"]


def rel(path):
    return path.replace("\\", "/")


def repo_path(relpath):
    return os.path.join(ROOT, relpath.replace("/", os.sep))


def read_text(relpath):
    try:
        with open(repo_path(relpath), encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def file_exists(relpath):
    return os.path.exists(repo_path(relpath))


def run_cmd(*args, timeout=20):
    try:
        p = subprocess.run(
            list(args),
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = ""
        if exc.stdout:
            out += str(exc.stdout)
        if exc.stderr:
            out += str(exc.stderr)
        return 124, out


def git_status_paths():
    rc, out = run_cmd("git", "status", "--short", "--untracked-files=all", timeout=20)
    if rc != 0:
        return []
    paths = []
    for raw in out.splitlines():
        if len(raw) < 4:
            continue
        path = raw[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(rel(path))
    return paths


def instruction_entry(item, reason=None):
    path = item["path"]
    return {
        "id": item["id"],
        "path": path,
        "exists": file_exists(path),
        "scope": item["scope"],
        "why": reason or item["why"],
        "evidence": item["evidence"],
    }


def task_context(task_id):
    if not task_id:
        return None
    norm = task_id.upper()
    if not norm.startswith("T-"):
        norm = "T-" + norm
    path = "tasks/%s.md" % norm
    text = read_text(path)
    fm = parse_front_matter(text) if text else {}
    return {
        "id": norm,
        "path": path,
        "exists": bool(text),
        "title": fm.get("title", ""),
        "status": fm.get("status", ""),
        "owner": fm.get("owner", ""),
        "topic": fm.get("topic", ""),
        "depends_on": fm.get("depends_on", ""),
        "next": fm.get("next", ""),
        "front_matter": fm,
    }


def text_keywords(ctx):
    if not ctx:
        return ""
    fields = [ctx.get("title", ""), ctx.get("topic", ""), ctx.get("next", "")]
    if ctx.get("exists"):
        fields.append(read_text(ctx["path"])[:4000])
    return "\n".join(fields).lower()


def add_unique(out, item):
    if item["id"] not in {x["id"] for x in out}:
        out.append(item)


def build_preflight(agent=None, task_id=None, include_onboarding=False):
    ctx = task_context(task_id) if task_id else None
    dirty = git_status_paths()
    kw = text_keywords(ctx)
    selected = []

    for ident in CORE_IDS:
        add_unique(selected, instruction_entry(BY_ID[ident]))

    if include_onboarding or not task_id:
        for ident in ONBOARDING_IDS:
            add_unique(selected, instruction_entry(BY_ID[ident]))

    if ctx:
        add_unique(selected, {
            "id": "task-card",
            "path": ctx["path"],
            "exists": ctx["exists"],
            "scope": "task",
            "why": "источник правды по задаче: критерии done, owner, depends_on, topic",
            "evidence": "указать, какие критерии done закрыты и что осталось",
        })
        topic = ctx.get("topic") or ""
        if topic:
            add_unique(selected, {
                "id": "task-topic",
                "path": topic,
                "exists": file_exists(topic),
                "scope": "task",
                "why": "профильная документация/тема задачи из front-matter",
                "evidence": "указать, какие положения topic использованы",
            })

    if dirty:
        for ident in DIRTY_IDS:
            add_unique(selected, instruction_entry(BY_ID[ident], reason="рабочее дерево dirty; нужна дисциплина selective-add/worktree"))

    if any(word in kw for word in ["external", "sandbox", "svend4", "execute", "внешн", "песоч"]):
        for ident in EXTERNAL_IDS:
            add_unique(selected, instruction_entry(BY_ID[ident]))

    if any(word in kw for word in ["synthesis", "variant", "stream", "fork", "синтез", "вариант", "ручей", "расхожд"]):
        for ident in VARIANT_IDS:
            add_unique(selected, instruction_entry(BY_ID[ident]))

    gates = [
        "python tools/top.py status %s" % agent if agent else "python tools/top.py status <agent>",
        "python tools/friction.py status --agent %s --task %s" % (agent or "<agent>", ctx["id"] if ctx else "<T-id>"),
        "python tools/generate.py --check",
        "python tools/validate.py",
        "python tools/top.py health",
    ]
    if dirty:
        gates.append("commit stage: explicit file list only; no git add -A in dirty shared tree")

    evidence = [
        "`AGENTS.md` / `PROTOCOL.md`: zone/write rules respected; no чужие сообщения overwritten.",
        "Task: `%s` %s." % (ctx["id"], "done criteria checked" if ctx else "not specified"),
        "Instruction preflight: `python tools/instructions.py preflight %s%s`." % (
            agent or "<agent>", " " + ctx["id"] if ctx else ""),
        "Friction/work-mode: dirty tree checked; shared/worktree choice explained.",
        "Checks: list exact commands and results.",
        "Commit safety: commit_lock + explicit staging if a commit was made.",
    ]

    return {
        "root": ROOT,
        "agent": agent or "",
        "task": ctx,
        "dirty_paths": dirty,
        "instructions": selected,
        "gates": gates,
        "evidence_template": evidence,
    }


def manifest_payload():
    return {"instructions": [instruction_entry(item) for item in INSTRUCTIONS]}


def format_manifest(payload):
    lines = ["# Instruction manifest", "", "| ID | Scope | Exists | Path | Why |", "|---|---|---|---|---|"]
    for item in payload["instructions"]:
        lines.append("| {id} | {scope} | {exists} | `{path}` | {why} |".format(**item))
    return "\n".join(lines)


def format_preflight(payload):
    task = payload.get("task") or {}
    lines = [
        "# Instruction preflight",
        "",
        "agent: `%s`" % (payload.get("agent") or "<not specified>"),
        "task: `%s`" % (task.get("id") or "<not specified>"),
    ]
    if task:
        lines.append("task status: `%s`, owner: `%s`, topic: `%s`" % (
            task.get("status", ""), task.get("owner", ""), task.get("topic", "")))
    if payload.get("dirty_paths"):
        lines.append("dirty paths: %d" % len(payload["dirty_paths"]))
    lines.extend(["", "## Read/apply", "", "| ID | Exists | Path | Why | Evidence expected |", "|---|---|---|---|---|"])
    for item in payload["instructions"]:
        lines.append("| {id} | {exists} | `{path}` | {why} | {evidence} |".format(**item))
    lines.extend(["", "## Gates before done/commit", ""])
    for gate in payload["gates"]:
        lines.append("- `%s`" % gate if gate.startswith("python ") else "- %s" % gate)
    lines.extend(["", "## Applied instructions template", "", "```md", "## Applied instructions", ""])
    for ev in payload["evidence_template"]:
        lines.append("- %s" % ev)
    lines.extend(["```", ""])
    return "\n".join(lines)


def check_report_text(text):
    required = ["## Applied instructions", "AGENTS.md", "PROTOCOL.md", "Checks:"]
    return [token for token in required if token not in text]


def cmd_manifest(args):
    payload = manifest_payload()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_manifest(payload))
    return 0


def cmd_preflight(args):
    payload = build_preflight(args.agent, args.task, include_onboarding=args.onboarding)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_preflight(payload))
    missing = [i["path"] for i in payload["instructions"] if not i.get("exists")]
    return 1 if missing else 0


def cmd_check_report(args):
    path = args.path if os.path.isabs(args.path) else os.path.join(ROOT, args.path)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as exc:
        print("ERROR: cannot read report: %s" % exc)
        return 1
    missing = check_report_text(text)
    if missing:
        print("MISSING Applied instructions evidence: %s" % ", ".join(missing))
        return 1
    print("OK: Applied instructions evidence present")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Instruction assurance preflight for agents and humans.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("manifest", help="show curated instruction manifest")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_manifest)

    p = sub.add_parser("preflight", help="show task-scoped instruction checklist")
    p.add_argument("agent")
    p.add_argument("task", nargs="?")
    p.add_argument("--json", action="store_true")
    p.add_argument("--onboarding", action="store_true", help="also include human/new-agent onboarding docs")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("check-report", help="check that a report has an Applied instructions section")
    p.add_argument("path")
    p.set_defaults(func=cmd_check_report)

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
