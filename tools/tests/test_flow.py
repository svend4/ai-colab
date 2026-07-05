#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_flow
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_flow.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест flow.py — обвязка Уровня-1 (--worktree) и сохранность ветко-режима (Уровень-0). Dry-by-default."""
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
import json
import subprocess

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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

        # merge-back race close (P4 EDIT 6): пост-merge регенерация индексов в merge-commit (dry)
        out = _run("finish", "mavis", "T-020", "--worktree")
        assert out.count("tools/generate.py") >= 2, "merge-back: нужен пост-merge regenerate"
        assert "commit --amend" in out, "merge-back: индексы должны вкладываться в merge-commit"
        # post-merge gate присутствует после merge (закрытие гонки flow.py:141)
        assert out.rfind("merge_gate.py") > out.find("git merge"), "пост-merge гейт после merge"

        # Внешний launcher запускает sub-agent, а repo-flow печатает воспроизводимый handoff.
        out = _run("launch-plan", "mavis", "T-200", "parallel", "policy", "--worktree")
        assert "# Sub-agent launch plan" in out, out
        assert "External sub-agent prompt" in out, out
        assert "Task: `T-200`." in out, out
        assert "python tools/flow.py start mavis T-200 --worktree" in out, out
        assert 'python tools/top.py agent-start mavis --context "parallel policy"' in out, out
        assert "python tools/pipeline.py claim mavis T-200" in out, out
        assert "python tools/flow.py finish mavis T-200 --worktree" in out, out

        out = _run("launch-plan", "mavis", "T-200", "parallel", "policy", "--worktree", "--json")
        data = json.loads(out)
        assert data["schema"] == "subagent_launch_plan.v1", data
        assert data["agent"] == "mavis" and data["task"] == "T-200", data
        assert data["repo_lane"]["mode"] == "worktree", data
        assert data["commands"]["prepare"] == ["python", "tools/flow.py", "start", "mavis", "T-200", "--worktree"], data
        assert data["commands"]["finish_text"] == "python tools/flow.py finish mavis T-200 --worktree", data
        assert 'python tools/top.py agent-start mavis --context "parallel policy"' in data["worker_prompt"], data

        print("TESTS OK flow: --worktree обвязка + launch-plan markdown/json handoff + Ур.0 цел")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
