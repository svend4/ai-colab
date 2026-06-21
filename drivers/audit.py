#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Канонический аудит-хелпер для драйверов (слой безопасности).

Драйверы с `risk: medium|high` обязаны логировать вызовы
(`docs/driver-safety-policy.md`). Лёгкий append-only JSONL-журнал — один общий
механизм вместо точечных решений и без жёсткой связки каждого драйвера с
`workbench.db` (ревью T-078, находка E).

Путь журнала: env `DRIVER_AUDIT_LOG`, иначе `<repo-root>/logs/driver-audit.jsonl`.
Запись одной строки атомарна на уровне ОС (один `write` в режиме append).
Аудит никогда не бросает наружу: сбой журнала не должен ломать read-only вызов.

CLI:
    python audit.py tail [N]   # показать последние N записей журнала
"""
import os
import sys
import json
import time

_DEFAULT_REL = os.path.join("logs", "driver-audit.jsonl")


def log_path():
    env = os.environ.get("DRIVER_AUDIT_LOG")
    if env:
        return env
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # drivers/.. = repo-root
    return os.path.join(root, _DEFAULT_REL)


def audit(driver, action, target=None, **extra):
    """Записать одну строку аудита вызова драйвера. Возвращает записанную запись."""
    rec = {"ts": int(time.time()), "driver": driver, "action": action, "target": target}
    if extra:
        rec.update(extra)
    try:
        path = log_path()
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:  # аудит не должен ронять драйвер
        print("WARN: audit write failed: %s" % exc, file=sys.stderr)
    return rec


def _tail(n=20):
    path = log_path()
    if not os.path.exists(path):
        print("(пусто) %s" % path)
        return 0
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[-n:]:
        print(line.rstrip())
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "tail":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        sys.exit(_tail(n))
    print(__doc__)
    sys.exit(2)
