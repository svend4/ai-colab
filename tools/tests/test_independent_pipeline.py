#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест independent_pipeline.py — оркестратор конвейера D-030 (grow-only connector).

Логику оркестрации тестируем IN-PROCESS с подменённым _run (быстро, детерминированно, mutation-sensitive:
мутации PHASES/PER_TOPIC/цикла run() ломают точные утверждения). Реальную subprocess-интеграцию с 7
тулами проверяет отдельный smoke-прогон `independent_pipeline.py --board` (см. конец).
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
import sys
import time
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
configure_output()
import independent_pipeline as pipe

EXPECTED_TOOLS = [None, "ripeness_gate", "portals", "independence_measure",
                  "consensus_by_meaning", "divergence_detail", "red_team_gate", "oracle_quorum"]


def run():
    tmp_root = os.path.join(REPO_ROOT, "tmp-work")
    os.makedirs(tmp_root, exist_ok=True)
    root = os.path.join(tmp_root, "indep_pipe_test_%d_%d" % (os.getpid(), time.time_ns()))
    os.makedirs(root, exist_ok=True)
    saved_root = pipe.ROOT
    saved_run = pipe._run
    try:
        os.makedirs(os.path.join(root, "variants", "topic-a"))
        os.makedirs(os.path.join(root, "variants", "topic-b"))
        pipe.ROOT = root

        calls = []

        def fake_run(tool, *args):
            calls.append((tool, args))
            return 0, "BOARD %s %s" % (tool, " ".join(args)), ""

        pipe._run = fake_run

        # --- мета-доска (board-режим) ---
        rows = pipe.run()
        assert [r["phase"] for r in rows] == ["1", "2", "3", "4", "5", "6", "7", "8"], \
            "фазы 1..8 в порядке: %s" % [r["phase"] for r in rows]
        assert [r["tool"] for r in rows] == EXPECTED_TOOLS, \
            "тулы в порядке конвейера: %s" % [r["tool"] for r in rows]
        assert all(r["rc"] == 0 for r in rows), "rc захвачен по всем фазам"
        assert "2 тем" in rows[0]["summary"], "фаза 1 считает темы variants/: %s" % rows[0]["summary"]
        # все 7 тулов реально вызваны в board-режиме
        assert calls == [(t, ("--board",)) for t in EXPECTED_TOOLS[1:]], \
            "каждый тул вызван с --board: %s" % calls

        # --- per-topic режим: фазы 4-5 идут по теме, остальные остаются board ---
        calls.clear()
        rows2 = pipe.run("topic-a")
        cmap = dict((t, a) for t, a in calls)
        assert cmap["independence_measure"] == ("topic-a",), "фаза 4 по теме: %s" % cmap.get("independence_measure")
        assert cmap["consensus_by_meaning"] == ("topic-a",), "фаза 5 по теме: %s" % cmap.get("consensus_by_meaning")
        assert cmap["ripeness_gate"] == ("--board",), "фаза 2 остаётся board"
        assert cmap["oracle_quorum"] == ("--board",), "фаза 8 остаётся board"
        assert "фокус: topic-a" in rows2[0]["summary"], "per-topic фокус виден"

        # --- грешный тул не роняет оркестратор (rc прокидывается) ---
        pipe._run = lambda tool, *a: (2, "", "boom")
        rows3 = pipe.run()
        assert len(rows3) == 8 and rows3[1]["rc"] == 2, "ошибка тула не ломает доску, rc прокинут"

        print("TESTS OK independent_pipeline: 8 фаз·порядок·тулы·board/per-topic·счёт тем·ошибка-тула-не-роняет")
        return 0
    finally:
        pipe.ROOT = saved_root
        pipe._run = saved_run
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
