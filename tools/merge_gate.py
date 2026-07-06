# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.merge_gate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт merge_gate.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Merge-gate orchestrator — «безопасно ли вливать эту работу в mainline?» green(0)/red(1).

Прогоняет существующие компоненты гейта (все ТОЛЬКО ЧИТАЮТ) и печатает отчёт по стадиям.
Команды стадий — те же, что уже определены в tools/flow.py для start/gate/finish:
    (1) validate.py
    (2) generate.py --check
    (3) permissions.py <agent>          # только если передан <agent>
С флагом --with-tests дополнительно находит tools/tests/test_*.py через glob и запускает их.
По умолчанию тесты ВЫКЛЮЧЕНЫ: in-flight падающий тест соседа (например test_top.py)
не должен ложно красить гейт.

    python tools/merge_gate.py check [<agent>] [<task>] [--with-tests]

exit 0 — все стадии зелёные; exit 1 — хотя бы одна красная.
"""
import os
import sys
import glob
import subprocess

from _ioutil import configure_output
from _cli import help_guard

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

configure_output()


def _run(script, *args):
    """Запустить tools/<script> read-only; вернуть (rc, combined output).

    Паттерн drift_check/onboard: sys.executable, capture_output, utf-8/replace,
    stdin=DEVNULL (фикс зависания на Windows)."""
    p = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", script), *args],
        cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def gate_stages(agent=None, with_tests=False):
    """Список стадий гейта как (label, script, args).

    Команды зеркалят tools/flow.py gate: validate -> generate --check -> permissions <agent>.
    permissions добавляется только если передан agent. С with_tests — каждый tools/tests/test_*.py (C14)."""
    stages = [
        ("validate", "validate.py", ()),
        ("generate --check", "generate.py", ("--check",)),
    ]
    if agent:
        stages.append(("permissions %s" % agent, "permissions.py", (agent,)))
    if with_tests:
        # C14: тесты перенесены в tools/tests/ — скрипт стадии задаётся путём относительно tools/
        for path in sorted(glob.glob(os.path.join(ROOT, "tools", "tests", "test_*.py"))):
            base = os.path.basename(path)
            stages.append(("test:%s" % base, os.path.join("tests", base), ()))
    return stages


def _is_green(rc, out):
    """Стадия зелёная, если rc==0 и в выводе нет маркеров провала (STALE/ERROR=N>0)."""
    if rc != 0:
        return False
    if "STALE" in out:
        return False
    return True


def gate(agent=None, with_tests=False, runner=None):
    """Прогнать стадии, вернуть (all_green, results).

    runner инъектируется (по умолчанию модульный _run, разрешается в момент вызова —
    чтобы monkeypatch mg._run работал) — тест подменяет его контролируемой фикстурой,
    чтобы PASS/FAIL не зависел от реального состояния репо (его churn'ит Codex)."""
    if runner is None:
        runner = _run
    results = []
    all_green = True
    for label, script, args in gate_stages(agent, with_tests):
        rc, out = runner(script, *args)
        green = _is_green(rc, out)
        if not green:
            all_green = False
        results.append((label, green, rc, out))
    return all_green, results


def _print_report(results):
    print("=" * 60)
    print("MERGE GATE")
    print("=" * 60)
    for label, green, rc, _out in results:
        mark = "GREEN" if green else "RED"
        print("  [%-5s] %-28s (rc=%s)" % (mark, label, rc))


def main():
    help_guard(__doc__)
    args = [a for a in sys.argv[1:] if a != "--with-tests"]
    with_tests = "--with-tests" in sys.argv
    if not args or args[0] != "check":
        print(__doc__)
        return 2
    rest = args[1:]
    agent = rest[0] if rest else None
    # rest[1] — необязательный <task> (контекст для отчёта; стадии его не используют).
    task = rest[1] if len(rest) > 1 else None

    all_green, results = gate(agent=agent, with_tests=with_tests)
    _print_report(results)
    ctx = []
    if agent:
        ctx.append("agent=%s" % agent)
    if task:
        ctx.append("task=%s" % task)
    suffix = (" [%s]" % " ".join(ctx)) if ctx else ""
    if all_green:
        print("РЕЗУЛЬТАТ: GREEN — безопасно вливать%s" % suffix)
        return 0
    print("РЕЗУЛЬТАТ: RED — НЕ вливать%s" % suffix)
    return 1


if __name__ == "__main__":
    sys.exit(main())
