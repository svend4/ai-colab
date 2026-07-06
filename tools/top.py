# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.top
# TYPE: active-script
# DOMAIN: core.apex
# DEPTH_LEVEL: 1
# SUMMARY: Верхняя командная панель для людей и агентов: health, status, cycle, advice, conveyor.
# ==========================================
"""
Top command panel (T-138) — one entrypoint for humans and agents at the pyramid top.

This tool groups existing low-level commands into repeatable scenarios. It does not replace
pipeline/validate/knowledge/drivers; it makes them easier to call consistently.

    python tools/top.py buttons                  # human/agent command groups
    python tools/top.py status [agent]           # quick state: git + pipeline + drift
    python tools/top.py workspace-cell <id> [--json]  # task/thread/worktree/outbox/checks state card
    python tools/top.py code-activation <target> [--json]  # read-only code activation gates
    python tools/top.py friction                 # repeated-problem diagnostics + recipes
    python tools/top.py actions [--json]         # outbox action item status
    python tools/top.py butterfly [--seed TEXT] [--json] [--apply-graph] [--apply-topic]  # cauldron atom graph + synthesis prompt
    python tools/top.py assurance [section] [--json] [--strict]  # apex verifiability dashboard
    python tools/top.py advice <agent> [T-id]   # activate existing advice against current symptoms
    python tools/top.py health                   # validation/generator/capability checks
    python tools/top.py agent-start <agent> [--task T-id] [--context QUERY]  # onboard + current advice + repo search
    python tools/top.py instruction-preflight <agent> [T-id]  # applicable rules + evidence template
    python tools/top.py take <agent> [T-id]      # side effect: pipeline next or targeted claim
    python tools/top.py snapshot                 # side effect: regenerate derived snapshots
    python tools/top.py knowledge <corpus> [--query TEXT] [--out reports/x.md]
    python tools/top.py repo-search <query> [--limit N] [--json]
    python tools/top.py variant-start <agent> <topic...> [--task T-id] [--search-now] [--json]  # create independent-first stream

    python tools/top.py variant-batch <topic...> --agents a,b,c [--task T-id] [--json]  # batch barrier manifest
    python tools/top.py question-tree [path] [--category open] [--action-plan] [--json]  # inspect numbered meta-questions
    python tools/top.py cycle <agent>            # print safe work cycle template
    python tools/top.py work-mode <agent> <task> # choose shared tree vs worktree
    python tools/top.py subagent-handoff <agent> <task> [context...] [--worktree] [--json]
    python tools/top.py conveyor [--target N] [--idle M] [--json]
    python tools/top.py cauldron-lanes [topic] [--json] [--out PATH]  # synthesis lanes: ratify-build/divergence-detail
    python tools/top.py synthesize-docs [topic] [--json] [--out PATH] [--with-streams] [--ready-only]  # doc synthesis v2
"""
import argparse

import datetime
import json
import os
import subprocess
import sys
from _ioutil import configure_output
import result_intake
import stream as stream_tool

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
        "id": "workspace-cell",
        "audience": "both",
        "command": "python tools/top.py workspace-cell <thread-or-task> [--json]",
        "does": "Собрать read-only карточку task/thread/stream/worktree/outbox/checks/next action.",
        "effect": "read-only",
    },
    {
        "id": "code-activation",
        "audience": "both",
        "command": "python tools/top.py code-activation <target> [--json]",
        "does": "Build D-014/D-033 read-only code activation plan; no execute.",
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
        "id": "outbox-actions",
        "audience": "both",
        "command": "python tools/top.py actions [--json]",
        "does": "Показать статус outbox action items: unprocessed, partial, shipped, no-actions, historical.",
        "effect": "read-only",
    },
    {
        "id": "butterfly-synthesis",
        "audience": "both",
        "command": "python tools/top.py butterfly [--seed TEXT] [--json] [--apply-graph] [--apply-topic]",
        "does": "Запустить безопасный dry-run смыслового графа и синтез-задачи из котла; запись только явными apply-флагами.",
        "effect": "read-only by default; writes graph/topic only with explicit apply flags",
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
        "id": "variant-start",
        "audience": "agent",
        "command": "python tools/top.py variant-start <agent> <topic...> [--task T-id] [--reason TEXT] [--search-now] [--json]",
        "does": "Запустить independent-first вариант: сначала stream-пакет; repo-search отложен до явного --search-now или следующей команды.",
        "effect": "writes stream packet; search deferred by default",
    },
    {
        "id": "variant-batch",
        "audience": "agent",
        "command": "python tools/top.py variant-batch <topic...> --agents a,b,c [--task T-id] [--json]",
        "does": "Создать batch/barrier manifest для нескольких independent-first агентов; stream-файлы агенты пишут сами.",
        "effect": "writes streams/<topic>/_batches/<batch-id>.json only",
    },
    {
        "id": "draft-code",
        "audience": "both",
        "command": "python tools/top.py draft-code create <draft-id> --owner <agent> --purpose <text>",
        "does": "Прокси к no-execute draft-code manager: create/check/review/list для sandbox/drafts packets.",
        "effect": "writes draft packet only for create; check/review/list are read-only",
    },
    {
        "id": "info-draft",
        "audience": "both",
        "command": "python tools/top.py info-draft create <draft-id> --owner <agent> --purpose <text>",
        "does": "Прокси к no-canon info/document draft manager: create/check/review/list для sandbox/info-drafts packets.",
        "effect": "writes info draft packet only for create; check/review/list are read-only",
    },    {
        "id": "report-diff",
        "audience": "both",
        "command": "python tools/top.py report-diff reports/a.md reports/b.md --out reports/diff.md",
        "does": "Сравнить два knowledge-отчёта по масштабу, типам и hit-count.",
        "effect": "writes report if --out",
    },
    {
        "id": "question-tree",
        "audience": "both",
        "command": "python tools/top.py question-tree [topics/information-refactoring-question-tree-2026-06-25.md] [--category open] [--action-plan] [--json]",
        "does": "Показать старые/новые методологические вопросы или action-plan по статусам из question-tree.",
        "effect": "read-only",
    },    {
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
        "id": "conveyor-recover",
        "audience": "both",
        "command": "python tools/top.py conveyor-recover [--json] [--limit N]",
        "does": "Показать read-only recover-диагностику workflow-конвейера: stale, missing-output, refill deficit и unreferenced reports.",
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
        "id": "synthesize-docs",
        "audience": "both",
        "command": "python tools/top.py synthesize-docs [topic] [--json] [--out docs/<name>.md] [--with-streams] [--ready-only]",
        "does": "Запустить doc_synthesis v2: candidates/source-line evidence/streams scaffold или ready-only stream corpus через верхнюю панель.",
        "effect": "read-only; writes report/streams only with explicit flags",
    },    {
        "id": "cauldron-lanes",
        "audience": "both",
        "command": "python tools/top.py cauldron-lanes [topic] [--json] [--out docs/<name>.md] [--ready-only]",
        "does": "Показать две полосы котла: ratify-build для ратификации/строительства и divergence-detail для детализации споров.",
        "effect": "read-only; writes report if --out",
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
        "does": "Создать independent-first semi-commit stream-пакет для варианта решения без засорения mainline.",
        "effect": "writes stream packet",
    },
    {
        "id": "stream-ready",
        "audience": "agent",
        "command": "python tools/stream.py mark <stream-id> ready-for-synthesis <note>",
        "does": "Отметить, что независимый вариант раскрыт и готов к синтезу с другими вариантами.",
        "effect": "writes stream front-matter",
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

def cmd_actions(args):
    cmd = _tool("action_tracker.py", "status")
    if args.json:
        cmd.append("--json")
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=45)
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
        if p.stdout:
            print(p.stdout.strip())
        if p.stderr:
            print(p.stderr.strip(), file=sys.stderr)
        return p.returncode
    return _run("outbox actions", cmd, timeout=45)


def _json_command_result(label, cmd, timeout=120):
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {
            "label": label,
            "ok": False,
            "returncode": 124,
            "command": cmd,
            "error": "timeout after %ss" % timeout,
        }
    text = (p.stdout or "").strip()
    payload = None
    parse_error = None
    if text:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    result = {
        "label": label,
        "ok": p.returncode == 0 and parse_error is None,
        "returncode": p.returncode,
        "command": cmd,
        "payload": payload,
    }
    if parse_error:
        result["parse_error"] = parse_error
        result["stdout"] = text[:4000]
    if p.stderr:
        result["stderr"] = p.stderr.strip()[:4000]
    return result


def _butterfly_graph_cmd(args, json_output=False):
    cmd = _tool("butterfly_graph_builder.py", "--source-dir", args.source_dir, "--graph", args.graph)
    if args.limit is not None:
        cmd += ["--limit", str(args.limit)]
    if args.apply_graph:
        cmd.append("--apply")
    if args.force_truncate:
        cmd.append("--force-truncate")
    if json_output:
        cmd.append("--json")
    return cmd


def _butterfly_alchemy_cmd(args, json_output=False):
    cmd = _tool("butterfly_alchemist.py", "--graph", args.graph, "--sample-size", str(args.sample_size))
    if args.seed:
        cmd += ["--seed", args.seed]
    if args.created_at:
        cmd += ["--created-at", args.created_at]
    if args.out:
        cmd += ["--out", args.out]
    else:
        cmd += ["--out-dir", args.out_dir]
    if args.apply_topic:
        cmd.append("--apply")
    if args.force_truncate:
        cmd.append("--force-truncate")
    if json_output:
        cmd.append("--json")
    return cmd


def cmd_butterfly(args):
    graph_cmd = _butterfly_graph_cmd(args, json_output=args.json)
    alchemy_cmd = _butterfly_alchemy_cmd(args, json_output=args.json)
    mutates = bool(args.apply_graph or args.apply_topic)
    if args.json:
        graph_result = _json_command_result("butterfly graph", graph_cmd)
        alchemy_result = _json_command_result("butterfly alchemist", alchemy_cmd)
        payload = {
            "schema": "top_butterfly.v1",
            "mutates": mutates,
            "graph": graph_result,
            "alchemy": alchemy_result,
            "notes": [],
        }
        if not args.apply_graph:
            payload["notes"].append("graph dry-run only; use --apply-graph to update the graph")
        if not args.apply_topic:
            payload["notes"].append("topic dry-run only; use --apply-topic to write the synthesis task")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if graph_result["ok"] and alchemy_result["ok"] else 1

    rc = _run("butterfly graph", graph_cmd, timeout=120)
    step = _run("butterfly alchemist", alchemy_cmd, timeout=120, fail_ok=True)
    if step != 0:
        rc = step
    if not mutates:
        print("\nread-only: no graph/topic writes were made; use --apply-graph and/or --apply-topic explicitly")
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
        ("metadata soft-check", _tool("enforce_metadata.py", "--warn-only")),
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

def _capture_cmd(cmd, timeout=90):
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           stdin=subprocess.DEVNULL)
        return {"returncode": p.returncode, "stdout": p.stdout or "", "stderr": p.stderr or "",
                "command": " ".join(cmd)}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "",
                "command": " ".join(cmd), "error": "timeout"}


def _repo_rel(path):
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return path


def _resolve_repo_dir(path):
    if not path:
        return None
    dest = path if os.path.isabs(path) else os.path.join(ROOT, path)
    dest_r = os.path.realpath(dest)
    root_r = os.path.realpath(ROOT)
    if os.path.commonpath([dest_r, root_r]) != root_r:
        raise ValueError("refusing path outside repo: %s" % path)
    return dest_r


def _variant_start_payload(args):
    topic = " ".join(args.topic).strip()
    if not topic:
        raise ValueError("topic is required")
    stream_root = _resolve_repo_dir(args.stream_root) if args.stream_root else None
    reason = args.reason or "independent-first variant for %s" % topic

    created = stream_tool.create(topic, args.agent, reason, root=stream_root)
    stream_path = created["path"]
    stream_rel = _repo_rel(stream_path)
    topic_slug = created.get("topic") or _topic_slug(topic)

    topic_for_ps = '"' + topic.replace('"', '`"') + '"'
    repo_search_next_cmd = "python tools\\top.py repo-search %s --limit %s" % (topic_for_ps, args.search_limit)
    repo_search_run_cmd = _tool("repo_search.py", "search", topic, "--limit", str(args.search_limit))

    if args.no_search:
        repo_search = {
            "skipped": True,
            "deferred": False,
            "reason": "--no-search requested",
            "command": repo_search_next_cmd,
        }
    elif args.search_now:
        repo_search = _capture_cmd(repo_search_run_cmd, timeout=90)
        repo_search["deferred"] = False
        repo_search["search_now"] = True
        repo_search["top_command"] = repo_search_next_cmd
    else:
        repo_search = {
            "skipped": True,
            "deferred": True,
            "reason": "independent-first default: fill the stream before repo-search",
            "command": repo_search_next_cmd,
        }

    root_suffix = ""
    if args.stream_root:
        root_suffix = " --root %s" % args.stream_root
    mark_cmd = 'python tools\\stream.py mark %s ready-for-synthesis "variant completed"%s' % (created["id"], root_suffix)

    preflight = None
    preflight_cmd = None
    if args.task:
        preflight_cmd = "python tools\\top.py instruction-preflight %s %s" % (args.agent, args.task)
        if not args.no_preflight:
            preflight = _capture_cmd(_tool("instructions.py", "preflight", args.agent, args.task), timeout=45)

    independent_check_cmd = "python tools\\independent_first.py check %s --json" % stream_rel
    next_commands = [
        "# edit %s first: fill independent sections 01-03 before repo-search" % stream_rel,
        independent_check_cmd,
    ]
    if preflight_cmd:
        next_commands.append(preflight_cmd)
    if not args.no_search:
        if args.search_now:
            next_commands.append("# repo-search already executed by --search-now; repeat only if context changed")
        next_commands.append(repo_search_next_cmd)
    next_commands.extend([
        mark_cmd,
        "python tools\\stream.py check --max-age-days 7%s" % root_suffix,
        "python tools\\synthesis_helper.py report %s --out topics\\%s-synthesis.md" % (topic_slug, topic_slug),
    ])

    return {
        "schema": "top_variant_start.v1",
        "mutates": True,
        "agent": args.agent,
        "task": args.task,
        "topic": topic,
        "reason": reason,
        "stream": {"id": created["id"], "topic": topic_slug, "path": stream_path, "relpath": stream_rel},
        "repo_search": repo_search,
        "instruction_preflight": preflight,
        "next_commands": next_commands,
        "policy": "D-028 independent-first: write the independent variant before repo-search/comparison; do not treat same topic as duplicate before synthesis.",
    }


def cmd_variant_start(args):
    try:
        payload = _variant_start_payload(args)
    except Exception as exc:
        if args.json:
            print(json.dumps({"schema": "top_variant_start.v1", "error": str(exc)}, ensure_ascii=False))
        else:
            print("ERROR: %s" % exc)
        return 1
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("# Variant start")
    print("")
    print("agent: `%s`" % payload["agent"])
    if payload.get("task"):
        print("task: `%s`" % payload["task"])
    print("topic: %s" % payload["topic"])
    print("stream: `%s`" % payload["stream"]["relpath"])
    print("stream id: `%s`" % payload["stream"]["id"])
    print("")
    print("## Next commands")
    print("")
    print("```powershell")
    for cmd in payload["next_commands"]:
        print(cmd)
    print("```")
    if payload.get("repo_search"):
        print("")
        print("## Repo search")
        rs = payload["repo_search"]
        if rs.get("skipped"):
            status = "deferred" if rs.get("deferred") else "skipped"
            print("status: `%s`" % status)
            print("reason: %s" % rs.get("reason"))
            if rs.get("command"):
                print("command: `%s`" % rs.get("command"))
        else:
            print("status: `executed`")
            if rs.get("top_command") or rs.get("command"):
                print("command: `%s`" % (rs.get("top_command") or rs.get("command")))
            print("returncode: `%s`" % rs.get("returncode"))
            lines = (rs.get("stdout") or rs.get("stderr") or "").splitlines()
            for line in lines[:40]:
                print(line)
            if len(lines) > 40:
                print("... (%d more lines)" % (len(lines) - 40))
    if payload.get("instruction_preflight"):
        print("")
        print("## Instruction preflight")
        pf = payload["instruction_preflight"]
        print("returncode: `%s`" % pf.get("returncode"))
        lines = (pf.get("stdout") or pf.get("stderr") or "").splitlines()
        for line in lines[:40]:
            print(line)
        if len(lines) > 40:
            print("... (%d more lines)" % (len(lines) - 40))
    return 0


def _ps_quote(text):
    return '"' + (text or "").replace('"', '`"') + '"'


def _parse_agents(values):
    agents = []
    seen = set()
    for value in values or []:
        for raw in str(value).split(","):
            agent = raw.strip()
            if not agent or agent in seen:
                continue
            seen.add(agent)
            agents.append(agent)
    if not agents:
        raise ValueError("--agents must contain at least one agent")
    return agents


def _stream_packet_ready(packet):
    status = str(packet.get("status") or "").strip().lower()
    ready = str(packet.get("synthesis_ready") or "").strip().lower()
    return status == "ready-for-synthesis" or ready == "true"

def _stream_topic_slug(topic):
    slugger = getattr(stream_tool, "_slug", None)
    if slugger:
        return slugger(topic)
    return _topic_slug(topic)


def _variant_batch_payload(args):
    topic = " ".join(args.topic).strip()
    if not topic:
        raise ValueError("topic is required")
    agents = _parse_agents(args.agents)
    quorum = args.quorum or len(agents)
    if quorum < 1 or quorum > len(agents):
        raise ValueError("--quorum must be between 1 and the number of agents")

    stream_root = _resolve_repo_dir(args.stream_root) if args.stream_root else None
    root = stream_tool.streams_root(stream_root)
    topic_slug = _topic_slug(topic)
    topic_dir = os.path.join(root, topic_slug)
    batch_dir = os.path.join(topic_dir, "_batches")
    os.makedirs(batch_dir, exist_ok=True)
    batch_id = _topic_slug(args.batch_id) if args.batch_id else datetime.datetime.now().strftime("%Y%m%d-%H%M")
    manifest_path = os.path.join(batch_dir, "%s.json" % batch_id)

    existing = {}
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    packets = stream_tool.list_packets(topic_slug, ready_only=False, root=stream_root)
    by_agent = {agent: [] for agent in agents}
    ready_by_agent = {agent: [] for agent in agents}
    for packet in packets:
        agent = packet.get("agent") or "?"
        if agent not in by_agent:
            continue
        item = {
            "id": packet.get("id"),
            "status": packet.get("status"),
            "synthesis_ready": packet.get("synthesis_ready"),
            "path": _repo_rel(packet.get("path")),
        }
        by_agent[agent].append(item)
        if _stream_packet_ready(packet):
            ready_by_agent[agent].append(item)

    ready_agents = [agent for agent in agents if ready_by_agent.get(agent)]
    missing_agents = [agent for agent in agents if not ready_by_agent.get(agent)]
    ready_count = len(ready_agents)
    phase = "comparison-open" if ready_count >= quorum else "draft"

    root_suffix = ""
    if args.stream_root:
        root_suffix = " --stream-root %s" % args.stream_root
    task_suffix = ""
    if args.task:
        task_suffix = " --task %s" % args.task
    topic_arg = _ps_quote(topic)
    per_agent_commands = [
        "python tools\\top.py variant-start %s %s%s --no-preflight%s" % (agent, topic_arg, task_suffix, root_suffix)
        for agent in agents
    ]
    stream_check_cmd = "python tools\\stream.py check --max-age-days 7"
    if args.stream_root:
        stream_check_cmd += " --root %s" % args.stream_root
    barrier_commands = [
        stream_check_cmd,
        "python tools\\top.py cauldron-lanes %s --ready-only" % topic_arg,
        "python tools\\top.py synthesize-docs %s --ready-only --json" % topic_arg,
    ]

    now = datetime.datetime.now().replace(microsecond=0).isoformat()
    manifest = {
        "schema": "top_variant_batch.v1",
        "batch_id": batch_id,
        "topic": topic,
        "topic_slug": topic_slug,
        "task": args.task,
        "agents": agents,
        "quorum": quorum,
        "created": existing.get("created") or now,
        "updated": now,
        "policy": "independent-first batch barrier: agents write streams before repo-search/compare/synthesis",
        "phase": phase,
        "ready_count": ready_count,
        "missing_count": len(missing_agents),
        "ready_agents": ready_agents,
        "missing_agents": missing_agents,
        "streams_by_agent": by_agent,
        "ready_streams_by_agent": ready_by_agent,
        "per_agent_commands": per_agent_commands,
        "barrier_commands": barrier_commands,
    }
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return {
        "schema": "top_variant_batch.v1",
        "mutates": True,
        "batch_id": batch_id,
        "topic": topic,
        "topic_slug": topic_slug,
        "task": args.task,
        "manifest": {"path": manifest_path, "relpath": _repo_rel(manifest_path)},
        "phase": phase,
        "agents": agents,
        "quorum": quorum,
        "ready_count": ready_count,
        "missing_agents": missing_agents,
        "ready_agents": ready_agents,
        "per_agent_commands": per_agent_commands,
        "barrier_commands": barrier_commands,
        "policy": manifest["policy"],
    }


def cmd_variant_batch(args):
    try:
        payload = _variant_batch_payload(args)
    except Exception as exc:
        if args.json:
            print(json.dumps({"schema": "top_variant_batch.v1", "error": str(exc)}, ensure_ascii=False))
        else:
            print("ERROR: %s" % exc)
        return 1
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("# Variant batch barrier")
    print("")
    print("topic: %s" % payload["topic"])
    if payload.get("task"):
        print("task: `%s`" % payload["task"])
    print("manifest: `%s`" % payload["manifest"]["relpath"])
    print("phase: `%s`  ready: `%s/%s`  quorum: `%s`" % (
        payload["phase"], payload["ready_count"], len(payload["agents"]), payload["quorum"]))
    if payload["missing_agents"]:
        print("missing: %s" % ", ".join(payload["missing_agents"]))
    print("")
    print("## Per-agent independent draft commands")
    print("")
    print("```powershell")
    for cmd in payload["per_agent_commands"]:
        print(cmd)
    print("```")
    print("")
    print("## Barrier / comparison commands")
    print("")
    print("```powershell")
    for cmd in payload["barrier_commands"]:
        print(cmd)
    print("```")
    return 0


def cmd_draft_code(args):
    draft_args = list(args.draft_args or [])
    if not draft_args:
        draft_args = ["list"]
    cmd = _tool("draft_code.py", *draft_args)
    if "--json" in draft_args:
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=90,
                               stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
        if p.stdout:
            print(p.stdout.strip())
        if p.stderr:
            print(p.stderr.strip(), file=sys.stderr)
        return p.returncode
    return _run("draft code", cmd, timeout=90)


def cmd_info_draft(args):
    info_args = list(args.info_args or [])
    if not info_args:
        info_args = ["list"]
    cmd = _tool("info_draft.py", *info_args)
    if "--json" in info_args:
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=90,
                               stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
        if p.stdout:
            print(p.stdout.strip())
        if p.stderr:
            print(p.stderr.strip(), file=sys.stderr)
        return p.returncode
    return _run("info draft", cmd, timeout=90)


def cmd_report_diff(args):
    cmd = _tool("report_diff.py", args.a, args.b)
    if args.out:
        cmd += ["--out", args.out]
    return _run("report diff", cmd, timeout=45)

def _default_question_tree_path():
    return os.path.join("topics", "information-refactoring-question-tree-2026-06-25.md")


def _question_tree_cmd(path=None, category=None, json_output=False, limit=None, action_plan=False):
    cmd = _tool("question_tree.py", path or _default_question_tree_path())
    if category:
        cmd += ["--category", category]
    if action_plan:
        cmd.append("--action-plan")
    if json_output:
        cmd.append("--json")
    if limit is not None:
        cmd += ["--limit", str(limit)]
    return cmd


def cmd_question_tree(args):
    cmd = _question_tree_cmd(args.path, args.category, args.json, args.limit, args.action_plan)
    if args.json:
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=45)
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
        if p.stdout:
            print(p.stdout.strip())
        if p.stderr:
            print(p.stderr.strip(), file=sys.stderr)
        return p.returncode
    return _run("question tree", cmd, timeout=45)
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


def _conveyor_recover_cmd(limit=None, json_output=False):
    cmd = _tool("conveyor.py", "recover")
    if json_output:
        cmd.append("--json")
    if limit is not None:
        cmd += ["--limit", str(limit)]
    return cmd


def cmd_conveyor_recover(args):
    cmd = _conveyor_recover_cmd(limit=args.limit, json_output=args.json)
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=45)
    except subprocess.TimeoutExpired:
        payload = {"error": "timeout", "command": " ".join(cmd), "mutates": False}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print("CONVEYOR RECOVER - error")
            print("read-only: no conveyor ledger changes and no Git changes were made")
            print("error: timeout")
        return 124
    if args.json:
        if p.stdout:
            print(p.stdout.strip())
        if p.stderr:
            print(p.stderr.strip(), file=sys.stderr)
        return p.returncode
    print("CONVEYOR RECOVER - top-layer advisory")
    print("read-only: no automatic land/ship/dismiss/launch/tick and no Git changes")
    print("")
    if p.stdout:
        print(p.stdout.strip())
    if p.stderr:
        print(p.stderr.strip(), file=sys.stderr)
    return 0 if p.returncode == 0 else p.returncode

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

def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default

def _repo_path(path):
    if not path:
        return None
    if os.path.isabs(path):
        return path
    return os.path.join(ROOT, path)

def _repo_rel(path):
    if not path:
        return None
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")

def _load_pipeline_snapshot():
    data = _read_json(os.path.join(ROOT, "logs", "pipeline.json"), {})
    if not isinstance(data, dict):
        data = {}
    return {
        "epoch": data.get("epoch"),
        "doing": data.get("doing") or [],
        "ready": data.get("ready") or [],
        "blocked": data.get("blocked") or [],
    }

def _pipeline_entry_for(task_id):
    snapshot = _load_pipeline_snapshot()
    if not task_id:
        return {"state": "none", "entry": None, "snapshot_epoch": snapshot.get("epoch")}
    for state in ("doing", "ready", "blocked"):
        for item in snapshot.get(state, []):
            if item.get("id") == task_id:
                return {"state": state, "entry": item, "snapshot_epoch": snapshot.get("epoch")}
    return {"state": "none", "entry": None, "snapshot_epoch": snapshot.get("epoch")}

def _task_from_index(task_id):
    if not task_id:
        return None
    index = _read_json(os.path.join(ROOT, "index.json"), {})
    for item in index.get("tasks", []) if isinstance(index, dict) else []:
        if item.get("id") == task_id:
            return item
    return None

def _iter_thread_records():
    topics_root = os.path.join(ROOT, "topics")
    if not os.path.isdir(topics_root):
        return
    for topic in sorted(os.listdir(topics_root)):
        thread_root = os.path.join(topics_root, topic, "threads")
        if not os.path.isdir(thread_root):
            continue
        for thread_id in sorted(os.listdir(thread_root)):
            path = os.path.join(thread_root, thread_id, "THREAD.json")
            data = _read_json(path, None)
            if isinstance(data, dict):
                yield path, data

def _find_workspace_threads(ref):
    exact = []
    by_task = []
    for path, data in _iter_thread_records() or []:
        item = dict(data)
        item["path"] = _repo_rel(path)
        if data.get("id") == ref:
            exact.append(item)
        if data.get("task_id") == ref:
            by_task.append(item)
    return exact or by_task

def _path_status(path):
    full = _repo_path(path)
    return {
        "path": path,
        "exists": bool(full and os.path.exists(full)),
    }

def _git_state():
    result = {"branch": None, "dirty_count": None, "status_sample": [], "error": None}
    try:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=10)
        if branch.returncode == 0:
            result["branch"] = (branch.stdout or "").strip()
        status = subprocess.run(["git", "status", "--short", "--untracked-files=no"], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=10)
        if status.returncode == 0:
            lines = [line for line in (status.stdout or "").splitlines() if line.strip()]
            result["dirty_count"] = len(lines)
            result["status_sample"] = lines[:20]
        elif not result["error"]:
            result["error"] = (status.stderr or status.stdout or "git status failed").strip()
    except Exception as exc:
        result["error"] = str(exc)
    return result

def _workspace_cell_payload(ref):
    threads = _find_workspace_threads(ref)
    primary = threads[0] if threads else None
    task_id = (primary or {}).get("task_id") or (ref if str(ref).startswith("T-") else None)
    task = _task_from_index(task_id)
    pipeline = _pipeline_entry_for(task_id)
    outputs = []
    checks = []
    worktree = None
    stream = None
    if primary:
        outputs = [dict(item, **_path_status(item.get("path"))) for item in primary.get("outputs", [])]
        checks = primary.get("checks") or []
        if primary.get("worktree"):
            worktree = _path_status(primary.get("worktree"))
        if primary.get("stream_id"):
            stream = {"id": primary.get("stream_id")}

    blockers = []
    hard_blocked = False
    if not primary:
        blockers.append("no thread object found for %s" % ref)
    if task_id and pipeline["state"] == "blocked":
        hard_blocked = True
        blockers.append("task is blocked in pipeline snapshot")
    for item in outputs:
        if not item.get("exists"):
            hard_blocked = True
            blockers.append("output missing: %s" % item.get("path"))

    next_commands = []
    if not primary and task_id:
        topic_hint = _ascii_slug((task or {}).get("title") or task_id, fallback="task-%s" % task_id.lower())
        next_commands.append("python tools\\thread.py init %s --agent codex --mode read-only --task-id %s" % (topic_hint, task_id))
    elif primary and not outputs:
        next_commands.append("python tools\\thread.py add-output %s queues\\outbox\\<report>.md --kind report" % primary.get("id"))
    if primary:
        next_commands.append("python tools\\thread.py status %s --json" % primary.get("id"))
    next_commands.append("python tools\\validate.py")
    next_commands.append("python tools\\generate.py --check")

    if hard_blocked:
        state = "blocked"
    elif primary and outputs:
        state = "ready-for-review"
    elif primary:
        state = "open"
    elif task_id:
        state = "needs-thread"
    else:
        state = "unknown"

    return {
        "schema": "top_workspace_cell.v1",
        "id": ref,
        "state": state,
        "ref_type": "thread" if primary and primary.get("id") == ref else ("task" if task_id else "unknown"),
        "task": task or (pipeline.get("entry") if pipeline.get("entry") else None),
        "pipeline": pipeline,
        "thread": primary,
        "threads": threads,
        "stream": stream,
        "worktree": worktree,
        "outputs": outputs,
        "checks": checks,
        "git": _git_state(),
        "blockers": blockers,
        "next_commands": next_commands,
    }

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

def _ascii_slug(text, fallback="workspace-cell"):
    chars = []
    for ch in (text or fallback).lower():
        if "a" <= ch <= "z" or "0" <= ch <= "9":
            chars.append(ch)
        elif chars and chars[-1] != "-":
            chars.append("-")
    slug = "".join(chars).strip("-")
    return slug[:64] or fallback

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

def cmd_workspace_cell(args):
    payload = _workspace_cell_payload(args.ref)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print("# Workspace cell")
    print("")
    print("id: `%s`" % payload["id"])
    print("state: `%s`" % payload["state"])
    task = payload.get("task") or {}
    if task:
        print("task: `%s` %s" % (task.get("id") or "", task.get("title") or ""))
    thread = payload.get("thread") or {}
    if thread:
        print("thread: `%s`  topic: `%s`  agent: `%s`  mode: `%s`" % (
            thread.get("id"), thread.get("topic"), thread.get("agent"), thread.get("mode")))
    pipeline = payload.get("pipeline") or {}
    print("pipeline: `%s`" % pipeline.get("state"))
    if payload.get("worktree"):
        print("worktree: `%s` exists=`%s`" % (payload["worktree"].get("path"), str(payload["worktree"].get("exists")).lower()))
    if payload.get("outputs"):
        print("")
        print("## Outputs")
        for item in payload["outputs"]:
            print("- `%s` kind=`%s` exists=`%s`" % (
                item.get("path"), item.get("kind", "output"), str(item.get("exists")).lower()))
    if payload.get("checks"):
        print("")
        print("## Checks")
        for item in payload["checks"]:
            print("- %s" % item)
    if payload.get("blockers"):
        print("")
        print("## Blockers")
        for item in payload["blockers"]:
            print("- %s" % item)
    print("")
    print("## Next commands")
    print("")
    print("```powershell")
    for item in payload["next_commands"]:
        print(item)
    print("```")
    return 0

def cmd_code_activation(args):
    cmd = _tool("code_activation.py", "plan", args.target,
                "--driver-id", args.driver_id,
                "--require-confirmations", str(args.require_confirmations))
    if args.json:
        cmd.append("--json")
    if args.command:
        cmd.append("--command")
        cmd.extend(args.command)
    if args.json:
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
    return _run("code activation", cmd, timeout=45)

def cmd_stream_proxy(args):
    """Proxy commands to tools/stream.py."""
    cmd = _tool("stream.py") + args.args
    p = subprocess.run(cmd, cwd=ROOT)
    return p.returncode

def _run_doc_synthesis(label, args):
    cmd = _tool("doc_synthesis.py", "scan", args.topic, *args.files)
    if getattr(args, "out", None):
        cmd += ["--out", args.out]
    if getattr(args, "with_streams", False):
        cmd.append("--with-streams")
    if getattr(args, "ready_only", False):
        cmd.append("--ready-only")
    if getattr(args, "json", False):
        cmd.append("--json")
    if getattr(args, "json", False) and not getattr(args, "out", None) and not getattr(args, "with_streams", False):
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=90)
            if p.stdout:
                print(p.stdout.strip())
            if p.stderr:
                print(p.stderr.strip(), file=sys.stderr)
            return p.returncode
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
    return _run(label, cmd, timeout=90)


def cmd_cauldron_lanes(args):
    return _run_doc_synthesis("cauldron lanes", args)


def cmd_synthesize_docs(args):
    return _run_doc_synthesis("synthesize docs", args)


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

    p = sub.add_parser("actions", help="show queues/outbox action item status")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_actions)

    p = sub.add_parser("butterfly", help="safe cauldron graph refresh and synthesis prompt preview")
    p.add_argument("--source-dir", default=os.path.join("queues", "outbox"))
    p.add_argument("--graph", default=os.path.join("indexes", "cauldron_graph.json"))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--sample-size", type=int, default=3)
    p.add_argument("--seed")
    p.add_argument("--created-at")
    p.add_argument("--out-dir", default="topics")
    p.add_argument("--out")
    p.add_argument("--apply-graph", action="store_true")
    p.add_argument("--apply-topic", action="store_true")
    p.add_argument("--force-truncate", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_butterfly)

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

    p = sub.add_parser("variant-start", help="create an independent-first stream packet with context")
    p.add_argument("agent")
    p.add_argument("topic", nargs="+")
    p.add_argument("--task")
    p.add_argument("--reason")
    p.add_argument("--search-limit", type=int, default=5)
    p.add_argument("--stream-root", help="override streams root; must stay inside repo")
    search_group = p.add_mutually_exclusive_group()
    search_group.add_argument("--no-search", action="store_true")
    search_group.add_argument("--search-now", action="store_true", help="run repo-search after creating the stream; default defers search for independent-first")
    p.add_argument("--no-preflight", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_variant_start)
    p = sub.add_parser("variant-batch", help="create/update an independent-first batch barrier manifest")
    p.add_argument("topic", nargs="+")
    p.add_argument("--agents", nargs="+", required=True, help="comma or space separated agent ids")
    p.add_argument("--task")
    p.add_argument("--quorum", type=int)
    p.add_argument("--batch-id")
    p.add_argument("--stream-root", help="override streams root; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_variant_batch)
    p = sub.add_parser("draft-code", help="proxy to draft_code.py no-execute packet manager")
    p.add_argument("draft_args", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_draft_code)
    p = sub.add_parser("info-draft", help="proxy to info_draft.py no-canon packet manager")
    p.add_argument("info_args", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_info_draft)
    p = sub.add_parser("report-diff", help="compare two knowledge reports")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--out")
    p.set_defaults(func=cmd_report_diff)

    p = sub.add_parser("question-tree", help="inspect numbered question tree status and next actions")
    p.add_argument("path", nargs="?", default=os.path.join("topics", "information-refactoring-question-tree-2026-06-25.md"))
    p.add_argument("--category", choices=["solved", "partial", "open", "requires-decision", "unknown", "other"])
    p.add_argument("--action-plan", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--limit", type=int, default=80)
    p.set_defaults(func=cmd_question_tree)
    p = sub.add_parser("conveyor", help="show workflow conveyor supervisor status")
    p.add_argument("--target", type=int)
    p.add_argument("--idle", type=int)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_conveyor)

    p = sub.add_parser("conveyor-recover", help="show read-only workflow conveyor recovery diagnostics")
    p.add_argument("--json", action="store_true")
    p.add_argument("--limit", type=int)
    p.set_defaults(func=cmd_conveyor_recover)

    p = sub.add_parser("process-landed", help="plan intake/verify/synthesis for landed workflow outputs")
    p.add_argument("--target", type=int)
    p.add_argument("--idle", type=int)
    p.add_argument("--topic")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_process_landed)

    p = sub.add_parser("code-activation", help="read-only D-014/D-033 code activation gate card")
    p.add_argument("target")
    p.add_argument("--driver-id", default="code-activation")
    p.add_argument("--require-confirmations", type=int, default=2)
    p.add_argument("--json", action="store_true")
    p.add_argument("--command", nargs=argparse.REMAINDER, help="optional command to statically preflight; never executed")
    p.set_defaults(func=cmd_code_activation)

    p = sub.add_parser("workspace-cell", help="show read-only task/thread/worktree/outbox/checks card")
    p.add_argument("ref", help="thread id or task id")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_workspace_cell)

    p = sub.add_parser("cauldron-lanes", help="show synthesis lanes: ratify-build and divergence-detail")
    p.add_argument("topic", nargs="?", default="architecture-core")
    p.add_argument("files", nargs="*")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out")
    p.add_argument("--with-streams", action="store_true")
    p.add_argument("--ready-only", action="store_true")
    p.set_defaults(func=cmd_cauldron_lanes)

    p = sub.add_parser("synthesize-docs", help="run doc_synthesis v2 through the top layer")
    p.add_argument("topic", nargs="?", default="architecture-core")
    p.add_argument("files", nargs="*")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out")
    p.add_argument("--with-streams", action="store_true")
    p.add_argument("--ready-only", action="store_true")
    p.set_defaults(func=cmd_synthesize_docs)

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

    p = sub.add_parser("stream", help="proxy to stream.py for stream-packet lifecycle")
    p.add_argument("args", nargs="*", help="stream.py arguments")
    p.set_defaults(func=cmd_stream_proxy)

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
