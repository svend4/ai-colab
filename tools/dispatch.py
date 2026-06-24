#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.dispatch
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт dispatch.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Диспетчер задач по DAG зависимостей (Этап D из scaling-design).

Задача «готова», если её status=todo и все её depends_on имеют status=done.
Помогает многим агентам не толкаться: каждый видит, что можно брать, и что
заблокировано и чем.

    python tools/dispatch.py          # список готовых и заблокированных задач
    python tools/dispatch.py next     # id одной задачи с наивысшим приоритетом (для скриптов)

Не меняет файлы. Захват — через queue.py; статусы — в tasks/*.md.
"""
import os
import re
import sys
from _ioutil import configure_output
import glob

configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
PRIO = {"high": 0, "normal": 1, "low": 2, "": 3}

from _canon import parse_fm  # единый парсер front-matter (T-085, находка L)

def load_tasks():
    tasks = {}
    for path in glob.glob(os.path.join(ROOT, "tasks", "*.md")):
        with open(path, encoding="utf-8") as f:
            fm = parse_fm(f.read())
        tid = fm.get("id")
        if not tid:
            continue
        tasks[tid] = {
            "id": tid,
            "title": fm.get("title", ""),
            "status": fm.get("status", "todo"),
            "priority": fm.get("priority", ""),
            "deps": re.findall(r"T-\d+", fm.get("depends_on", "")),
        }
    return tasks

def main():
    tasks = load_tasks()
    ready, blocked = [], []
    for t in tasks.values():
        if t["status"] != "todo":
            continue
        unmet = [d for d in t["deps"] if tasks.get(d, {}).get("status") != "done"]
        (blocked if unmet else ready).append((t, unmet))
    ready.sort(key=lambda x: (PRIO.get(x[0]["priority"], 3), x[0]["id"]))
    blocked.sort(key=lambda x: x[0]["id"])

    if "next" in sys.argv[1:]:
        print(ready[0][0]["id"] if ready else "")
        return 0

    print("ГОТОВЫ (можно брать), %d:" % len(ready))
    for t, _ in ready:
        print("  [%s] %s — %s" % (t["priority"] or "—", t["id"], t["title"]))
    print("ЗАБЛОКИРОВАНЫ, %d:" % len(blocked))
    for t, unmet in blocked:
        print("  [%s] %s — ждёт: %s" % (t["priority"] or "—", t["id"], ", ".join(unmet)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
