#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест doc_consensus (tools/doc_consensus.py) — консенсус (>=2 док.) + разногласия (1 док.)."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DRIVERS = os.path.join(ROOT, "drivers")
sys.path.insert(0, HERE)
sys.path.insert(0, DRIVERS)
import doc_consensus as dc
from test_tmp import make_temp_dir


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    base = make_temp_dir("doccons_")
    try:
        d1 = os.path.join(base, "agentA.md")
        d2 = os.path.join(base, "agentB.md")
        with open(d1, "w", encoding="utf-8") as f:
            f.write("# A\n\n- консенсус безопасность коммитов commit_lock\n"
                    "- уникальный червонец worktree изоляцию агента\n")
        with open(d2, "w", encoding="utf-8") as f:
            f.write("# B\n\n- консенсус безопасность коммитов всегда\n"
                    "- особенный пункт sandbox приём внешнего\n")

        res = dc.analyze([d1, d2], root=base, thr=0.4)

        # консенсус: 1 кластер на >=2 документа (общий пункт безопасности)
        assert len(res["consensus"]) == 1, "ожидался 1 консенсус-кластер: %d" % len(res["consensus"])
        cl = res["consensus"][0]
        docs = {u["doc"] for u in cl["members"]}
        assert len(docs) == 2, "консенсус должен охватывать оба дока: %s" % docs
        wheres = sorted(u["where"] for u in cl["members"])
        assert any("agentA.md" in w for w in wheres) and any("agentB.md" in w for w in wheres), wheres

        # разногласия: по одному уникальному пункту на документ
        div_docs = {c["members"][0]["doc"] for c in res["divergent"]}
        assert "agentA.md" in div_docs and "agentB.md" in div_docs, "разногласия по обоим докам: %s" % div_docs
        assert len(res["divergent"]) >= 2, "ожидалось >=2 разногласия: %d" % len(res["divergent"])

        q1 = os.path.join(base, "q1.md")
        q2 = os.path.join(base, "q2.md")
        with open(q1, "w", encoding="utf-8") as f:
            f.write("---\nid: q1\n---\n\n# Q1\n\nОбщий пункт: применять инструкции через evidence gate.\n\nУникальная часть A: freshness metadata.\n")
        with open(q2, "w", encoding="utf-8") as f:
            f.write("# Q2\n\nОбщий пункт: применять инструкции через evidence gate.\n\nУникальная часть B: promotion coverage.\n")
        res2 = dc.analyze([q1, q2], root=base, thr=0.4)
        assert res2["n_units"] >= 4, "H1/абзацы должны извлекаться: %s" % res2
        assert len(res2["consensus"]) >= 1, "ожидался consensus из абзацев: %s" % res2

        # render не падает и содержит секции
        txt = dc.render(res)
        assert "Консенсус" in txt and "Разногласия" in txt, "render без секций"

        print("TESTS OK doc_consensus: консенсус(>=2 док, cross-ref) + разногласия(1 док)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
