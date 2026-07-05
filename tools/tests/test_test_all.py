#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_test_all
# TYPE: active-script
# DOMAIN: core.testing
# DEPTH_LEVEL: 2
# SUMMARY: Смоук-тест раннера test_all.py: агрегация exit-кодов на фейковых зелёном/красном/pytest-only скриптах.
# ==========================================
"""
"""Смоук-тест tools/test_all.py (C13-c): tmp-каталог с зелёным, красным и pytest-only
фейк-скриптами → проверяем агрегацию кодов (не-ноль хотя бы одного → не-ноль итог),
классификацию skip, --filter и то, что --list ничего не запускает.
"""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import shutil
import subprocess
import sys

from _ioutil import configure_output

HERE = _TOOLS_DIR  # tools/
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO_ROOT, "drivers"))
configure_output()

from test_tmp import make_temp_dir  # noqa: E402 — hermetic tmp в tmp-work (рецепт F-friction)

TEST_ALL = os.path.join(HERE, "test_all.py")

GREEN = """import sys
if __name__ == "__main__":
    # сентинел: файл-маркер доказывает, что скрипт реально ЗАПУСКАЛСЯ (для проверки --list)
    open(__file__ + ".ran", "w").close()
    print("OK green")
    sys.exit(0)
"""

RED = """import sys
if __name__ == "__main__":
    print("FAIL red by design")
    sys.exit(3)
"""

PYTEST_ONLY = """def test_nothing():
    assert True
"""


def _make_fixture_dir():
    d = make_temp_dir("test_all_smoke_")
    with open(os.path.join(d, "test_green.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(GREEN)
    with open(os.path.join(d, "test_red.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(RED)
    with open(os.path.join(d, "test_pytest_only.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PYTEST_ONLY)
    return d


def _run(*args):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, TEST_ALL, *args],
        env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL, timeout=120,
    )


def test_aggregation_red_and_green():
    """Красный скрипт красит итог (rc=1), зелёный/скип посчитаны; --filter сужает до зелёного."""
    d = _make_fixture_dir()
    try:
        # 1) полный прогон: red → итог не-ноль; счётчики ok=1 fail=1 skip=1
        p = _run("--dir", d, "--timeout", "60")
        assert p.returncode == 1, (p.returncode, p.stdout, p.stderr)
        assert "ИТОГ test_all: ok=1 fail=1 skip=1" in p.stdout, p.stdout
        assert "test_red.py" in p.stdout, p.stdout
        # pytest-only файл не запускался как скрипт, а ушёл в skip
        assert "test_pytest_only.py" not in p.stdout.split("Красные:")[-1], p.stdout

        # 2) --filter green: только зелёный → rc=0
        p = _run("--dir", d, "--filter", "green", "--timeout", "60")
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert "ИТОГ test_all: ok=1 fail=0 skip=0" in p.stdout, p.stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_list_does_not_execute():
    """--list печатает план (run/skip) и НЕ запускает скрипты (сентинел не появляется)."""
    d = _make_fixture_dir()
    try:
        p = _run("--dir", d, "--list")
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert "run  test_green.py" in p.stdout, p.stdout
        assert "run  test_red.py" in p.stdout, p.stdout
        assert "skip test_pytest_only.py" in p.stdout, p.stdout
        assert "ПЛАН test_all: run=2 skip=1" in p.stdout, p.stdout
        sentinel = os.path.join(d, "test_green.py.ran")
        assert not os.path.exists(sentinel), "--list не должен запускать скрипты"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_dir():
    """Несуществующий каталог → rc=2 (диагностика, не тихий 0)."""
    p = _run("--dir", os.path.join(REPO_ROOT, "tmp-work", "no_such_dir_xyz"))
    assert p.returncode == 2, (p.returncode, p.stdout, p.stderr)


def run():
    test_aggregation_red_and_green()
    test_list_does_not_execute()
    test_missing_dir()
    print("TESTS OK test_all: агрегация rc (red→1) + счётчики ok/fail/skip + --filter + --list без запуска + rc=2 на кривом dir")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
