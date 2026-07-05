#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_reconcile_state
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_reconcile_state.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Hermetic-тест reconcile_state: check-категории (done-missing-marker/orphan/drift)
детектятся на синтетическом дереве через COLLAB_ROOT.

Не трогает рабочий репо: строит временный COLLAB_ROOT (tasks/, queues/done,
queues/claimed, index.json, logs/pipeline.json) в tmp-work и переиспользует
drivers/test_tmp.make_temp_dir. COLLAB_ROOT выставляется ДО import pipeline/
reconcile_state, поэтому оба модуля видят фикстуру (pipeline.ROOT и P.ROOT
вычисляются на import-time из окружения).
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
import json

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

import test_tmp  # drivers/test_tmp.py — writable tmp-work helper


TASK_FM = (
    "---\n"
    "id: %s\n"
    "type: task\n"
    "title: %s\n"
    "status: %s\n"
    "owner: tester\n"
    "priority: normal\n"
    "risk: low\n"
    "depends_on: []\n"
    "---\n\n"
    "# %s\n"
)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _build_fixture(root):
    """Синтетическое дерево с заранее известными расхождениями по каждой check-категории."""
    tasks = os.path.join(root, "tasks")
    done = os.path.join(root, "queues", "done")
    claimed = os.path.join(root, "queues", "claimed")
    logs = os.path.join(root, "logs")
    for d in (tasks, done, claimed, logs):
        os.makedirs(d, exist_ok=True)

    # T-001: done в primary, но БЕЗ done-marker -> warning done-missing-marker
    _write(os.path.join(tasks, "T-001.md"), TASK_FM % ("T-001", "Done no marker", "done", "T-001"))

    # T-002: done в primary И есть marker -> чисто (контроль: не должно ругаться)
    _write(os.path.join(tasks, "T-002.md"), TASK_FM % ("T-002", "Done with marker", "done", "T-002"))
    _write(os.path.join(done, "T-002.done.md"), "done\n")

    # done-marker без задачи -> warning orphan-done-marker
    _write(os.path.join(done, "T-777.done.md"), "orphan\n")

    # claim без задачи -> warning orphan-claim
    _write(os.path.join(claimed, "T-888.claim.md"),
           "---\ntask: T-888\nagent: ghost\nclaim_id: dead\nlease_epoch: 9999999999\n---\n")

    # index.json со status, расходящимся с tasks/T-001.md (done) -> warning index-status-drift
    index = {"tasks": [{"id": "T-001", "status": "todo"}, {"id": "T-002", "status": "done"}]}
    _write(os.path.join(root, "index.json"),
           json.dumps(index, ensure_ascii=False, indent=2) + "\n")

    # logs/pipeline.json с фиктивным doing -> warning pipeline-snapshot-drift
    _write(os.path.join(logs, "pipeline.json"),
           json.dumps({"doing": [{"id": "T-555"}], "ready": [], "blocked": []},
                      ensure_ascii=False) + "\n")


def run():
    ok = True
    tmp = test_tmp.make_temp_dir("reconcile-state-")
    try:
        _build_fixture(tmp)
        os.environ["COLLAB_ROOT"] = tmp
        # import ПОСЛЕ выставления COLLAB_ROOT: модули зафиксируют ROOT из фикстуры
        import pipeline  # noqa: F401
        import reconcile_state as rs
        assert rs.ROOT == tmp, "reconcile_state.ROOT не указывает на фикстуру: %s" % rs.ROOT

        # регресс (аудит P3/B-04): в исходнике модуля нет bare-CR переводов строк
        # (bare-CR ломает git-диффы: файл считается -text/binary)
        raw = open(os.path.join(HERE, "reconcile_state.py"), "rb").read()
        assert b"\r" not in raw.replace(b"\r\n", b"\n"), \
            "bare-CR переводы строк в reconcile_state.py (git видит файл как binary)"

        report = rs.reconcile()
        codes = {(it["code"], it["task"]) for it in report["items"]}

        # каждая целевая check-категория сдетектилась на своём fixture-входе
        assert ("done-missing-marker", "T-001") in codes, codes
        assert ("orphan-done-marker", "T-777") in codes, codes
        assert ("orphan-claim", "T-888") in codes, codes
        assert ("index-status-drift", "T-001") in codes, codes
        assert ("pipeline-snapshot-drift", "-") in codes, codes

        # контроль: T-002 (done + marker, index==primary) НЕ порождает done-missing-marker/drift
        bad = {c for (c, t) in codes if t == "T-002"}
        assert not bad, "T-002 (согласованная задача) не должна давать находок: %s" % bad

        # статус отчёта и exit-код согласованы: есть warning -> status=warning, exit=1
        assert report["status"] == "warning", report["status"]
        assert report["counts"]["warning"] >= 4, report["counts"]
        assert rs.exit_code(report) == 1, rs.exit_code(report)

        # check НЕ должен писать в outbox (report-режим пишет, check — нет)
        outbox = os.path.join(tmp, "queues", "outbox")
        before = set(os.listdir(outbox)) if os.path.isdir(outbox) else set()
        sys.argv = ["reconcile_state.py", "check"]
        rs.main()
        after = set(os.listdir(outbox)) if os.path.isdir(outbox) else set()
        assert before == after, "check НЕ должен писать в outbox: %s" % (after - before)

        print("TESTS OK reconcile_state: done-missing-marker/orphan-done/orphan-claim/"
              "index-drift/snapshot-drift детектятся на fixture; check без записи; нет bare-CR")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        import shutil
        os.environ.pop("COLLAB_ROOT", None)
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
