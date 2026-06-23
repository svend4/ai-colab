#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Top command panel (T-138) — one entrypoint for humans and agents at the pyramid top.

This tool groups existing low-level commands into repeatable scenarios. It does not replace
pipeline/validate/knowledge/drivers; it makes them easier to call consistently.

    python tools/top.py buttons                  # human/agent command groups
    python tools/top.py status [agent]           # quick state: git + pipeline + drift
    python tools/top.py friction                 # repeated-problem diagnostics + recipes
    python tools/top.py assurance [section] [--json] [--strict]  # apex verifiability dashboard
    python tools/top.py advice <agent> [T-id]   # activate existing advice against current symptoms
    python tools/top.py health                   # validation/generator/capability checks
    python tools/top.py agent-start <agent> [--task T-id] [--context QUERY]  # onboard + current advice + repo search
    python tools/top.py instruction-preflight <agent> [T-id]  # applicable rules + evidence template
    python tools/top.py take <agent> [T-id]      # side effect: pipeline next or targeted claim
    python tools/top.py snapshot                 # side effect: regenerate derived snapshots
    python tools/top.py knowledge <corpus> [--query TEXT] [--out reports/x.md]
    python tools/top.py repo-search <query> [--limit N] [--json]
    python tools/top.py cycle <agent>            # print safe work cycle template
    python tools/top.py work-mode <agent> <task> # choose shared tree vs worktree
    python tools/top.py subagent-handoff <agent> <task> [context...] [--worktree] [--json]
    python tools/top.py conveyor [--target N] [--idle M] [--json]
"""
import argparse
import json
import os
import subprocess
import sys
from _ioutil import configure_output
import result_intake

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
MAX_LINES = 140

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
        "command": "python tools/top.py agent-start <agent> [--task T-id] [--context <query>]",
        "does": "Подключить агента: onboarding, конвейер, дрейф, assurance, advice и быстрый поиск по канону.",
        "effect": "read-only",
    },
    {
        "id": "instruction-preflight",
        "audience": "both",
        "command": "python tools/top.py instruction-preflight <agent> [T-id]",
        "does": "Показать task-scoped инструкции, evidence-блок и проверки перед работой/отчётом.",
        "effect": "read-only",
    },
    {
        "id": "advice-activator",
        "audience": "both",
        "command": "python tools/top.py advice <agent> [T-id] [--parallel] [--hot-files]",
        "does": "Найти уже существующие советы, применимые к текущим симптомам, и показать команды активации.",
        "effect": "read-mostly",
    },
    {
        "id": "status",
        "audience": "both",
        "command": "python tools/top.py status [agent]",
        "does": "Быстро увидеть git status, pipeline status и drift_check.",
        "effect": "read-only",
    },
    {
        "id": "friction-status",
        "audience": "both",
        "command": "python tools/top.py friction",
        "does": "Проверить повторяющиеся проблемы: dirty/stale/volatile/lock/pipeline/drift/streams/temp и получить рецепты.",
        "effect": "read-mostly",
    },
    {
        "id": "assurance",
        "audience": "both",
        "command": "python tools/top.py assurance [section] [--json] [--strict] [--max-age N]",
        "does": "Показать apex-проверяемость инструкций: applied/currency/coverage/flow; advisory по умолчанию.",
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
        "command": "python tools/top.py take <agent> [T-id]",
        "does": "Атомарно взять следующую задачу из котла или конкретную ready-задачу по T-id.",
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
    },    {
        "id": "repo-search",
        "audience": "both",
        "command": "python tools/top.py repo-search <query> [--limit N] [--json]",
        "does": "Найти решения, политики, вопросы и задачи в каноне через FTS/BM25 индекс.",
        "effect": "read-mostly; builds ignored logs/repo-knowledge.db if missing",
    },
    {
        "id": "report-diff",
        "audience": "both",
        "command": "python tools/top.py report-diff reports/a.md reports/b.md --out reports/diff.md",
        "does": "Сравнить два knowledge-отчёта по масштабу, типам и hit-count.",
        "effect": "writes report if --out",
    },
    {
        "id": "cohort-board",
        "audience": "both",
        "command": "python tools/cohort.py board",
        "does": "Показать dashboard параллельной работы: котёл, claims, drift, recent commits.",
        "effect": "read-only",
    },
    {
        "id": "conveyor-status",
        "audience": "both",
        "command": "python tools/top.py conveyor [--target N] [--idle M] [--json]",
        "does": "Показать надзирателя workflow-конвейера: REFILL/PROCESS/IDLE и кандидатов дозалива.",
        "effect": "read-only",
    },
    {
        "id": "process-landed",
        "audience": "both",
        "command": "python tools/top.py process-landed [--json] [--all] [--topic <topic>]",
        "does": "Составить read-only план обработки landed outputs: intake, evidence check, synthesis, commit/ship шаги.",
        "effect": "read-only",
    },
    {
        "id": "cohort-self",
        "audience": "agent",
        "command": "python tools/cohort.py self --json",
        "does": "Проверить, как движок обслуживает сам себя, и получить next maintenance hints.",
        "effect": "read-only",
    },
    {
        "id": "variants",
        "audience": "both",
        "command": "python tools/variants.py list --topic <topic>",
        "does": "Найти параллельные fork-варианты по теме перед синтезом.",
        "effect": "read-only",
    },
    {
        "id": "synthesis-helper",
        "audience": "both",
        "command": "python tools/synthesis_helper.py report <topic> --out topics/<topic>-synthesis.md",
        "does": "Собрать scaffold синтеза из найденных fork-вариантов без принятия решения.",
        "effect": "writes report if --out",
    },
    {
        "id": "merge-gate",
        "audience": "agent",
        "command": "python tools/merge_gate.py check <agent>",
        "does": "Проверить, безопасно ли вливать работу: validate + generate --check + permissions.",
        "effect": "read-only",
    },
    {
        "id": "stream-create",
        "audience": "agent",
        "command": "python tools/stream.py create <topic> <agent> <reason>",
        "does": "Создать semi-commit stream-пакет для варианта решения без засорения mainline.",
        "effect": "writes stream packet",
    },
    {
        "id": "promote-check",
        "audience": "both",
        "command": "python tools/promote.py check --artifact <path>",
        "does": "Проверить, готов ли артефакт к подъёму L4→L3→L2→L1.",
        "effect": "read-only",
    },
    {
        "id": "sandbox-demo",
        "audience": "both",
        "command": "python tools/sandbox_intake_demo.py --out tmp-work/sandbox-demo",
        "does": "Показать read-only intake внешнего источника на безопасных fixture-данных.",
        "effect": "writes report under --out",
        "status": "manual-demo",
        "adoption": "keep-manual: fixture-only read-only proof; not dead code and not part of normal cycle",
    },
    {
        "id": "work-cycle",
        "audience": "agent",
        "command": "python tools/top.py cycle <agent>",
        "does": "Показать безопасный цикл работы агента с claim, проверками и отчётом.",
        "effect": "read-only",
    },
    {
        "id": "subagent-handoff",
        "audience": "both",
        "command": "python tools/top.py subagent-handoff <agent> <task> [context...] [--worktree] [--json]",
        "does": "Подготовить launch-пакет для внешнего sub-agent: repo lane, prompt, старт и finish-команды.",
        "effect": "read-only",
    },
    {
        "id": "work-mode",
        "audience": "both",
        "command": "python tools/top.py work-mode <agent> <task> [--parallel|--dirty-mainline|--hot-files]",
        "does": "Подсказать режим D-021: Level 0 shared tree или Level 1 worktree-приток.",
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

def cmd_friction(args):
    cmd = _tool("friction.py", "status")
    if args.json:
        cmd.append("--json")
    if args.strict:
        cmd.append("--strict")
    return _run("friction status", cmd, timeout=90)

def cmd_assurance(args):
    cmd = _tool("assurance.py", args.section or "all")
    if args.json:
        cmd.append("--json")
    if args.strict:
        cmd.append("--strict")
    if args.max_age is not None:
        cmd += ["--max-age", str(args.max_age)]
    return _run("assurance", cmd, timeout=90, fail_ok=not args.strict)

def cmd_advice(args):
    cmd = _tool("advice.py", "current", args.agent)
    if args.task:
        cmd.append(args.task)
    if args.parallel:
        cmd.append("--parallel")
    if args.hot_files:
        cmd.append("--hot-files")
    if args.json:
        cmd.append("--json")
    return _run("advice activator", cmd, timeout=120)

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
    _run("assurance (warning layer)", _tool("assurance.py", "all"), timeout=90, fail_ok=True)
    return rc

def cmd_agent_start(args):
    rc = _run("onboard", _tool("onboard.py", args.agent), timeout=60)
    _run("top status", [PY, os.path.join(ROOT, "tools", "top.py"), "status", args.agent], timeout=90, fail_ok=True)
    _run("assurance (advisory)", _tool("assurance.py", "all"), timeout=90, fail_ok=True)
    advice_cmd = _tool("advice.py", "current", args.agent)
    if args.task:
        advice_cmd.append(args.task)
    _run("advice activator (advisory)", advice_cmd, timeout=120, fail_ok=True)
    if args.context:
        cmd = _tool("repo_search.py", "search", " ".join(args.context), "--limit", str(args.context_limit))
        _run("repo context search", cmd, timeout=90, fail_ok=True)
    return rc

def cmd_instruction_preflight(args):
    cmd = _tool("instructions.py", "preflight", args.agent)
    if args.task:
        cmd.append(args.task)
    if args.json:
        cmd.append("--json")
    if args.onboarding:
        cmd.append("--onboarding")
    return _run("instruction preflight", cmd, timeout=45)

def cmd_take(args):
    if args.task:
        return _run("pipeline claim", _tool("pipeline.py", "claim", args.agent, args.task), timeout=45)
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
    if args.db:
        cmd += ["--db", args.db]
    if args.query:
        cmd += ["--query", args.query]
    if args.out:
        cmd += ["--out", args.out]
    return _run("knowledge report", cmd, timeout=90)

def cmd_repo_search(args):
    cmd = _tool("repo_search.py", "search", " ".join(args.query), "--limit", str(args.limit))
    if args.json:
        cmd.append("--json")
    return _run("repo search", cmd, timeout=90)

def cmd_report_diff(args):
    cmd = _tool("report_diff.py", args.a, args.b)
    if args.out:
        cmd += ["--out", args.out]
    return _run("report diff", cmd, timeout=45)

def cmd_conveyor(args):
    cmd = _tool("conveyor.py", "status")
    if args.target is not None:
        cmd += ["--target", str(args.target)]
    if args.idle is not None:
        cmd += ["--idle", str(args.idle)]
    if args.json:
        cmd.append("--json")
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=45)
            if p.stdout:
                print(p.stdout.strip())
            if p.stderr:
                print(p.stderr.strip(), file=sys.stderr)
            return p.returncode
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
    return _run("conveyor status", cmd, timeout=45, fail_ok=True)

def _conveyor_status_payload(target=None, idle=None):
    cmd = _tool("conveyor.py", "status", "--json")
    if target is not None:
        cmd += ["--target", str(target)]
    if idle is not None:
        cmd += ["--idle", str(idle)]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=45)
    if p.returncode not in (0, 1):
        return {"error": "conveyor status failed", "returncode": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr}
    try:
        return json.loads(p.stdout or "{}")
    except ValueError:
        return {"error": "invalid conveyor json", "stdout": p.stdout, "stderr": p.stderr}

def _load_conveyor_ledger():
    path = os.path.join(ROOT, "logs", "conveyor.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    return data.get("workflows", [])

def _output_kind(path):
    if not path or not os.path.exists(os.path.join(ROOT, path)):
        return "result", []
    try:
        res = result_intake.classify_path(path)
        return res["class"], res.get("recommended_next_checks", [])
    except Exception:
        # Fallback if parsing fails
        p = (path or "").replace("\\", "/").lstrip("./")
        if p.startswith("streams/"):
            return "variant", []
        if p.startswith("reports/"):
            return "read-only-report", []
        if p.startswith("queues/outbox/"):
            return "agent-report", []
        if p.startswith("docs/"):
            return "docs-change", []
        if p.startswith("tasks/") or p.startswith("questions/") or p.startswith("decisions/"):
            return "governance-or-canon", []
        return "result", []

def _topic_slug(text):
    chars = []
    for ch in (text or "landed-result").lower():
        if ch.isalnum():
            chars.append(ch)
        elif chars and chars[-1] != "-":
            chars.append("-")
    slug = "".join(chars).strip("-")
    return slug[:64] or "landed-result"

def _landed_plan_for(workflow, topic=None):
    output = workflow.get("output") or "<missing-output>"
    label = workflow.get("label") or workflow.get("id") or "landed-result"
    kind, checks = _output_kind(output)
    topic = topic or _topic_slug(label)

    plan = []
    if checks:
        for c in checks:
            plan.append(c.replace("<topic>", topic))
    else:
        plan = [
            "python tools\\instructions.py check-report %s" % output,
            "python tools\\validate.py",
            "python tools\\generate.py --check",
            "python tools\\top.py assurance all",
        ]
        if kind in {"variant", "agent-report", "read-only-report"}:
            plan.append("python tools\\synthesis_helper.py report %s --out topics\\%s-synthesis.md" % (topic, topic))

    plan.append("# after review/commit: python tools\\conveyor.py ship %s" % workflow.get("id", "<workflow-id>"))
    return {"id": workflow.get("id"), "label": label, "output": output, "kind": kind,
            "topic": topic, "output_exists": os.path.exists(os.path.join(ROOT, output)), "commands": plan}

def _process_landed_payload(args):
    status = _conveyor_status_payload(args.target, args.idle)
    workflows = _load_conveyor_ledger()
    landed = [w for w in workflows if w.get("state") == "landed"]
    with_output = [w for w in landed if w.get("output")]
    missing = [w for w in landed if not w.get("output")]
    selected = with_output if args.all else with_output[:1]
    plans = [_landed_plan_for(w, args.topic) for w in selected]
    if missing:
        state = "missing-output"
    elif with_output:
        state = "ready"
    else:
        state = "empty"
    return {
        "schema": "top_process_landed.v1",
        "state": state,
        "status": status,
        "counts": {"landed": len(landed), "with_output": len(with_output), "missing_output": len(missing)},
        "missing_output": [{"id": w.get("id"), "label": w.get("label")} for w in missing],
        "plans": plans,
        "advice": _process_landed_advice(state, status, missing),
    }

def _process_landed_advice(state, status, missing):
    if state == "missing-output":
        return [
            "Stop new fan-out until every landed workflow has an output ref or a dismiss reason.",
            "Attach output: python tools\\conveyor.py land <id> --output queues\\outbox\\<result>.md",
            "Or dismiss: python tools\\conveyor.py dismiss <id> --reason \"no usable output\"",
        ]
    if state == "ready":
        return [
            "Process the selected output before raising target.",
            "Verify evidence, classify the result, synthesize variants, then ship only after review/commit.",
        ]
    actions = status.get("actions") if isinstance(status, dict) else None
    if actions:
        return list(actions)
    return ["No landed outputs. Keep target unchanged; wait for in-flight workflows or tick the conveyor."]

def cmd_process_landed(args):
    payload = _process_landed_payload(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print("# Process landed plan")
    print("")
    status = payload.get("status", {})
    if isinstance(status, dict) and "target" in status:
        print("state: `%s`  target: `%s`  in-flight: `%s`  landed: `%s`" % (
            payload["state"], status.get("target"), status.get("n_inflight"), status.get("n_landed")))
    else:
        print("state: `%s`" % payload["state"])
    print("")
    for item in payload["advice"]:
        print("- %s" % item)
    if payload["missing_output"]:
        print("")
        print("## Missing output refs")
        for item in payload["missing_output"]:
            print("- `%s` — %s" % (item.get("id") or "<id>", item.get("label") or "<label>"))
    for plan in payload["plans"]:
        print("")
        print("## Selected landed output")
        print("")
        print("- workflow: `%s`" % plan["id"])
        print("- label: %s" % plan["label"])
        print("- output: `%s`" % plan["output"])
        print("- class: `%s`" % plan["kind"])
        print("- output exists: `%s`" % str(plan["output_exists"]).lower())
        print("")
        print("```powershell")
        for cmd in plan["commands"]:
            print(cmd)
        print("```")
    return 0

def cmd_cycle(args):
    agent = args.agent
    print("# Safe agent work cycle for %s" % agent)
    print("")
    print("1. `python tools/top.py status %s`" % agent)
    print("2. `python tools/top.py advice %s <T-id>`  # activate existing advice before repeating manual workarounds" % agent)
    print("3. `python tools/top.py take %s`  # save claim_id" % agent)
    print("4. `python tools/top.py instruction-preflight %s <T-id>`" % agent)
    print("5. `python tools/top.py repo-search \"<topic/query>\" --limit 5`  # raise canonical context")
    print("6. inspect task + related docs")
    print("7. make scoped edits; write outbox/topic rationale")
    print("8. `python tools/top.py health`")
    print("9. `python tools/pipeline.py done %s <T-id> --claim <claim_id> --report \"...\" --applied \"AGENTS.md, PROTOCOL.md, Checks\"`" % agent)
    print("10. `python tools/top.py snapshot`")
    print("11. commit with `tools/commit_lock.py` + explicit `git add <files>`")
    print("")
    print("Rule: if the decision is architectural or affects people/process, create a proposed decision and leave the task blocked for Stefan/integrator approval.")
    return 0

def cmd_subagent_handoff(args):
    cmd = _tool("flow.py", "launch-plan", args.agent, args.task, *args.context)
    if args.worktree:
        cmd.append("--worktree")
    if args.json:
        cmd.append("--json")
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=45)
            if p.stdout:
                print(p.stdout.strip())
            if p.stderr:
                print(p.stderr.strip(), file=sys.stderr)
            return p.returncode
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
    return _run("subagent handoff", cmd, timeout=45)

def _work_mode_choice(args):
    if args.mode in {"shared", "worktree"}:
        return args.mode
    if args.parallel or args.dirty_mainline or args.hot_files:
        return "worktree"
    return "shared"

def cmd_work_mode(args):
    choice = _work_mode_choice(args)
    reasons = []
    if args.mode in {"shared", "worktree"}:
        reasons.append("explicit --mode %s" % args.mode)
    if args.parallel:
        reasons.append("parallel work")
    if args.dirty_mainline:
        reasons.append("dirty mainline")
    if args.hot_files:
        reasons.append("hot generated/shared files")
    if not reasons:
        reasons.append("small or isolated task")
    label = "Level 1 worktree" if choice == "worktree" else "Level 0 shared tree"

    print("# Work mode recommendation")
    print("")
    print("agent: `%s`" % args.agent)
    print("task: `%s`" % args.task)
    print("recommended: **%s**" % label)
    print("reason: %s" % ", ".join(reasons))
    print("")
    print("## Level 0 shared tree")
    print("")
    print("Use for small, low-conflict edits in the current workspace.")
    print("")
    print("```powershell")
    print("python tools/top.py status %s" % args.agent)
    print("python tools/pipeline.py mine %s" % args.agent)
    print("python tools/top.py health")
    print("python tools/merge_gate.py check %s" % args.agent)
    print('python tools/cohort.py ship %s <files> --message "%s: <summary>"' % (args.agent, args.task))
    print("```")
    print("")
    print("## Level 1 worktree")
    print("")
    print("Use for parallel/contested work, dirty mainline, or changes likely to touch generated indexes.")
    print("")
    print("```powershell")
    print("python tools/flow.py start %s %s --worktree" % (args.agent, args.task))
    print("# add --run only after reviewing the printed worktree path")
    print("python tools/flow.py finish %s %s --worktree" % (args.agent, args.task))
    print("```")
    print("")
    print("Rule: D-021 keeps Level 0 as the default; Level 1 is explicit for real parallel load.")
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

    p = sub.add_parser("friction", help="diagnose repeated repo friction and print recipes")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_friction)

    p = sub.add_parser("assurance", help="show instruction assurance apex dashboard")
    p.add_argument("section", nargs="?", default="all", choices=["applied", "currency", "coverage", "flow", "all"])
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--max-age", type=int)
    p.set_defaults(func=cmd_assurance)

    p = sub.add_parser("advice", help="show existing advice applicable to current symptoms")
    p.add_argument("agent")
    p.add_argument("task", nargs="?")
    p.add_argument("--parallel", action="store_true")
    p.add_argument("--hot-files", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_advice)

    p = sub.add_parser("health", help="validate generated state and capability indexes")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("agent-start", help="onboard an agent")
    p.add_argument("agent")
    p.add_argument("--task", help="optional T-id used by advice/preflight context")
    p.add_argument("--context", nargs="+", help="canonical repo-search query to run after status")
    p.add_argument("--context-limit", type=int, default=5)
    p.set_defaults(func=cmd_agent_start)

    p = sub.add_parser("instruction-preflight", help="show applicable instructions and evidence template")
    p.add_argument("agent")
    p.add_argument("task", nargs="?")
    p.add_argument("--json", action="store_true")
    p.add_argument("--onboarding", action="store_true")
    p.set_defaults(func=cmd_instruction_preflight)

    p = sub.add_parser("take", help="take next pipeline task or claim a specific ready T-id; writes claim/status")
    p.add_argument("agent")
    p.add_argument("task", nargs="?")
    p.set_defaults(func=cmd_take)

    p = sub.add_parser("snapshot", help="regenerate derived snapshots")
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("knowledge", help="run knowledge report")
    p.add_argument("corpus")
    p.add_argument("--query")
    p.add_argument("--db")
    p.add_argument("--out")
    p.set_defaults(func=cmd_knowledge)
    p = sub.add_parser("repo-search", help="ranked search across canonical repo documentation")
    p.add_argument("query", nargs="+")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_repo_search)

    p = sub.add_parser("report-diff", help="compare two knowledge reports")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--out")
    p.set_defaults(func=cmd_report_diff)

    p = sub.add_parser("conveyor", help="show workflow conveyor supervisor status")
    p.add_argument("--target", type=int)
    p.add_argument("--idle", type=int)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_conveyor)

    p = sub.add_parser("process-landed", help="plan intake/verify/synthesis for landed workflow outputs")
    p.add_argument("--target", type=int)
    p.add_argument("--idle", type=int)
    p.add_argument("--topic")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_process_landed)

    p = sub.add_parser("cycle", help="print safe agent work cycle")
    p.add_argument("agent")
    p.set_defaults(func=cmd_cycle)

    p = sub.add_parser("subagent-handoff", help="print repo lane and prompt for external sub-agent launch")
    p.add_argument("agent")
    p.add_argument("task")
    p.add_argument("context", nargs="*")
    p.add_argument("--worktree", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_subagent_handoff)

    p = sub.add_parser("work-mode", help="recommend Level 0 shared tree or Level 1 worktree")
    p.add_argument("agent")
    p.add_argument("task")
    p.add_argument("--mode", choices=["auto", "shared", "worktree"], default="auto")
    p.add_argument("--parallel", action="store_true")
    p.add_argument("--dirty-mainline", action="store_true")
    p.add_argument("--hot-files", action="store_true")
    p.set_defaults(func=cmd_work_mode)

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
