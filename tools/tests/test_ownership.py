#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_ownership
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_ownership.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест ownership (tools/ownership.py) — классификатор mine/generated/volatile/foreign/unknown."""
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
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import ownership as own
from test_tmp import make_temp_dir


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _claim(root, task, agent):
    d = os.path.join(root, "queues", "claimed")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "%s.claim.md" % task), "w", encoding="utf-8", newline="\n") as f:
        f.write("---\ntask: %s\nagent: %s\nclaim_id: x\n---\n" % (task, agent))


def run():
    ok = True
    base = make_temp_dir("ownership_")
    try:
        _claim(base, "T-150", "codex")   # чужая задача
        _claim(base, "T-153", "claude")  # моя задача

        def c(path, **kw):
            return own.classify(path, root=base, **kw)

        # generated
        assert c("TASKS.md") == "generated", c("TASKS.md")
        assert c("index.json") == "generated", c("index.json")
        # volatile
        assert c("LIVE.md") == "volatile", c("LIVE.md")
        assert c("logs/heartbeat.json") == "volatile", c("logs/heartbeat.json")
        assert c("PIPELINE.md") == "volatile", c("PIPELINE.md")
        # foreign: source-файл чужой заявленной задачи
        assert c("tasks/T-150.md", agent="claude") == "foreign", c("tasks/T-150.md", agent="claude")
        # mine: source-файл моей заявленной задачи
        assert c("tasks/T-153.md", agent="claude") == "mine", c("tasks/T-153.md", agent="claude")
        # mine: явный список файлов задачи
        assert c("docs/whatever.md", agent="claude", task_files=["docs/whatever.md"]) == "mine"
        # unknown: source без привязки (мой свежий инструмент)
        assert c("tools/cohort.py", agent="claude") == "unknown", c("tools/cohort.py", agent="claude")
        # foreign по суффиксу имени в чужом stream/outbox
        assert c("queues/outbox/2026-06-22-codex-x.md", agent="claude") == "foreign"

        # C36-a (волна 2): агент из ЕДИНОГО ростера (_canon.AGENTS_ROSTER) виден классификатору —
        # в т.ч. mavis/novax, которых регекс-хардкод мог потерять при рассинхроне копий
        from _canon import AGENTS_ROSTER
        for a in AGENTS_ROSTER:
            if a == "claude":
                continue
            got = c("queues/outbox/2026-06-22-%s-x.md" % a, agent="claude")
            assert got == "foreign", "агент %r из ростера должен давать foreign: %r" % (a, got)

        # summary.has_foreign
        s = own.summary(["TASKS.md", "tools/cohort.py", "tasks/T-150.md"], agent="claude", root=base)
        assert s["has_foreign"] is True, s
        assert "tasks/T-150.md" in s["by"]["foreign"], s
        assert "TASKS.md" in s["by"]["generated"], s
        s2 = own.summary(["TASKS.md", "tools/cohort.py"], agent="claude", root=base)
        assert s2["has_foreign"] is False, s2

        print("TESTS OK ownership: mine/generated/volatile/foreign/unknown + summary.has_foreign")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
