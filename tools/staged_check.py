# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.staged_check
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: Проверка staged-снимка для pre-commit: канон-источники staged без регенерированной навигации → блок.
# ==========================================
"""staged_check.py — гейт «частичного стейджинга» навигации (C1-b, аудит 2026-07-02).

Корневая причина находки C1: pre-commit проверял РАБОЧЕЕ ДЕРЕВО (`generate.py --check`),
а не staged-снимок. Сценарий обхода: агент регенерировал навигацию (рабочее дерево чистое,
--check зелёный), но в коммит добавил только канон-источники — регенерированные
STATUS.md/board.md/index.json/indexes/* остались незастейдженными. HEAD становится
внутренне противоречивым: свежий клон провалит `generate.py --check` (прецедент faab828).

Правило: если staged есть канон-источник (topics/tasks/questions/decisions/drivers),
а у генерируемых файлов навигации есть НЕзастейдженные изменения — блокировать коммит
(exit 1) с подсказкой добавить регенераты. Если генераты вообще не менялись (правка тела
без front-matter), блока нет — регенерация не требовалась.

Исключение (D-023, «загрязнённый случай»): владелец source сознательно НЕ коммитит индекс,
захвативший чужой незакоммиченный source — тогда разовый обход `git commit --no-verify`.

CLI:
  python tools/staged_check.py            # exit 0 = ок; 1 = блок; 2 = git недоступен (fail-open в хуке)
  python tools/staged_check.py --json
"""
import os
import sys
import json
import subprocess

from _ioutil import configure_output
from _cli import help_guard

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

# Канон-источники, из которых generate.py строит навигацию (front-matter carriers).
SOURCE_PREFIXES = ("topics/", "tasks/", "questions/", "decisions/", "drivers/")
# Генерируемые файлы навигации (регенераты generate.py).
GENERATED_FILES = {"STATUS.md", "board.md", "TASKS.md", "QUESTIONS.md", "DECISIONS.md", "index.json"}
GENERATED_PREFIXES = ("indexes/",)


def _norm(path):
    return str(path).replace("\\", "/").lstrip("./")


def _is_source(path):
    p = _norm(path)
    return p.startswith(SOURCE_PREFIXES) and p.endswith(".md")


def _is_generated(path):
    p = _norm(path)
    return p in GENERATED_FILES or p.startswith(GENERATED_PREFIXES)


def verdict(staged, unstaged):
    """Чистая логика (тестируемо без git): блокировать ли коммит по staged-снимку.

    Блок ⇔ (staged содержит канон-источник) И (у генератов есть незастейдженные изменения):
    значит, регенерированная навигация существует, но В КОММИТ не попадает — ровно класс C1.
    """
    staged_sources = sorted(p for p in map(_norm, staged) if _is_source(p))
    unstaged_generated = sorted(p for p in map(_norm, unstaged) if _is_generated(p))
    blocked = bool(staged_sources and unstaged_generated)
    return {
        "blocked": blocked,
        "staged_sources": staged_sources,
        "unstaged_generated": unstaged_generated,
        "reason": ("канон-источники staged, а регенерированная навигация не застейджена "
                   "(частичный стейджинг, класс C1)" if blocked else ""),
    }


def _git_lines(args):
    """Строки вывода git или None при недоступном git (fail-open решает вызывающий)."""
    try:
        p = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return [ln.strip() for ln in (p.stdout or "").splitlines() if ln.strip()]


def check():
    """Verdict по реальному репо. None → git недоступен (exit 2, хук не блокирует)."""
    staged = _git_lines(["diff", "--cached", "--name-only"])
    unstaged = _git_lines(["diff", "--name-only"])
    if staged is None or unstaged is None:
        return None
    return verdict(staged, unstaged)


def main(argv):
    help_guard(__doc__, argv)
    res = check()
    if res is None:
        print("staged_check: git недоступен — проверка staged-снимка пропущена (fail-open).")
        return 2
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 1 if res["blocked"] else 0
    if not res["blocked"]:
        print("staged_check: OK — staged-снимок согласован (источники ↔ навигация).")
        return 0
    print("staged_check: БЛОК — канон-источники staged, а регенерированная навигация не добавлена в коммит:")
    for p in res["staged_sources"]:
        print("  source (staged):      %s" % p)
    for p in res["unstaged_generated"]:
        print("  генерат (НЕ staged):  %s" % p)
    print("Добавь регенераты: git add %s" % " ".join(res["unstaged_generated"]))
    print("(Исключение D-023 «foreign-индекс не коммичу» — разовый git commit --no-verify.)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
