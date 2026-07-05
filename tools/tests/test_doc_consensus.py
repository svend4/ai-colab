#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_doc_consensus
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_doc_consensus.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест doc_consensus (tools/doc_consensus.py) — консенсус (>=2 док.) + разногласия (1 док.)."""
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
import shutil
import subprocess

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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
        with open(d1, "w", encoding="utf-8", newline="\n") as f:
            f.write("# A\n\n- консенсус безопасность коммитов commit_lock\n"
                    "- уникальный червонец worktree изоляцию агента\n")
        with open(d2, "w", encoding="utf-8", newline="\n") as f:
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
        with open(q1, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: q1\n---\n\n# Q1\n\nОбщий пункт: применять инструкции через evidence gate.\n\nУникальная часть A: freshness metadata.\n")
        with open(q2, "w", encoding="utf-8", newline="\n") as f:
            f.write("# Q2\n\nОбщий пункт: применять инструкции через evidence gate.\n\nУникальная часть B: promotion coverage.\n")
        res2 = dc.analyze([q1, q2], root=base, thr=0.4)
        assert res2["n_units"] >= 4, "H1/абзацы должны извлекаться: %s" % res2
        assert len(res2["consensus"]) >= 1, "ожидался consensus из абзацев: %s" % res2

        # --- gate: "одна идея — разные слова" — лексика ПРОВАЛИВАЕТ, --semantic ЛОВИТ ---
        s1 = os.path.join(base, "semA.md")
        s2 = os.path.join(base, "semB.md")
        with open(s1, "w", encoding="utf-8", newline="\n") as f:
            f.write("# A\n\n- каждый агент работает в изолированном worktree\n")
        with open(s2, "w", encoding="utf-8", newline="\n") as f:
            f.write("# B\n\n- параллельные ветки не пересекаются на диске\n")

        # 1) lexical mode PROVABLY fails: zero token overlap -> 0 consensus at any thr
        lex = dc.analyze([s1, s2], root=base, thr=0.3)
        assert len(lex["consensus"]) == 0, "лексика должна дать 0 consensus (слепое пятно): %d" % len(lex["consensus"])

        # 2) stub the agent: it conceptually groups the two paraphrases by unit-id
        unit_ids = [u["id"] for u in dc.units(s1, base) + dc.units(s2, base)]
        assert len(unit_ids) == 2, "ожидалось 2 unit: %s" % unit_ids
        orig_run_agent = dc._run_agent
        dc._run_agent = lambda payload: json.dumps({
            "consensus": [{"ids": unit_ids, "rationale": "изоляция worktree = непересечение веток на диске"}],
            "divergences": []})
        try:
            sem = dc.analyze_semantic([s1, s2], root=base)
        finally:
            dc._run_agent = orig_run_agent

        # 3) --semantic CATCHES it: 1 consensus spanning both docs, carrying rationale
        assert len(sem["consensus"]) == 1, "--semantic должен поймать парафраз: %d" % len(sem["consensus"])
        c = sem["consensus"][0]
        assert len({u["doc"] for u in c["members"]}) == 2, "консенсус через оба дока"
        assert c["rationale"], "семантический пункт несёт rationale (оба свидетельства)"

        # 4) semantic render is status: proposed, never auto-accepted
        stxt = dc.render(sem)
        assert "status: proposed" in stxt and "Консенсус" in stxt, "семантический отчёт proposed+консенсус"

        # 5) CLI budget guard fails before agent fan-out when the residue needs > budget calls
        p = subprocess.run([
            sys.executable, os.path.join(HERE, "doc_consensus.py"), "report", "--semantic",
            "--semantic-budget", "0", "--files", s1, s2,
        ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        assert p.returncode == 1 and "semantic budget exceeded" in p.stdout, (p.returncode, p.stdout, p.stderr)

        # 6) CLI --semantic uses DOC_CONSENSUS_AGENT subprocess seam and writes proposed output
        stub = os.path.join(base, "agent_stub.py")
        with open(stub, "w", encoding="utf-8", newline="\n") as f:
            f.write("import json, sys\n"
                    "raw = sys.stdin.read()\n"
                    "payload = raw.split('Units (JSON):', 1)[-1].strip()\n"
                    "items = json.loads(payload) if payload else []\n"
                    "ids = [x['id'] for x in items]\n"
                    "print(json.dumps({'consensus':[{'ids': ids, 'rationale':'stub semantic match'}], 'divergences': []}, ensure_ascii=False))\n")
        sem_out = os.path.join(base, "semantic.md")
        env = os.environ.copy()
        env["DOC_CONSENSUS_AGENT"] = '"%s" "%s"' % (sys.executable, stub)
        p = subprocess.run([
            sys.executable, os.path.join(HERE, "doc_consensus.py"), "report", "--semantic",
            "--semantic-budget", "1", "--files", s1, s2, "--out", sem_out,
        ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
           stdin=subprocess.DEVNULL, env=env)
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        with open(sem_out, encoding="utf-8") as f:
            rendered_sem = f.read()
        assert "status: proposed" in rendered_sem and "stub semantic match" in rendered_sem, rendered_sem

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
