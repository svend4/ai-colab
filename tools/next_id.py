#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Атомарная выдача id (T-/Q-/D-) — чтобы агенты не занимали один номер дважды.

    python tools/next_id.py question [--agent NAME]
    python tools/next_id.py task     [--agent NAME]
    python tools/next_id.py decision [--agent NAME]

Сканирует каталог, берёт max+1 и АТОМАРНО создаёт файл-заглушку через
os.O_CREAT|O_EXCL (как claim в queue.py). Если номер перехватил другой агент —
берёт следующий свободный. Печатает выданный id и путь; агент сразу заполняет файл.

Заглушка валидна для validate.py (есть id/title/status), но помечена
«(зарезервировано)» — заполните её до коммита.
"""
import os
import re
import sys
import datetime


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
TODAY = datetime.date.today().isoformat()

TYPES = {"question": ("questions", "Q"), "task": ("tasks", "T"), "decision": ("decisions", "D")}
ALIASES = {"q": "question", "t": "task", "d": "decision"}


def stub(kind, ident, agent):
    if kind == "question":
        return (
            "---\n"
            "id: %s\n"
            "type: question\n"
            "title: (зарезервировано — заполните)\n"
            "status: open\n"
            "asked_by: %s\n"
            "addressed_to: все\n"
            "where: dialog.md\n"
            "outcome:\n"
            "---\n\n"
            "# %s — зарезервировано\n\n"
            "id выдан атомарно (`tools/next_id.py`). Заполните по D-004: варианты → плюсы/минусы → рекомендация.\n"
            % (ident, agent, ident)
        )
    if kind == "task":
        return (
            "---\n"
            "id: %s\n"
            "type: task\n"
            "title: (зарезервировано — заполните)\n"
            "status: todo\n"
            "owner: %s\n"
            "priority: normal\n"
            "risk: low\n"
            "depends_on: []\n"
            "next: зарезервировано через tools/next_id.py — заполните\n"
            "---\n\n"
            "# %s — зарезервировано\n"
            % (ident, agent, ident)
        )
    return (
        "---\n"
        "id: %s\n"
        "type: decision\n"
        "title: (зарезервировано — заполните)\n"
        "status: proposed\n"
        "date: %s\n"
        "---\n\n"
        "# %s — зарезервировано\n"
        % (ident, TODAY, ident)
    )


def existing_max(dirpath, prefix):
    mx = 0
    if os.path.isdir(dirpath):
        for fn in os.listdir(dirpath):
            m = re.match(r"^%s-(\d+)\.md$" % prefix, fn)
            if m:
                mx = max(mx, int(m.group(1)))
    return mx


def main():
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not pos:
        print("Использование: python tools/next_id.py question|task|decision [--agent NAME]")
        return 2
    kind = ALIASES.get(pos[0].lower(), pos[0].lower())
    if kind not in TYPES:
        print("Неизвестный тип: %s (нужно question|task|decision)" % pos[0])
        return 2

    agent = "unknown"
    for i, a in enumerate(sys.argv):
        if a == "--agent" and i + 1 < len(sys.argv):
            agent = sys.argv[i + 1]

    subdir, prefix = TYPES[kind]
    dirpath = os.path.join(ROOT, subdir)
    os.makedirs(dirpath, exist_ok=True)

    n = existing_max(dirpath, prefix) + 1
    for _ in range(1000):
        ident = "%s-%03d" % (prefix, n)
        path = os.path.join(dirpath, ident + ".md")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            n += 1
            continue
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(stub(kind, ident, agent))
        print("Выдан id: %s" % ident)
        print("Файл: %s/%s.md — заполните и закоммитьте" % (subdir, ident))
        return 0
    print("Не удалось выдать свободный id за 1000 попыток")
    return 1


if __name__ == "__main__":
    sys.exit(main())
