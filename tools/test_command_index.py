"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_command_index
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_command_index.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест command_index.py — индекс команд из docstring (извлечение, gist, поиск)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import command_index as ci

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DOC = """foo.py — суть инструмента.

CLI:
    python tools/foo.py board [--json]
    python tools/foo.py run <x> --flag
    python tools/foo.py board [--json]
"""


def main():
    fails = []
    # gist из «name — суть»
    if ci._gist(DOC) != "суть инструмента.":
        fails.append("gist неверный: %r" % ci._gist(DOC))
    # команды: board + run (board дедуплицирован по usage)
    cmds = ci._commands("foo", DOC)
    verbs = [c["verb"] for c in cmds]
    if "board" not in verbs or "run" not in verbs:
        fails.append("команды board/run не извлечены: %s" % verbs)
    # дедуп: board встречается дважды с одним usage → один раз
    if verbs.count("board") != 1:
        fails.append("board не дедуплицирован: %s" % verbs)
    # реальный collect на репо: непустой, у каждого есть gist+commands
    data = ci.collect()
    if not data:
        fails.append("collect пуст на реальном репо")
    sample = next(iter(data.values()))
    if "gist" not in sample or "commands" not in sample:
        fails.append("структура collect без gist/commands")
    # сам себя индексирует
    if "command_index" not in data:
        fails.append("command_index не проиндексировал сам себя")

    if fails:
        print("FAIL test_command_index:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_command_index: извлечение команд + gist + дедуп + collect (%d инструментов)" % len(data))


if __name__ == "__main__":
    main()
