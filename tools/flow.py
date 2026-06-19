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

Пример: python tools/flow.py start mavis T-020 --run
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


def main():
    args = [a for a in sys.argv[1:] if a != "--run"]
    do_run = "--run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    if cmd == "start" and len(args) >= 3:
        b = branch_name(args[1], args[2])
        return run_or_print([["git", "checkout", "-b", b]], do_run)
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
