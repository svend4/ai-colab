#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inf_accuracy.py  —  the accuracy half of the falsification.

The mechanical harness (inf_falsify.py) showed the substrate feeds far less
context. The open question it could not answer without a model: does the slim
context still produce a CORRECT answer, or does reference-not-repeat quietly
drop a load-bearing argument?

This makes that falsifiable by construction. We plant one required argument
(the Rueckausnahme for ueberoertlicher Bedarf) in a block whose Q6 address sits
OUTSIDE agent A's territory, and we link A1 -> EX1 so the reference graph can
reach it. Then we grade three context regimes against a rubric of required
arguments:

  naive            full corpus
  territory        only Hamming<=radius of the agent anchor (excludes EX1)
  territory+ref    territory plus blocks reachable by following links (adds EX1)

A faithful MOCK model lets the whole apparatus run deterministically: the answer
contains a rubric argument iff its source block was in the supplied context, so
the grader detects exactly which arguments each regime can and cannot support.
--llama swaps the mock for a real local llama-server, turning this into a real
accuracy measurement on your own model.

The crisp claim under test: reference-not-repeat preserves correctness IFF the
reference graph reaches every load-bearing fact. The grader detects when it does
not.

Needs infon.py + inf_collab.py + inf_falsify.py alongside. Stdlib only.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Set

import inf_collab
from inf_falsify import ham, toks

ANCHOR_A = "-+--+-"

# explicit, reproducible corpus (so territory math is legible) --------------
CORPUS: List[Dict[str, Any]] = [
    {"id": "A1", "type": "rule", "q6": "-+--+-", "rel": "zustaendig", "pol": "+", "args": [],
     "links": [{"kind": "elaborate", "target": "A2", "label": "begruendet"},
               {"kind": "elaborate", "target": "P1", "label": "prinzip"},
               {"kind": "exception", "target": "EX1", "label": "rueckausnahme"}],
     "body": "\u00d6rtliche Zust\u00e4ndigkeit liegt grunds\u00e4tzlich beim \u00f6rtlichen Tr\u00e4ger nach \u00a710 Abs. 2 S\u00e4chsAGSGB; ma\u00dfgeblich ist der Zeitpunkt der Antragstellung."},
    {"id": "A2", "type": "evidence", "q6": "-+--++", "pol": "+", "args": [], "links": [],
     "body": "Die Zust\u00e4ndigkeit folgt aus dem gew\u00f6hnlichen Aufenthalt (Hauptwohnsitz)."},
    {"id": "P1", "type": "prinzip", "q6": "-+--+-", "pol": "+", "args": [], "links": [],
     "body": "Der gew\u00f6hnliche Aufenthalt bestimmt die \u00f6rtliche Zust\u00e4ndigkeit."},
    {"id": "B1", "type": "claim", "q6": "+-+-+-", "pol": "+", "args": [], "links": [],
     "body": "Stundensatz im Arbeitgebermodell = TV\u00f6D-P + BGW-Umlage + PflegeArbbV-Zuschl\u00e4ge."},
    # PLANTED load-bearing fact: q6 far from anchor A (Hamming 4) -> outside territory
    {"id": "EX1", "type": "exception", "q6": "++++++", "pol": "+", "args": [], "links": [],
     "body": "Bei \u00fcber\u00f6rtlichem Eingliederungshilfe-Bedarf greift die R\u00fcckausnahme zugunsten des \u00fcber\u00f6rtlichen Tr\u00e4gers."},
]

# rubric: required arguments, each tied to a source block + detection keywords
RUBRIC = [
    {"claim": "\u00f6rtliche Zust\u00e4ndigkeit / \u00a710 II", "source": "A1", "kw": ["\u00f6rtlich", "\u00a710"]},
    {"claim": "gew\u00f6hnlicher Aufenthalt ma\u00dfgeblich", "source": "A2", "kw": ["gew\u00f6hnlich"]},
    {"claim": "R\u00fcckausnahme bei \u00fcber\u00f6rtlichem Bedarf", "source": "EX1", "kw": ["r\u00fcckausnahme", "\u00fcber\u00f6rtlich"]},
    {"claim": "Zeitpunkt der Antragstellung", "source": "A1", "kw": ["antragstellung"]},
]

TASK = ("Entwirf eine kurze Stellungnahme zur \u00f6rtlichen Zust\u00e4ndigkeit nach "
        "\u00a710 Abs.2 S\u00e4chsAGSGB. Ber\u00fccksichtige alle einschl\u00e4gigen Gesichtspunkte aus dem Kontext.")


def by_id(bid: str) -> Dict[str, Any]:
    return next(b for b in CORPUS if b["id"] == bid)


def territory(anchor: str, radius: int) -> List[Dict[str, Any]]:
    return [b for b in CORPUS if ham(b["q6"], anchor) <= radius]


def with_references(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids: Set[str] = {b["id"] for b in blocks}
    for b in list(blocks):
        for l in b.get("links", []):
            ids.add(l["target"])            # 1-hop reference closure
    return [b for b in CORPUS if b["id"] in ids]


def grade(answer: str) -> Dict[str, Any]:
    low = answer.lower()
    covered, missing = [], []
    for item in RUBRIC:
        if any(k.lower() in low for k in item["kw"]):
            covered.append(item["claim"])
        else:
            missing.append(item["claim"])
    return {"covered": covered, "missing": missing,
            "score": f"{len(covered)}/{len(RUBRIC)}"}


def mock_answer(ctx_ids: Set[str]) -> str:
    """A faithful model: states what the supplied context supports, nothing more."""
    return " ".join(b["body"] for b in CORPUS if b["id"] in ctx_ids)


def regimes(radius: int):
    terr = territory(ANCHOR_A, radius)
    terr_ref = with_references(terr)
    return {
        "naive": CORPUS,
        "territory": terr,
        "territory+ref": terr_ref,
    }


def run(use_llama: bool, endpoint: str, model: str, radius: int) -> None:
    regs = regimes(radius)
    print(f"agent A territory radius {radius}; planted fact EX1 (q6 {by_id('EX1')['q6']}, "
          f"Hamming {ham(by_id('EX1')['q6'], ANCHOR_A)} from anchor) is OUTSIDE the territory.\n")
    results = {}
    for name, blocks in regs.items():
        ctx_ids = {b["id"] for b in blocks}
        ctx_text = inf_collab.to_inf(blocks)
        if use_llama:
            prompt = f"{TASK}\n\nKONTEXT:\n{ctx_text}\n\nAntworte als kurze Stellungnahme."
            try:
                answer = inf_collab.call_llama(prompt, endpoint, model)
            except Exception as ex:
                answer = f"[llama-server unreachable: {ex}]"
        else:
            answer = mock_answer(ctx_ids)
        g = grade(answer)
        results[name] = g
        print(f"  {name:<14} ctx ~{toks(ctx_text):>4} tok  blocks {sorted(ctx_ids)}")
        print(f"  {'':<14} score {g['score']}"
              + (f"   MISSING: {g['missing']}" if g['missing'] else "   (all arguments present)"))
        print()

    print("VERDICT")
    n, t, tr = results["naive"], results["territory"], results["territory+ref"]
    lost = set(n["covered"]) - set(t["covered"])
    recovered = set(tr["covered"]) - set(t["covered"])
    if lost:
        print(f"  territory-only DROPPED: {sorted(lost)}")
        print(f"  - this is the failure mode: a load-bearing fact lived outside the partition,")
        print(f"    so reference-not-repeat without the reference loses the argument.")
        if recovered >= lost:
            print(f"  following the reference RECOVERED: {sorted(recovered)} \u2192 correctness restored.")
            print(f"  \u2192 reference-not-repeat preserves correctness IFF the reference graph reaches")
            print(f"    every load-bearing fact. Here A1 \u21d2 EX1 closes the gap.")
        else:
            print(f"  references did NOT recover it \u2192 the partition is unsafe for this task.")
    else:
        print(f"  territory-only lost nothing on this corpus \u2192 partition already covered the task.")

    if not use_llama:
        # built-in falsifiable self-check of the apparatus
        assert t["missing"], "expected territory-only to miss the planted argument"
        assert "R\u00fcckausnahme bei \u00fcber\u00f6rtlichem Bedarf" in t["missing"]
        assert not tr["missing"], "expected territory+ref to be complete"
        assert not n["missing"], "expected naive to be complete"
        print("\n  self-check \u2713  (mock is faithful; naive 4/4, territory drops the planted")
        print("  argument exactly, reference recovers it). Run --llama for a real model.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="inf_accuracy")
    p.add_argument("--llama", action="store_true")
    p.add_argument("--endpoint", default="http://localhost:8080/v1")
    p.add_argument("--model", default="local-gguf")
    p.add_argument("--radius", type=int, default=1)
    a = p.parse_args(argv)
    run(a.llama, a.endpoint, a.model, a.radius)


if __name__ == "__main__":
    main()
