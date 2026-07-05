#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_volatile
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_volatile.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Regression for D-022/T-148 volatile runtime snapshots.

Volatile files are useful live views, but they must not be tracked mainline files.
`pipeline.py snapshot` may rewrite them at any time; `generate.py --check` must stay green.
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
import subprocess
import sys

ROOT = os.path.dirname(_TOOLS_DIR)  # корень репозитория (тест перенесён в tools/tests/, C14)
VOLATILE = [
    "LIVE.md",
    "PIPELINE.md",
    "logs/heartbeat.json",
    "logs/pipeline.json",
]


def run_cmd(*args):
    p = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    rc, out = run_cmd("git", "ls-files", "--", *VOLATILE)
    if rc != 0:
        print(out)
        return rc
    tracked = [line.strip() for line in out.splitlines() if line.strip()]
    if tracked:
        print("TEST FAIL: volatile files are still tracked: %s" % ", ".join(tracked))
        return 1

    with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
        ignore = f.read()
    missing = [p for p in VOLATILE if p not in ignore]
    if missing:
        print("TEST FAIL: volatile files missing from .gitignore: %s" % ", ".join(missing))
        return 1

    rc, out = run_cmd(sys.executable, os.path.join(ROOT, "tools", "pipeline.py"), "snapshot")
    if rc != 0:
        print(out)
        return rc

    rc, out = run_cmd(sys.executable, os.path.join(ROOT, "tools", "generate.py"), "--check")
    if rc != 0:
        print(out)
        return rc

    print("TESTS OK volatile: untracked+ignored snapshots do not affect generate --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())