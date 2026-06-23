#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

        print("TESTS OK conveyor: assess(refill/process/idle/healthy/output refs) + реестр round-trip + кандидаты бэклога")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
