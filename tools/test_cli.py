"""Тест _cli.py — help_guard (--help → docstring + exit0) и die (→ stderr + код)."""
import os
import sys
import io

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _cli

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []

    # help_guard: --help → печать doc + SystemExit(0)
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        _cli.help_guard("ДОК-ТЕКСТ-X", ["--help"])
        fails.append("help_guard(--help) не вызвал SystemExit")
    except SystemExit as e:
        if e.code != 0:
            fails.append("help_guard exit != 0: %s" % e.code)
    finally:
        sys.stdout = old
    if "ДОК-ТЕКСТ-X" not in buf.getvalue():
        fails.append("help_guard не напечатал docstring")

    # -h тоже триггерит
    try:
        _cli.help_guard("Y", ["-h"]); fails.append("-h не сработал")
    except SystemExit:
        pass

    # без --help — НИЧЕГО (продолжаем)
    try:
        _cli.help_guard("Z", ["--json", "foo"])
    except SystemExit:
        fails.append("help_guard сработал без --help (ложно)")

    # die: сообщение в STDERR (не stdout), exit с кодом
    eb, ob = io.StringIO(), io.StringIO()
    oe, oo = sys.stderr, sys.stdout
    sys.stderr, sys.stdout = eb, ob
    try:
        _cli.die("ОШИБКА-Q", 2)
        fails.append("die не вызвал SystemExit")
    except SystemExit as e:
        if e.code != 2:
            fails.append("die exit != 2")
    finally:
        sys.stderr, sys.stdout = oe, oo
    if "ОШИБКА-Q" not in eb.getvalue():
        fails.append("die не написал в stderr")
    if ob.getvalue().strip():
        fails.append("die загрязнил stdout (должен быть чист для JSON-пайпов)")

    if fails:
        print("FAIL test_cli:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_cli: help_guard(--help/-h → doc+exit0, иначе пропуск) + die(stderr+код, чистый stdout)")


if __name__ == "__main__":
    main()
