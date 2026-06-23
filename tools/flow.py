#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git-flow для агентов (Этап F из scaling-design): ветка-на-агента + merge через гейт.

Модель: каждый агент работает в своей ветке `agent/<agent>/<task>`, чтобы не
толкаться в одной ветке на «горячих» файлах. Перед merge — гейт (validate +
generate --check + permissions). Merge делает человек или maintainer-агент.

По умолчанию команды только ПЕЧАТАЮТСЯ (безопасно). С флагом --run — выполняются.

    python tools/flow.py start  <agent> <task>   # создать ветку agent/<agent>/<task>
    python tools/flow.py gate   <agent>          # прогнать гейт перед merge
    python tools/flow.py finish <agent> <task>   # merge ветки в master (после зелёного гейта)
    python tools/flow.py launch-plan <agent> <task> [context...] [--worktree]
                                                # prompt/commands для внешнего sub-agent launcher

Уровень-1 (worktree-на-агента, принят Stefan 2026-06-21): добавь `--worktree`, тогда `start`
создаёт изолированный приток (через `worktree.py`), а `finish` гейтит `merge_gate` → merge → снимает
приток. Без `--worktree` поведение прежнее (ветка в общем рабочем дереве).

Пример: python tools/flow.py start mavis T-020 --worktree --run
Пример launch-plan: python tools/flow.py launch-plan mavis T-160 repo search onboarding --worktree
"""
import sys
import subprocess


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


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

def launch_plan(agent, task, context, use_worktree=False):
    """План запуска внешнего sub-agent поверх repo flow.

    Локальный flow.py не может вызвать платформенный spawn_agent сам. Он готовит
    воспроизводимый lane: branch/worktree, prompt для worker'а и finish-команду.
    """
    context = (context or task).strip()
    mode = " --worktree" if use_worktree else ""
    quoted_context = context.replace('"', "'")
    print("# Sub-agent launch plan")
    print("")
    print("agent: `%s`" % agent)
    print("task: `%s`" % task)
    print("context: `%s`" % context)
    print("repo lane: `%s`" % ("Level 1 worktree" if use_worktree else "Level 0 branch"))
    print("")
    print("## Boundary")
    print("")
    print("- `flow.py` prepares git branch/worktree and merge-gate commands.")
    print("- External platform sub-agent launcher starts the AI worker with the prompt below.")
    print("- The worker must not revert other agents' work and must report changed files/tests.")
    print("")
    print("## 1. Prepare repo lane")
    print("")
    print("```powershell")
    print("python tools/flow.py start %s %s%s" % (agent, task, mode))
    print("# add --run only after reviewing the printed command and current git status")
    print("```")
    print("")
    print("## 2. External sub-agent prompt")
    print("")
    print("```text")
    print("You are worker agent `%s` in the shared repository." % agent)
    print("You are not alone in the codebase: do not revert or overwrite changes made by other agents.")
    print("Task: `%s`." % task)
    print("Start by running: python tools/top.py agent-start %s --context \"%s\"" % (agent, quoted_context))
    print("Claim or confirm the task with: python tools/pipeline.py claim %s %s" % (agent, task))
    print("Use the existing repo policies: AGENTS.md, PROTOCOL.md, D-022/D-023, and docs/parallel-work-policy.md.")
    print("Keep edits scoped to the task, run focused tests plus python tools/top.py health, and finish with:")
    print("python tools/pipeline.py done %s %s --claim <claim_id> --report \"...\" --applied \"AGENTS.md, PROTOCOL.md, docs/agent-launch-workflow.md, Checks\"" % (agent, task))
    print("Final reply must list changed files, tests run, and any blockers.")
    print("```")
    print("")
    print("## 3. Finish repo lane")
    print("")
    print("```powershell")
    print("python tools/flow.py finish %s %s%s" % (agent, task, mode))
    print("# add --run only after worker commit/review and green merge_gate")
    print("```")
    return 0


def main():
    flags = {"--run", "--worktree"}
    args = [a for a in sys.argv[1:] if a not in flags]
    do_run = "--run" in sys.argv
    use_worktree = "--worktree" in sys.argv
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
        return launch_plan(args[1], args[2], " ".join(args[3:]), use_worktree)
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
        if use_worktree:  # Уровень-1: регенерация (снять чужой generate-stale) -> гейт -> merge -> снять приток
            import worktree as wt
            # generate.py перед гейтом сглаживает merge-back wall: чужая незакоммиченная задача делает
            # общий индекс STALE → merge_gate RED. Регенерируем индексы (не-staged) — merge приносит
            # только ветку, индексы оставляем владельцу источников. (Узкая гонка остаётся — retry.)
            cmds = [[sys.executable, "tools/generate.py"],
                    [sys.executable, "tools/merge_gate.py", "check", args[1]],
                    ["git", "merge", "--no-ff", b, "-m", "Merge %s" % b]] + wt.remove_cmds(args[1], args[2])
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
