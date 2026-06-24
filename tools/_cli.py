"""_cli.py — общий CLI-хелпер (агент-дружелюбный --help без argparse-бойлерплейта).

Лечит ВЕРИФИЦИРОВАННУЮ боль из kotel-system-critique-2026-06-24: ручной sys.argv не даёт `--help`
(conveyor.py выходит rc=2, другие запускают default-действие вместо подсказки — это разрушает
зондирование инструмента агентом). Один вызов `help_guard(__doc__)` в начале main() даёт корректный
`--help`/`-h` (печать docstring + exit 0) ВСЕМ sys.argv-тулам без перехода на argparse и без правки
парсинга. Пропорциональный фикс: 1 строка/тул вместо переписывания 63 CLI.

`die()` — ошибка в STDERR (чистый STDOUT для JSON-пайпов `tool --json | jq`), exit с кодом.

Применение:
    from _cli import help_guard, die
    def main(argv):
        help_guard(__doc__, argv)      # --help/-h → docstring, exit 0
        ...
"""
import sys


def help_guard(doc, argv=None):
    """--help/-h в argv → печать docstring в stdout, exit 0. Иначе — ничего (продолжаем)."""
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--help" in argv or "-h" in argv:
        sys.stdout.write((doc or "(нет docstring)").strip() + "\n")
        raise SystemExit(0)


def die(msg, code=2):
    """Ошибка → STDERR (stdout остаётся чистым для пайпов), exit с кодом (по умолч. 2)."""
    sys.stderr.write(str(msg).rstrip() + "\n")
    raise SystemExit(code)
