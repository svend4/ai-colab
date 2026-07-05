#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_worktree
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_worktree.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест worktree.py (Уровень-1) — генерация команд + dry-by-default (без реальных git-worktree эффектов)."""
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
import contextlib

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import worktree as wt


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    try:
        # имена ветки/каталога
        assert wt.branch_name("claude", "T-140") == "agent/claude/T-140"
        p = wt.worktree_path("claude", "T-140")
        assert p.endswith("-wt-claude-T-140"), p
        # каталог притока — СОСЕД репо, не вложен в него
        assert os.path.dirname(os.path.abspath(wt.ROOT)) == os.path.dirname(p), "приток должен быть рядом с репо"

        # команды spawn/remove
        sc = wt.spawn_cmds("mavis", "T-9")
        assert sc == [["git", "worktree", "add", "-b", "agent/mavis/T-9", wt.worktree_path("mavis", "T-9")]], sc
        rc = wt.remove_cmds("mavis", "T-9")
        assert rc[0][:3] == ["git", "worktree", "remove"] and rc[1] == ["git", "branch", "-D", "agent/mavis/T-9"], rc

        # dry-by-default: run_or_print без --run печатает и НЕ выполняет (ничего не падает)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = wt.run_or_print([["git", "this-would-fail-if-run"]], do_run=False)
        out = buf.getvalue()
        assert r == 0 and "печать" in out and "this-would-fail-if-run" in out, out

        print("TESTS OK worktree: branch/path (приток-сосед) + spawn/remove cmds + dry-by-default")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
