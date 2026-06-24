#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.flow
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт flow.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Git-flow для агентов (Этап F из scaling-design): ветка-на-агента + merge через гейт.

Модель: каждый агент работает в своей ветке `agent/<agent>/<task>`, чтобы не
толкаться в одной ветке на «горячих» файлах. Перед merge — гейт (validate +
generate --check + permissions). Merge делает человек или maintainer-агент.

По умолчанию команды только ПЕЧАТАЮТСЯ (безопасно). С флагом --run — выполняются.

    python tools/flow.py start  <agent> <task>   # создать ветку agent/<agent>/<task>
    python tools/flow.py gate   <agent>          # прогнать гейт перед merge
    python tools/flow.py finish <agent> <task>   # merge ветки в master (после зелёного гейта)
    python tools/flow.py launch-plan <agent> <task> [context...] [--worktree] [--json]
                                                # prompt/commands для внешнего sub-agent launcher

Уровень-1 (worktree-на-агента, принят Stefan 2026-06-21): добавь `--worktree`, тогда `start`
создаёт изолированный приток (через `worktree.py`), а `finish` гейтит `merge_gate` → merge → снимает
приток. Без `--worktree` поведение прежнее (ветка в общем рабочем дереве).

Пример: python tools/flow.py start mavis T-020 --worktree --run
Пример launch-plan: python tools/flow.py launch-plan mavis T-160 repo search onboarding --worktree
Пример JSON: python tools/flow.py launch-plan mavis T-160 repo search onboarding --worktree --json
"""
import sys
import json
import subprocess

from _ioutil import configure_output

configure_output()


def branch_name(agent, task):
    return "agent/%s/%s" % (agent, task)


def run_or_print(cmds, do_run):
    for cmd in cmds:
        print("$ " + " ".join(cmd))
    if not do_run:
        print("(печать; добавь --run, чтобы выполнить)")
        return 0
    for cmd in cmds:
        rc = subprocess.call(cmd)
        if rc != 0:
            print("Команда завершилась с кодом %d — остановка." % rc)
            return rc
    return 0

def _cmd_parts(action, agent, task, use_worktree=False):
    parts = ["python", "tools/flow.py", action, agent, task]
    if use_worktree:
        parts.append("--worktree")
    return parts


def _cmd_text(parts):
    return " ".join(parts)


def launch_plan_data(agent, task, context, use_worktree=False):
    """Машиночитаемый контракт handoff для внешнего sub-agent launcher."""
    context = (context or task).strip()
    quoted_context = context.replace('"', "'")
    prepare = _cmd_parts("start", agent, task, use_worktree)
    finish = _cmd_parts("finish", agent, task, use_worktree)
    worker_prompt_lines = [
        "You are worker agent `%s` in the shared repository." % agent,
        "You are not alone in the codebase: do not revert or overwrite changes made by other agents.",
        "Task: `%s`." % task,
        "Start by running: python tools/top.py agent-start %s --context \"%s\"" % (agent, quoted_context),
        "Claim or confirm the task with: python tools/pipeline.py claim %s %s" % (agent, task),
        "Use the existing repo policies: AGENTS.md, PROTOCOL.md, D-022/D-023, and docs/parallel-work-policy.md.",
        "Keep edits scoped to the task, run focused tests plus python tools/top.py health, and finish with:",
        "python tools/pipeline.py done %s %s --claim <claim_id> --report \"...\" --applied \"AGENTS.md, PROTOCOL.md, docs/agent-launch-workflow.md, Checks\"" % (agent, task),
        "Final reply must list changed files, tests run, and any blockers.",
    ]
    return {
        "schema": "subagent_launch_plan.v1",
        "agent": agent,
        "task": task,
        "context": context,
        "repo_lane": {
            "mode": "worktree" if use_worktree else "branch",
            "label": "Level 1 worktree" if use_worktree else "Level 0 branch",
        },
        "boundary": [
            "flow.py prepares git branch/worktree and merge-gate commands.",
            "External platform sub-agent launcher starts the AI worker with the prompt.",
            "The worker must not revert other agents' work and must report changed files/tests.",
        ],
        "commands": {
            "prepare": prepare,
            "prepare_text": _cmd_text(prepare),
            "finish": finish,
            "finish_text": _cmd_text(finish),
        },
        "worker_prompt_lines": worker_prompt_lines,
        "worker_prompt": "\n".join(worker_prompt_lines),
        "policies": [
            "AGENTS.md",
            "PROTOCOL.md",
            "D-022",
            "D-023",
            "docs/parallel-work-policy.md",
            "docs/agent-launch-workflow.md",
        ],
        "checks": [
            "python tools/top.py health",
            "focused tests for changed tools/docs",
            "python tools/pipeline.py done <agent> <task> --claim <claim_id> --applied ...",
        ],
    }


def launch_plan(agent, task, context, use_worktree=False, as_json=False):
    """План запуска внешнего sub-agent поверх repo flow."""
    data = launch_plan_data(agent, task, context, use_worktree)
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print("# Sub-agent launch plan")
    print("")
    print("agent: `%s`" % data["agent"])
    print("task: `%s`" % data["task"])
    print("context: `%s`" % data["context"])
    print("repo lane: `%s`" % data["repo_lane"]["label"])
    print("")
    print("## Boundary")
    print("")
    for item in data["boundary"]:
        print("- %s" % item)
    print("")
    print("## 1. Prepare repo lane")
    print("")
    print("```powershell")
    print(data["commands"]["prepare_text"])
    print("# add --run only after reviewing the printed command and current git status")
    print("```")
    print("")
    print("## 2. External sub-agent prompt")
    print("")
    print("```text")
    print(data["worker_prompt"])
    print("```")
    print("")
    print("## 3. Finish repo lane")
    print("")
    print("```powershell")
    print(data["commands"]["finish_text"])
    print("# add --run only after worker commit/review and green merge_gate")
    print("```")
    return 0
def main():
    flags = {"--run", "--worktree", "--json"}
    args = [a for a in sys.argv[1:] if a not in flags]
    do_run = "--run" in sys.argv
    use_worktree = "--worktree" in sys.argv
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    if cmd == "start" and len(args) >= 3:
        if use_worktree:  # Уровень-1: изолированный приток вместо ветки в общем дереве
            import worktree as wt
            return wt.run_or_print(wt.spawn_cmds(args[1], args[2]), do_run)
        b = branch_name(args[1], args[2])
        return run_or_print([["git", "checkout", "-b", b]], do_run)
    if cmd == "launch-plan" and len(args) >= 3:
        return launch_plan(args[1], args[2], " ".join(args[3:]), use_worktree, as_json=as_json)
    if cmd == "gate" and len(args) >= 2:
        agent = args[1]
        return run_or_print(
            [
                [sys.executable, "tools/validate.py"],
                [sys.executable, "tools/generate.py", "--check"],
                [sys.executable, "tools/permissions.py", agent],
            ],
            do_run,
        )
    if cmd == "finish" and len(args) >= 3:
        b = branch_name(args[1], args[2])
        if use_worktree:  # Уровень-1: регенерация -> гейт -> merge -> РЕГЕН-НА-MERGED -> verify -> снять приток
            import worktree as wt
            # generate.py перед гейтом сглаживает merge-back wall: чужая незакоммиченная задача делает
            # общий индекс STALE → merge_gate RED. Регенерируем индексы (не-staged) — merge приносит
            # только ветку, индексы оставляем владельцу источников.
            # Остаточная гонка (была flow.py:141): чужой коммит мог приземлиться МЕЖДУ пред-merge гейтом и
            # самим merge → слитый HEAD снова STALE, хотя гейт был зелёным. Закрываем: после merge
            # РЕГЕНЕРИРУЕМ индексы НА УЖЕ-СЛИТОМ коммите и amend'им их в merge-commit (changeset
            # самосогласован), затем повторный merge_gate подтверждает green-после-merge. Если повторный
            # гейт КРАСНЫЙ — run_or_print останавливается с nonzero ДО снятия притока (приток цел для retry).
            cmds = [[sys.executable, "tools/generate.py"],
                    [sys.executable, "tools/merge_gate.py", "check", args[1]],
                    ["git", "merge", "--no-ff", b, "-m", "Merge %s" % b],
                    [sys.executable, "tools/generate.py"],
                    ["git", "add",
                     "TASKS.md", "QUESTIONS.md", "DECISIONS.md", "board.md", "STATUS.md", "index.json"],
                    ["git", "commit", "--amend", "--no-edit"],
                    [sys.executable, "tools/merge_gate.py", "check", args[1]]]
            cmds += wt.remove_cmds(args[1], args[2])
            return run_or_print(cmds, do_run)
        return run_or_print(
            [
                ["git", "checkout", "master"],
                ["git", "merge", "--no-ff", b, "-m", "Merge %s" % b],
            ],
            do_run,
        )
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
