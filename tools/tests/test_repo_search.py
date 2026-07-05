#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_repo_search
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_repo_search.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест repo_search (tools/repo_search.py) — индекс + ранжированный поиск, герметично (temp-корпус)."""
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
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir
sys.path.insert(0, HERE)
import repo_search as rs


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    cdir = make_temp_dir("rs_")
    rel = os.path.relpath(cdir, ROOT).replace("\\", "/")
    db = "tmp-work/_rs_test_%d.db" % os.getpid()
    try:
        with open(os.path.join(cdir, "alpha.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# Alpha\n\nуникальныймаркерзизл про worktree изоляцию агента.\n")
        with open(os.path.join(cdir, "beta.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# Beta\n\nдругой текст про sandbox приём внешнего кода.\n")

        n = rs.build_index(db=db, dirs=[rel])
        assert n >= 2, "индекс должен охватить оба дока: %s" % n

        # уникальный токен находит именно alpha.md
        hits = rs.search("уникальныймаркерзизл", db=db, limit=5)
        assert hits, "поиск по уникальному токену должен находить"
        assert any("alpha.md" in (h.get("path") or "") for h in hits), "релевантный док в выдаче: %s" % hits

        # терм из beta находит beta, не alpha (ранжирование/recall)
        hits2 = rs.search("sandbox внешнего", db=db, limit=5)
        assert any("beta.md" in (h.get("path") or "") for h in hits2), "beta по своему терму: %s" % hits2

        print("TESTS OK repo_search: индекс temp-корпуса + ранжированный поиск (уникальный токен -> нужный док)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(cdir, ignore_errors=True)
        dbp = os.path.join(ROOT, db)
        if os.path.exists(dbp):
            os.remove(dbp)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
