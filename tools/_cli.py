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


def _real_docstring():
    """Из исходника вызывающего модуля достать первый топ-левел docstring, НЕ являющийся
    авто-визиткой [FILE ID CARD] (линтер вставляет её первой и она затеняет __doc__)."""
    import inspect
    import ast
    try:
        caller = inspect.stack()[2].filename
        with open(caller, encoding="utf-8") as f:
            mod = ast.parse(f.read())
        for node in mod.body:
            if (isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant)
                    and isinstance(node.value.value, str)):
                s = node.value.value
                if "[FILE ID CARD]" not in s:
                    return s.strip()
    except Exception:
        return None
    return None


def help_guard(doc, argv=None):
    """--help/-h в argv → печать docstring в stdout, exit 0. Иначе — ничего (продолжаем).
    Если __doc__ — авто-визитка [FILE ID CARD], печатаем РЕАЛЬНЫЙ docstring (с CLI-секцией)."""
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--help" in argv or "-h" in argv:
        text = (doc or "").strip()
        if "[FILE ID CARD]" in text:
            real = _real_docstring()
            if real:
                text = real
        sys.stdout.write((text or "(нет docstring)").strip() + "\n")
        raise SystemExit(0)


def die(msg, code=2):
    """Ошибка → STDERR (stdout остаётся чистым для пайпов), exit с кодом (по умолч. 2)."""
    sys.stderr.write(str(msg).rstrip() + "\n")
    raise SystemExit(code)
