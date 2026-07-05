#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.metrics
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт metrics.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Метрики / наблюдаемость канона (пункт 8 из scaling-design).

Сводка по реестрам и очереди — чтобы видеть состояние одним взглядом при многих
агентах и задачах. Читает front-matter; ничего не меняет.

    python tools/metrics.py            # человекочитаемая сводка
    python tools/metrics.py --json     # машинный вывод
"""
import os
import re
import sys
from _ioutil import configure_output
from _cli import help_guard
import json
import glob

configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

from _canon import parse_fm, missing_canon_dirs  # единые источники (T-085, находка L; P9-a волна 2)

def load(sub):
    # Контракт P9 (мягкая форма для read-only репортёра): несуществующий каталог реестра —
    # ГРОМКИЙ WARN в stderr, а не тихий 0 в счётчиках («немой ноль выглядит валидным», симптом (f)).
    if missing_canon_dirs(ROOT, (sub,)):
        print("WARN: metrics: каталог %r не найден под %s — счётчик будет 0 (P9: тихий 0 запрещён)"
              % (sub, ROOT), file=sys.stderr)
    items = []
    for path in glob.glob(os.path.join(ROOT, sub, "*.md")):
        with open(path, encoding="utf-8") as f:
            fm = parse_fm(f.read())
        if fm.get("id"):
            items.append(fm)
    return items

def by_status(items):
    c = {}
    for it in items:
        s = it.get("status", "?")
        c[s] = c.get(s, 0) + 1
    return c

def count_dir(sub, suffix=".md"):
    d = os.path.join(ROOT, sub)
    if not os.path.isdir(d):
        return 0
    return sum(1 for f in os.listdir(d) if f.endswith(suffix) and f != "README.md")

def ready_blocked(tasks):
    idx = {t["id"]: t for t in tasks}
    ready = blocked = 0
    for t in tasks:
        if t.get("status") != "todo":
            continue
        deps = re.findall(r"T-\d+", t.get("depends_on", ""))
        if all(idx.get(d, {}).get("status") == "done" for d in deps):
            ready += 1
        else:
            blocked += 1
    return ready, blocked

def build():
    tasks = load("tasks")
    questions = load("questions")
    decisions = load("decisions")
    topics = load("topics")
    ready, blocked = ready_blocked(tasks)
    return {
        "tasks": {"total": len(tasks), "by_status": by_status(tasks),
                  "ready": ready, "blocked": blocked},
        "questions": {"total": len(questions), "by_status": by_status(questions)},
        "decisions": {"total": len(decisions), "by_status": by_status(decisions)},
        "topics": {"total": len(topics), "by_status": by_status(topics)},
        "queue": {"inbox": count_dir("queues/inbox"),
                  "claimed": count_dir("queues/claimed", ".claim.md"),
                  "done": count_dir("queues/done", ".done.md"),
                  "failed": count_dir("queues/failed", ".failed.md")},
    }

def main():
    help_guard(__doc__)
    m = build()
    if "--json" in sys.argv[1:]:
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return 0

    def fmt(d):
        return ", ".join("%s=%d" % (k, v) for k, v in sorted(d.items())) or "—"

    print("=== Метрики канона ===")
    print("Задачи:   %d (%s) | готовы=%d, заблокированы=%d"
          % (m["tasks"]["total"], fmt(m["tasks"]["by_status"]),
             m["tasks"]["ready"], m["tasks"]["blocked"]))
    print("Вопросы:  %d (%s)" % (m["questions"]["total"], fmt(m["questions"]["by_status"])))
    print("Решения:  %d (%s)" % (m["decisions"]["total"], fmt(m["decisions"]["by_status"])))
    print("Темы:     %d (%s)" % (m["topics"]["total"], fmt(m["topics"]["by_status"])))
    print("Очередь:  inbox=%d, claimed=%d, done=%d, failed=%d"
          % (m["queue"]["inbox"], m["queue"]["claimed"],
             m["queue"]["done"], m["queue"]["failed"]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
