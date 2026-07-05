"""Тест _cli.py — help_guard (--help → docstring + exit0) и die (→ stderr + код)."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import io
import subprocess

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _cli


def _run_help(script):
    return subprocess.run(
        [sys.executable, os.path.join(HERE, script), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )

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
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        _cli.help_guard("Y", ["-h"]); fails.append("-h не сработал")
    except SystemExit:
        pass
    finally:
        sys.stdout = old
    if "Y" not in buf.getvalue():
        fails.append("-h не напечатал docstring")

    # без --help — НИЧЕГО (продолжаем)
    try:
        _cli.help_guard("Z", ["--json", "foo"])
    except SystemExit:
        fails.append("help_guard сработал без --help (ложно)")

    # real tools: --help must be safe, useful, exit 0, and not write reconcile reports
    outbox = os.path.join(ROOT, "queues", "outbox")
    before = set(os.listdir(outbox)) if os.path.isdir(outbox) else set()
    help_cases = [
        ("conveyor.py", "python tools/conveyor.py status"),
        ("dispatch.py", "python tools/dispatch.py next"),
        ("reconcile_state.py", "python tools/reconcile_state.py check"),
        ("dir_health.py", "python tools/dir_health.py [root]"),
        ("sandbox_intake_demo.py", "python tools/sandbox_intake_demo.py [source-dir]"),
        ("drivers_catalog.py", "python tools/drivers_catalog.py --check"),
        ("heading_check.py", "python tools/heading_check.py <file>"),
        ("portability_check.py", "python tools/portability_check.py --json"),
        ("report_diff.py", "python tools/report_diff.py reports/a.md reports/b.md"),
    ]
    for script, marker in help_cases:
        p = _run_help(script)
        if p.returncode != 0:
            fails.append("%s --help rc=%s stderr=%s" % (script, p.returncode, p.stderr.strip()))
        if marker not in p.stdout:
            fails.append("%s --help не содержит marker %r" % (script, marker))
    after = set(os.listdir(outbox)) if os.path.isdir(outbox) else set()
    if before != after:
        fails.append("--help изменил queues/outbox: %s" % sorted(after - before))
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
    print("OK test_cli: help_guard + die + real tool --help is safe/useful")


if __name__ == "__main__":
    main()
