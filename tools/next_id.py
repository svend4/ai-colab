#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.next_id
# TYPE: active-script
# DOMAIN: core.coordination
# DEPTH_LEVEL: 1
# SUMMARY: Атомарно выдаёт Q/T/D id и защищает заполнение placeholder через reservation_token.
# ==========================================
"""
Атомарная выдача id (T-/Q-/D-) — чтобы агенты не занимали один номер дважды.

    python tools/next_id.py question [--agent NAME]
    python tools/next_id.py task     [--agent NAME]
    python tools/next_id.py decision [--agent NAME]
    python tools/next_id.py check <T-123|path> --agent NAME --token TOKEN
    python tools/next_id.py fill  <T-123|path> --agent NAME --token TOKEN --from FILE

Сканирует каталог, берёт max+1 и АТОМАРНО создаёт файл-заглушку через
os.O_CREAT|O_EXCL (как claim в queue.py). Если номер перехватил другой агент —
берёт следующий свободный. Печатает выданный id, путь и reservation_token.

Заглушка валидна для validate.py (есть id/title/status), но помечена
«(зарезервировано)». Для параллельного режима она также содержит
reservation_token. Перед заполнением корректный агент должен проверить токен
или использовать `fill`, чтобы не перезаписать чужой свежий резерв.
"""
import datetime
import os
import re
import sys
import time
import uuid

from _canon import parse_front_matter
from _ioutil import configure_output


configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
TODAY = datetime.date.today().isoformat()

TYPES = {"question": ("questions", "Q"), "task": ("tasks", "T"), "decision": ("decisions", "D")}
ALIASES = {"q": "question", "t": "task", "d": "decision"}
BY_PREFIX = {prefix: (kind, subdir) for kind, (subdir, prefix) in TYPES.items()}


def reservation_fields(agent, token):
    return (
        "reserved_by: %s\n"
        "reserved_epoch: %d\n"
        "reservation_token: %s\n"
        % (agent, int(time.time()), token)
    )


def stub(kind, ident, agent, token):
    reservation = reservation_fields(agent, token)
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
            "%s"
            "---\n\n"
            "# %s — зарезервировано\n\n"
            "id выдан атомарно (`tools/next_id.py`). Заполните по D-004: варианты → плюсы/минусы → рекомендация.\n"
            % (ident, agent, reservation, ident)
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
            "%s"
            "---\n\n"
            "# %s — зарезервировано\n"
            % (ident, agent, reservation, ident)
        )
    return (
        "---\n"
        "id: %s\n"
        "type: decision\n"
        "title: (зарезервировано — заполните)\n"
        "status: proposed\n"
        "date: %s\n"
        "%s"
        "---\n\n"
        "# %s — зарезервировано\n"
        % (ident, TODAY, reservation, ident)
    )


def existing_max(dirpath, prefix):
    mx = 0
    if os.path.isdir(dirpath):
        for fn in os.listdir(dirpath):
            m = re.match(r"^%s-(\d+)\.md$" % prefix, fn)
            if m:
                mx = max(mx, int(m.group(1)))
    return mx


def flag(name, default=""):
    for i, arg in enumerate(sys.argv):
        if arg == name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def resolve_target(target):
    target = (target or "").strip().strip('"')
    if not target:
        raise ValueError("target is required")
    norm = target.replace("\\", "/")
    if norm.endswith(".md"):
        path = target if os.path.isabs(target) else os.path.join(ROOT, norm.replace("/", os.sep))
    else:
        m = re.match(r"^([TQD])-\d{3,}$", target.upper())
        if not m:
            raise ValueError("target must be T-123/Q-123/D-123 or a .md path")
        _, subdir = BY_PREFIX[m.group(1)]
        path = os.path.join(ROOT, subdir, target.upper() + ".md")
    root_abs = os.path.abspath(ROOT)
    path_abs = os.path.abspath(path)
    if not (path_abs == root_abs or path_abs.startswith(root_abs + os.sep)):
        raise ValueError("target must stay inside COLLAB_ROOT")
    return path_abs


def read_fm(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as exc:
        raise ValueError("cannot read target: %s" % exc)
    fm = parse_front_matter(text)
    if not fm:
        raise ValueError("target has no front-matter")
    return fm, text


def check_reservation(path, agent, token):
    fm, _ = read_fm(path)
    missing = []
    if not agent:
        missing.append("--agent")
    if not token:
        missing.append("--token")
    if missing:
        return 2, "missing %s" % ", ".join(missing)
    if fm.get("reserved_by") != agent:
        return 1, "reserved_by mismatch: expected %s, got %s" % (agent, fm.get("reserved_by", ""))
    if fm.get("reservation_token") != token:
        return 1, "reservation_token mismatch"
    return 0, "OK reservation %s for %s" % (fm.get("id", os.path.basename(path)), agent)


def cmd_check(pos):
    if len(pos) < 2:
        print("Использование: python tools/next_id.py check <T-id|path> --agent NAME --token TOKEN")
        return 2
    try:
        path = resolve_target(pos[1])
        rc, msg = check_reservation(path, flag("--agent"), flag("--token"))
    except ValueError as exc:
        print("ОШИБКА: %s" % exc)
        return 2
    print(msg)
    return rc


def cmd_fill(pos):
    if len(pos) < 2:
        print("Использование: python tools/next_id.py fill <T-id|path> --agent NAME --token TOKEN --from FILE")
        return 2
    source = flag("--from")
    if not source:
        print("ОШИБКА: нужен --from FILE")
        return 2
    try:
        path = resolve_target(pos[1])
        rc, msg = check_reservation(path, flag("--agent"), flag("--token"))
        if rc:
            print("ОШИБКА: %s" % msg)
            return rc
        fm, _ = read_fm(path)
        source_path = source if os.path.isabs(source) else os.path.join(ROOT, source)
        with open(source_path, encoding="utf-8", errors="replace") as f:
            new_text = f.read()
        new_fm = parse_front_matter(new_text)
        if new_fm.get("id") != fm.get("id"):
            print("ОШИБКА: id в --from (%s) не совпадает с резервом (%s)" % (new_fm.get("id"), fm.get("id")))
            return 1
        tmp = path + ".tmp." + flag("--token")
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_text)
        os.replace(tmp, path)
    except OSError as exc:
        print("ОШИБКА: %s" % exc)
        return 1
    except ValueError as exc:
        print("ОШИБКА: %s" % exc)
        return 2
    print("FILLED: %s" % os.path.relpath(path, ROOT).replace("\\", "/"))
    return 0


def cmd_issue(kind, agent):
    subdir, prefix = TYPES[kind]
    dirpath = os.path.join(ROOT, subdir)
    os.makedirs(dirpath, exist_ok=True)

    n = existing_max(dirpath, prefix) + 1
    for _ in range(1000):
        ident = "%s-%03d" % (prefix, n)
        path = os.path.join(dirpath, ident + ".md")
        token = uuid.uuid4().hex[:12]
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            n += 1
            continue
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(stub(kind, ident, agent, token))
        print("Выдан id: %s" % ident)
        print("Файл: %s/%s.md — заполните и закоммитьте" % (subdir, ident))
        print("reservation_token: %s" % token)
        print("Перед заполнением: python tools/next_id.py check %s --agent %s --token %s" % (ident, agent, token))
        return 0
    print("Не удалось выдать свободный id за 1000 попыток")
    return 1


def main():
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not pos:
        print("Использование: python tools/next_id.py question|task|decision [--agent NAME]")
        return 2
    if pos[0].lower() == "check":
        return cmd_check(pos)
    if pos[0].lower() == "fill":
        return cmd_fill(pos)

    kind = ALIASES.get(pos[0].lower(), pos[0].lower())
    if kind not in TYPES:
        print("Неизвестный тип: %s (нужно question|task|decision)" % pos[0])
        return 2
    return cmd_issue(kind, flag("--agent", "unknown"))


if __name__ == "__main__":
    sys.exit(main())