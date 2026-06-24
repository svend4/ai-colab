#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.worktree
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт worktree.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
worktree (Уровень-1 политики коммитов, T-136 — принят Stefan 2026-06-21) — git-worktree на агента.

Завершает набор Уровня-1: `stream.py` (пакеты-форки) + `merge_gate.py` (гейт) + `worktree.py`
(изоляция исполнения). Каждый агент работает в СВОЁМ рабочем каталоге на ветке `agent/<agent>/<task>`,
поэтому `git add -A` видит только его работу, а `index.lock` не пересекается — «маленький ручеёк»,
впадающий в основную линию через merge-gate.

Безопасно по умолчанию: команды только ПЕЧАТАЮТСЯ, пока не передан `--run` (как `flow.py`).

    python tools/worktree.py spawn  <agent> <task> [--run]   # создать worktree + ветку
    python tools/worktree.py list                            # активные worktree
    python tools/worktree.py remove <agent> <task> [--run]   # снять worktree + удалить ветку

Каталог притока — рядом с репозиторием: `<parent>/<repo>-wt-<agent>-<task>` (не вложен в репо).
Слияние притока в основную линию — через `tools/merge_gate.py` (зелёный гейт), затем `git merge`.
"""
import os
import sys
from _ioutil import configure_output
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

configure_output()

def branch_name(agent, task):
    return "agent/%s/%s" % (agent, task)

def worktree_path(agent, task, root=ROOT):
    """Каталог притока — сосед репозитория (git worktree нельзя вкладывать в тот же репо)."""
    parent = os.path.dirname(os.path.abspath(root))
    return os.path.join(parent, "%s-wt-%s-%s" % (os.path.basename(os.path.abspath(root)), agent, task))

def spawn_cmds(agent, task, root=ROOT):
    return [["git", "worktree", "add", "-b", branch_name(agent, task),
             worktree_path(agent, task, root)]]

def remove_cmds(agent, task, root=ROOT):
    return [["git", "worktree", "remove", worktree_path(agent, task, root)],
            ["git", "branch", "-D", branch_name(agent, task)]]

def list_cmds():
    return [["git", "worktree", "list"]]

def run_or_print(cmds, do_run, cwd=ROOT):
    for cmd in cmds:
        print("$ " + " ".join(cmd))
    if not do_run:
        print("(печать; добавь --run, чтобы выполнить)")
        return 0
    for cmd in cmds:
        rc = subprocess.call(cmd, cwd=cwd, stdin=subprocess.DEVNULL)
        if rc != 0:
            print("Команда завершилась с кодом %d — остановка." % rc)
            return rc
    return 0

def main():
    args = [a for a in sys.argv[1:] if a != "--run"]
    do_run = "--run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    if cmd == "spawn" and len(args) >= 3:
        print("Приток для %s/%s -> %s" % (args[1], args[2], worktree_path(args[1], args[2])))
        rc = run_or_print(spawn_cmds(args[1], args[2]), do_run)
        if do_run and rc == 0:
            print("Работай в каталоге выше; слияние — через merge_gate + git merge.")
        return rc
    if cmd == "list":
        return run_or_print(list_cmds(), True)  # read-only, всегда выполняем
    if cmd == "remove" and len(args) >= 3:
        return run_or_print(remove_cmds(args[1], args[2]), do_run)
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main())
