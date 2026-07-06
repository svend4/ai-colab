#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.permissions
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт permissions.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Проверка прав агента на изменённые файлы (роли, Этап E из scaling-design).

Совещательный guard для кооперативных агентов: ловит ошибку, когда агент пишет
вне своей разрешённой зоны. Это не безопасность (агент объявляет себя сам), а
защита от случайных правок не туда.

Политика: `tools/permissions.json` — {agent: [glob, ...]}.
Глоб: "**" = всё; "dir/**" = всё внутри dir/; "*.md" = любой .md; иначе точный путь.

Служебные ключи политики (начинаются с "_", агентами не являются):
- "_deny_agents": [glob, ...] — критические пути, закрытые для ЛЮБОГО агента
  (в т.ч. с зоной "**"); проверяются ПЕРВЫМИ, совпадение → ВНЕ ЗОНЫ / exit 1.
  Только человек правит эти пути (решение Stefan 2026-07-06, закрывает gate-10/C31).
- "_comment" — пояснение для людей, игнорируется.

Запуск:
    python tools/permissions.py <agent>                  # проверить git-изменения (vs HEAD + новые)
    python tools/permissions.py <agent> file1 file2 ...  # проверить переданные пути (тест/CI)

Выход: 0 — нет нарушений; 1 — есть.
"""
import os
import sys
from _ioutil import configure_output
from _cli import help_guard
import json
import subprocess

configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

def load_policy():
    path = os.path.join(ROOT, "tools", "permissions.json")
    if not os.path.exists(path):
        print("ERROR: нет tools/permissions.json")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def match(path, pattern):
    path = path.replace("\\", "/")
    if pattern == "**":
        return True
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])  # "dir/**" → "dir/"
    if pattern.startswith("*."):
        return path.endswith(pattern[1:])  # "*.md" → ".md"
    return path == pattern

def denied(path, deny_globs):
    """Критические пути из "_deny_agents": закрыты для любого агента, только человек.

    Переиспользует match() — та же семантика глобов, что и у зон агентов
    (решение Stefan 2026-07-06, закрывает gate-10/C31)."""
    return any(match(path, g) for g in deny_globs)

def git_changes():
    files = set()
    for cmd in (
        ["git", "-C", ROOT, "-c", "core.quotepath=false", "diff", "--name-only", "HEAD"],
        ["git", "-C", ROOT, "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"],
    ):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            files.update(l.strip() for l in out.decode("utf-8", "replace").splitlines() if l.strip())
        except Exception as e:
            print("ERROR: git недоступен (%s) — передай файлы аргументами" % e)
            return None
    return sorted(files)

def main():
    help_guard(__doc__)
    args = sys.argv[1:]
    if not args:
        print("usage: permissions.py <agent> [files...]")
        return 2
    agent, files = args[0], args[1:]
    policy = load_policy()
    if policy is None:
        return 1
    # Служебные ключи ("_deny_agents", "_comment") — не агенты
    deny = policy.get("_deny_agents") or []
    agents = {k: v for k, v in policy.items() if not k.startswith("_")}
    if agent not in agents:
        print("ERROR: агент «%s» не в политике (%s)" % (agent, ", ".join(sorted(agents))))
        return 1
    globs = agents[agent]
    if not files:
        files = git_changes()
        if files is None:
            return 1
    if not files:
        print("OK: нет изменений для проверки")
        return 0
    # deny-список — ПЕРВЫМ и для ЛЮБОГО агента (в т.ч. с зоной "**"): критические
    # пути правит только человек (решение Stefan 2026-07-06, gate-10/C31)
    denied_files = {f for f in files if denied(f, deny)}
    violations = [f for f in files
                  if f in denied_files or not any(match(f, g) for g in globs)]
    for f in files:
        mark = "ok" if f not in violations else (
            "ВНЕ ЗОНЫ (deny: только человек)" if f in denied_files else "ВНЕ ЗОНЫ")
        print("  [%s] %s" % (mark, f))
    if violations:
        print("ERROR: %s пишет вне своих путей: %s" % (agent, ", ".join(violations)))
        return 1
    print("OK: все изменения (%d) в зоне агента %s" % (len(files), agent))
    return 0

if __name__ == "__main__":
    sys.exit(main())
