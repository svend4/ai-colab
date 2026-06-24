#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_conveyor
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_conveyor.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест conveyor (tools/conveyor.py) — оценка состояния, output refs, реестр round-trip, кандидаты."""
import os
import sys
import shutil
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir
sys.path.insert(0, HERE)
import conveyor as c


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

NOW = datetime.datetime(2026, 6, 23, 12, 0, 0)


def _ledger(workflows, hb=NOW, target=2, idle=20):
    return {"target_min": target, "idle_min": idle,
            "heartbeat": hb.isoformat() if hb else None, "workflows": workflows}


def _wf(wid, state, output=None):
    w = {"id": wid, "label": wid, "state": state}
    if output:
        w["output"] = output
    return w


def run():
    ok = True
    base = make_temp_dir("conveyor_")
    try:
        # --- assess: пусто -> REFILL, unhealthy ---
        a = c.assess(_ledger([]), NOW)
        assert a["deficit"] == 2 and not a["healthy"], a
        assert any("REFILL" in x for x in a["actions"]), a["actions"]

        # --- assess: 2 in-flight, свежий heartbeat -> healthy ---
        a = c.assess(_ledger([_wf("a", "inflight"), _wf("b", "inflight")]), NOW)
        assert a["healthy"] and a["deficit"] == 0, a

        # --- assess: landed с output и без output -> PROCESS + missing-output диагностика ---
        a = c.assess(_ledger([_wf("a", "inflight"), _wf("b", "landed", "tmp-work/b.output.md"), _wf("c", "landed")]), NOW)
        assert a["deficit"] == 1 and a["n_landed"] == 2 and not a["healthy"], a
        assert a["landed_outputs"] == [{"id": "b", "label": "b", "output": "tmp-work/b.output.md"}], a
        assert a["landed_without_output"] == ["c"], a
        assert any("PROCESS" in x for x in a["actions"]), a["actions"]
        assert any("PROCESS-MISSING-OUTPUT" in x for x in a["actions"]), a["actions"]
        assert "landed без output: c" in c.render_status(a), c.render_status(a)

        # --- assess: масштаб цели (флот) — target из ledger двигает deficit ---
        a = c.assess(_ledger([_wf("a", "inflight"), _wf("b", "inflight")], target=5), NOW)
        assert a["deficit"] == 3 and not a["healthy"], "target 5, 2 в полёте -> нужно ещё 3: %s" % a
        assert a["target"] == 5, a

        # --- assess: stale heartbeat -> IDLE ---
        old = NOW - datetime.timedelta(minutes=30)
        a = c.assess(_ledger([_wf("a", "inflight"), _wf("b", "inflight")], hb=old), NOW)
        assert any("IDLE" in x for x in a["actions"]), a["actions"]

        # --- regulate: advisory target sizing, no mutation ---
        clean_assurance = {"ok": True, "findings": 0}
        bad_assurance = {"ok": False, "findings": 2}
        r = c.regulate(_ledger([_wf("a", "inflight"), _wf("b", "inflight")]), NOW,
                       assurance=clean_assurance)
        assert r["recommendation"] == "increase" and r["target_delta"] == 1 and not r["mutates"], r

        r = c.regulate(_ledger([_wf("a", "inflight")]), NOW, assurance=clean_assurance)
        assert r["recommendation"] == "hold" and r["target_delta"] == 0, r
        assert any("refill" in x for x in r["reasons"]), r

        r = c.regulate(_ledger([_wf("a", "inflight"), _wf("b", "landed")]), NOW,
                       assurance=clean_assurance)
        assert r["recommendation"] == "process-first" and r["target_delta"] == -1, r

        r = c.regulate(_ledger([_wf("a", "inflight"), _wf("b", "landed", "tmp-work/b.output.md")]), NOW,
                       assurance=clean_assurance,
                       classifications=[{"label": "b", "class": "governance"}])
        assert r["recommendation"] == "process-first", r
        assert any("governance" in x for x in r["reasons"]), r

        r = c.regulate(_ledger([_wf("a", "inflight"), _wf("b", "inflight")], hb=old), NOW,
                       assurance=clean_assurance)
        assert r["recommendation"] == "decrease" and r["target_delta"] == -1, r

        r = c.regulate(_ledger([_wf("a", "inflight"), _wf("b", "inflight")]), NOW,
                       assurance=bad_assurance)
        assert r["recommendation"] == "hold" and any("assurance" in x for x in r["reasons"]), r
        # --- реестр round-trip через диск ---
        path = os.path.join(base, "conv.json")
        d = c.load(path)
        c.cmd_launch(d, "w1", "alpha-map")
        c.save(d, path)
        d2 = c.load(path)
        assert c._find(d2, "w1")["state"] == "inflight", d2
        assert d2["heartbeat"], "launch должен писать heartbeat"
        c._set_state(d2, "w1", "landed", output="tmp-work/w1.output.md")
        c.save(d2, path)
        w1 = c._find(c.load(path), "w1")
        assert w1["state"] == "landed"
        assert w1["output"] == "tmp-work/w1.output.md", w1

        # --- кандидаты бэклога: исключают уже запущенные по подстроке label ---
        bpath = os.path.join(base, "backlog.md")
        with open(bpath, "w", encoding="utf-8", newline="\n") as f:
            f.write("# x\n\n## Готовы к запуску\n\n1. Alpha thing: do it\n2. Beta thing (other)\n\n## Следующее\n")
        cands_all = c.backlog_candidates({"workflows": []}, bpath)
        assert len(cands_all) == 2, cands_all
        cands_one = c.backlog_candidates({"workflows": [{"id": "w", "label": "Alpha thing", "state": "inflight"}]}, bpath)
        assert len(cands_one) == 1 and "Beta" in cands_one[0], cands_one
        with open(bpath, "w", encoding="utf-8", newline="\n") as f:
            f.write("# x\n\n## Готовы к запуску\n\n1. Instruction check-report: verify referenced files/commands exist\n2. Currency convention: adopt last_verified\n\n## Следующее\n")
        cands_norm = c.backlog_candidates({"workflows": [{"id": "codex-T-166", "label": "instruction-check-report-refs", "state": "shipped"}]}, bpath)
        assert len(cands_norm) == 1 and "Currency convention" in cands_norm[0], cands_norm

        # --- plan_hierarchy: reduce-дерево 3:1 (динамическое появление уровней) ---
        def top(n, span=3):
            return c.plan_hierarchy(n, span)[-1]
        # n<=3 → один слой интеграторов (бригад), верх = ceil(n/3) ≤ 3
        assert top(3)["level"] == 1 and top(3)["count"] == 1, c.plan_hierarchy(3)
        assert top(9)["level"] == 1 and top(9)["count"] == 3, c.plan_hierarchy(9)
        # >3 интеграторов → появляется дирижёр (L2)
        assert top(12)["level"] == 2 and top(12)["count"] == 2, c.plan_hierarchy(12)
        assert top(27)["level"] == 2 and top(27)["count"] == 3, c.plan_hierarchy(27)
        # >3 дирижёров → chief (L3)
        assert top(30)["level"] == 3 and top(30)["count"] == 2, c.plan_hierarchy(30)
        assert top(81)["level"] == 3 and top(81)["count"] == 3, c.plan_hierarchy(81)
        # накладные интеграции ограничены геом. рядом (~50%): для 27 → 9+3=12 интеграторов
        lay27 = c.plan_hierarchy(27)
        assert sum(L["count"] for L in lay27 if L["level"] >= 1) == 12, lay27
        # span переопределяется: n=16,span=4 → L1=4 (верх, ≤4); n=20 → 5 интеграторов >4 → дирижёр L2
        assert top(16, span=4)["level"] == 1 and top(16, span=4)["count"] == 4, c.plan_hierarchy(16, 4)
        assert top(20, span=4)["level"] == 2, c.plan_hierarchy(20, 4)
        assert "L2" in c.render_plan(27, 3, lay27)

        print("TESTS OK conveyor: assess/refill/process/idle + regulate advisory + реестр + нормализованный бэклог + plan(3:1 reduce-дерево)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
