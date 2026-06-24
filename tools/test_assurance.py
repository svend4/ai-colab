#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_assurance
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_assurance.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест assurance (tools/assurance.py) — 4 секции на герметичной temp-пирамиде (--root)."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir
sys.path.insert(0, HERE)
import assurance as asr
import instructions as ins


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _build_pyramid(base):
    # 13 файлов реестра инструкций как заглушки; в AGENTS.md — ссылка на D-100.
    for item in ins.INSTRUCTIONS:
        body = "stub\n" + ("see D-100\n" if item["path"] == "AGENTS.md" else "")
        _w(os.path.join(base, item["path"]), body)

    # задачи (служебные: topic под tools/) + done-маркеры конвенц-эры (T>=156)
    for tid in ("T-200", "T-201", "T-202", "T-203"):
        _w(os.path.join(base, "tasks", "%s.md" % tid),
           "---\nid: %s\ntype: task\ntitle: Service %s\nstatus: done\ntopic: tools/x.py\n---\n" % (tid, tid))
    _w(os.path.join(base, "queues", "done", "T-200.done.md"),
       "---\ntask: T-200\nagent: t\napplied: AGENTS.md, PROTOCOL.md, tools/x.py, Checks\n---\n\n"
       "Applied instructions: AGENTS.md, PROTOCOL.md, tools/x.py, Checks\n")          # good
    _w(os.path.join(base, "queues", "done", "T-201.done.md"),
       "---\ntask: T-201\nagent: t\napplied: AGENTS.md, PROTOCOL.md, Checks\n---\n\n"
       "Applied instructions: AGENTS.md, PROTOCOL.md, Checks\n")                       # rescued by addendum
    _w(os.path.join(base, "queues", "evidence", "T-201.evidence.md"),
       "---\ntask: T-201\ntype: evidence-addendum\nagent: reviewer\n"
       "applied: AGENTS.md, PROTOCOL.md, tools/x.py, Checks\n---\n\n"
       "Applied instructions: AGENTS.md, PROTOCOL.md, tools/x.py, Checks\n")
    _w(os.path.join(base, "queues", "done", "T-202.done.md"),
       "---\ntask: T-202\nagent: t\n---\n\ndone\n")                                    # no applied -> high
    _w(os.path.join(base, "queues", "done", "T-203.done.md"),
       "---\ntask: T-203\nagent: t\napplied: AGENTS.md, PROTOCOL.md, Checks\n---\n\n"
       "Applied instructions: AGENTS.md, PROTOCOL.md, Checks\n")                       # boilerplate -> low

    # решения
    _w(os.path.join(base, "decisions", "D-100.md"),
       "---\nid: D-100\ntype: decision\nstatus: accepted\nlast_verified: 2026-06-20\n---\n# ok\n")
    _w(os.path.join(base, "decisions", "D-101.md"),
       "---\nid: D-101\ntype: decision\nstatus: accepted\ndate: 2026-06-20\n---\n# ghost\nсм. [x](docs/ghost.md)\n")
    _w(os.path.join(base, "decisions", "D-102.md"),
       "---\nid: D-102\ntype: decision\nstatus: superseded\ndate: 2026-06-01\n---\n# old\n")
    _w(os.path.join(base, "decisions", "D-103.md"),
       "---\nid: D-103\ntype: decision\nstatus: accepted\nlast_verified: 2026-06-20\n---\n# refs\nзаменяет D-102 в этой части\n")
    _w(os.path.join(base, "decisions", "D-104.md"),
       "---\nid: D-104\ntype: decision\nstatus: accepted\nlast_verified: 2026-06-20\n---\n# related\nСвязано: D-102 как исторический источник\n")

    # пирамида: ядро + порталы
    _w(os.path.join(base, "core", "engine-manifest.md"),
       "---\nid: m\ntype: core-export-manifest\nlevel: L1\nfiles: [tools/aa.py, tools/bb.py]\n---\n# core\n")
    _w(os.path.join(base, "portals", "p1", "portal.md"),
       "---\nid: p1\ntype: portal\nlevel: L2\nl1_basis: tools/aa.py\n---\n# p1\nОпирается на aa.py.\n")
    _w(os.path.join(base, "portals", "p2", "portal.md"),
       "---\nid: p2\ntype: portal\nlevel: L2\n---\n# p2\nБез опоры на ядро.\n")


def run():
    ok = True
    base = make_temp_dir("assurance_")
    try:
        _build_pyramid(base)

        applied = asr.section_applied(base)
        msgs = [f["msg"] for f in applied["findings"]]
        assert any("T-202" in m and "без applied" in m for m in msgs), "T-202 без evidence: %s" % msgs
        assert any("T-203" in m and "формальное" in m for m in msgs), "T-203 boilerplate: %s" % msgs
        assert not any("T-201" in m for m in msgs), "T-201 должен быть закрыт addendum: %s" % msgs
        assert "5/5" not in applied["metric"], "метрика должна считать temp-пирамиду, не реальный репо"
        assert "2/4" in applied["metric"] or "2/" in applied["metric"], "2 из 4 конвенц-эры с evidence: %s" % applied["metric"]

        cur = asr.section_currency(base, max_age=180)
        cmsgs = [f["msg"] for f in cur["findings"]]
        assert any("docs/ghost.md" in m for m in cmsgs), "битая структурная ссылка: %s" % cmsgs
        assert any("D-102" in m and "superseded" in m for m in cmsgs), "ссылка на superseded: %s" % cmsgs
        assert not any("D-104" in m and "D-102" in m for m in cmsgs), "related/history ссылка не drift: %s" % cmsgs
        assert any("last_verified" in m for m in cmsgs), "нудж по last_verified: %s" % cmsgs

        cov = asr.section_coverage(base)
        covmsgs = " ".join(f["msg"] for f in cov["findings"])
        assert "bb.py" in covmsgs, "orphan-L1 bb.py: %s" % covmsgs
        assert any("p2" in f["msg"] and "без опоры" in f["msg"] for f in cov["findings"]), "ungrounded p2: %s" % covmsgs

        flow = asr.section_flow(base)
        fmsgs = " ".join(f["msg"] for f in flow["findings"])
        assert "отсутствует" not in fmsgs, "заглушки реестра созданы -> нет missing-file: %s" % fmsgs
        assert "D-101" in fmsgs, "висячее accepted-решение D-101: %s" % fmsgs
        assert "D-100" not in fmsgs, "D-100 упомянуто в AGENTS.md -> не висячее: %s" % fmsgs

        # render + strict-семантика (hard = число high/medium)
        text, hard = asr.render([applied, cur, cov, flow])
        assert "Вердикт" in text and hard >= 1, "render/вердикт: %s" % hard
        _, empty_hard = asr.render([{"name": "x", "metric": "m", "findings": []}])
        assert empty_hard == 0, "пустая секция -> hard=0: %s" % empty_hard

        print("TESTS OK assurance: applied/currency/coverage/flow на temp-пирамиде + вердикт")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
