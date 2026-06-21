#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест flow.py — обвязка Уровня-1 (--worktree) и сохранность ветко-режима (Уровень-0). Dry-by-default."""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _run(*args):
    p = subprocess.run([sys.executable, os.path.join(HERE, "flow.py"), *args],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    return (p.stdout or "") + (p.stderr or "")


def run():
    ok = True
    try:
        # Уровень-1: start --worktree -> приток (git worktree add), НЕ checkout
        out = _run("start", "claude", "T-140", "--worktree")
        assert "git worktree add" in out and "checkout" not in out, out
        assert "(печать" in out, "должно быть dry без --run"

        # Уровень-0: start без флага -> прежнее поведение (checkout -b)
        out = _run("start", "claude", "T-140")
        assert "git checkout -b agent/claude/T-140" in out, out
        assert "worktree" not in out, "без --worktree не должно трогать worktree"

        # Уровень-1: finish --worktree -> merge_gate -> merge -> снять приток
        out = _run("finish", "claude", "T-140", "--worktree")
        assert "merge_gate.py check" in out, out
        assert "git merge --no-ff agent/claude/T-140" in out, out
        assert "git worktree remove" in out and "git branch -D agent/claude/T-140" in out, out

        print("TESTS OK flow: --worktree обвязка (start приток / finish gate->merge->remove) + Ур.0 цел")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
