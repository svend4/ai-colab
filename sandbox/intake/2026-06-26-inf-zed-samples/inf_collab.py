#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inf_collab.py  —  offline multi-agent collaboration over an .inf graph.

Two replicas (agents) edit the SAME blocks concurrently while offline, then
merge via the CRDT in inf_crdt.py and converge — the thing the infon-board
MVP could not do (it avoided collisions by partitioning agents into disjoint
Q6 territories). Agents run on a LOCAL llama-server (llama.cpp /
OpenAI-compatible) with an offline synthetic fallback so the convergence
itself is testable without a model.

Usage:
    python inf_collab.py demo [--source normenkg_slice.json]
                              [--llama] [--endpoint http://localhost:8080/v1]
                              [--model my-gguf]
    python inf_collab.py laws            # check CRDT merge laws on a sample

Needs infon.py alongside (for .inf parsing and node-link import). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from typing import Any, Dict, List, Optional

import inf_crdt as crdt

try:
    import infon
except Exception:  # pragma: no cover
    infon = None

ARROW = {"elaborate": "\u2192", "exception": "\u21d2", "context": "\u00b7", "entails": "\u22a2"}
DEFAULT_ARROW = ARROW["elaborate"]
CHECK = "\u2713"
CROSS = "\u2717"


# --------------------------------------------------------------------------- #
# .inf I/O (parsing reused from infon.py; serialiser local)
# --------------------------------------------------------------------------- #
def graph_to_blocks(graph) -> List[Dict[str, Any]]:
    out = []
    for bid in graph.order:
        b = graph.blocks[bid]
        d: Dict[str, Any] = {
            "id": b.id, "type": b.type, "q6": b.q6, "rel": b.rel, "pol": b.pol,
            "args": list(b.args),
            "body": b.body,
            "links": [{"kind": l.kind, "target": l.target, "label": l.label} for l in b.links],
        }
        lvl = b.attrs.get("level")
        if lvl is not None:
            try:
                d["level"] = int(lvl)
            except ValueError:
                pass
        out.append(d)
    return out


def to_inf(blocks: List[Dict[str, Any]]) -> str:
    parts = []
    for b in blocks:
        h = "\u221e " + b["id"]
        if b.get("type"):
            h += f"  type:{b['type']}"
        if b.get("q6"):
            h += f"  q6:{b['q6']}"
        lines = [h]
        if b.get("level") is not None:
            lines.append(f"  level: {b['level']}")
        if b.get("rel"):
            lines.append(f"  rel:   {b['rel']}")
        if b.get("args"):
            lines.append("  args:  [" + ", ".join(b["args"]) + "]")
        if b.get("pol") == "-":
            lines.append("  pol:   -")
        if b.get("links"):
            lines.append("  links: " + "  ".join(
                f"{ARROW.get(l['kind'], DEFAULT_ARROW)}{l['target']}" + (f"({l['label']})" if l.get("label") else "")
                for l in b["links"]))
        lines.append("  \u2500\u2500")
        lines.append("  " + (b.get("body") or "").replace("\n", "\n  "))
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"


def get_block(blocks: List[Dict[str, Any]], bid: str) -> Optional[Dict[str, Any]]:
    for b in blocks:
        if b["id"] == bid:
            return b
    return None


# --------------------------------------------------------------------------- #
# agent backend: local llama-server, with offline synthetic fallback
# --------------------------------------------------------------------------- #
def call_llama(prompt: str, endpoint: str, model: str) -> str:
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3, "max_tokens": 700,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def parse_agent_blocks(text: str, label: str) -> List[Dict[str, Any]]:
    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        s, e = clean.find("["), clean.rfind("]")
        arr = json.loads(clean[s:e + 1] if s >= 0 else clean)
        if not isinstance(arr, list):
            return []
    except Exception:
        return []
    out = []
    for i, p in enumerate(arr[:3]):
        bid = str(p.get("id") or f"{label}.k{i + 1}")
        if not bid.startswith(label + "."):
            bid = f"{label}.{bid}"
        out.append({
            "id": bid, "type": p.get("type", "claim"), "q6": p.get("q6"),
            "rel": p.get("rel"), "args": p.get("args") or [], "pol": p.get("pol", "+"),
            "links": [], "body": str(p.get("body", "")),
        })
    return out


# offline synthetic contributions (deterministic; used when --llama is off or fails)
SYNTH = {
    "A": [{"id": "A.k1", "type": "evidence", "q6": "-+--++", "rel": "belegt",
           "body": "Beleg A: Hauptwohnsitz laut Meldebescheinigung begr\u00fcndet die \u00f6rtliche Zust\u00e4ndigkeit."}],
    "B": [{"id": "B.k1", "type": "evidence", "q6": "+-+-++", "rel": "berechnet",
           "body": "Beleg B: Stundensatz aus TV\u00f6D-P-Entgeltgruppe plus BGW-Umlage und PflegeArbbV-Zuschlag."}],
}


def agent_contribution(label: str, facet: str, task: str, ctx: str,
                       use_llama: bool, endpoint: str, model: str) -> List[Dict[str, Any]]:
    if not use_llama:
        return [dict(b) for b in SYNTH[label]]
    prompt = (
        f'You are sub-agent {label} on a shared .inf legal knowledge graph.\n'
        f'TASK: {task}\nYOUR FACET: {facet}\n\nEXISTING BLOCKS:\n{ctx}\n\n'
        f'Return ONLY a JSON array of 1-2 new blocks, no prose, no code fences. '
        f'Each: {{"id":"{label}.<short>","type":"evidence|claim|rule","q6":"<6 chars + or ->",'
        f'"rel":"<relation>","body":"<1 sentence, German legal register>"}}'
    )
    try:
        text = call_llama(prompt, endpoint, model)
        blocks = parse_agent_blocks(text, label)
        if blocks:
            return blocks
    except Exception as ex:
        print(f"  [agent {label}] llama-server unreachable ({ex}); using offline fallback", file=sys.stderr)
    return [dict(b) for b in SYNTH[label]]


# --------------------------------------------------------------------------- #
# seed loading
# --------------------------------------------------------------------------- #
SEED_INF = """\u221e A1  type:decision  q6:-+--+-
  level: 1
  rel:   zustaendig
  args:  [Traeger-oertlich, \u00a710-II-SaechsAGSGB]
  links: \u2192A2(begruendet)
  \u2500\u2500
  \u00d6rtliche Zust\u00e4ndigkeit liegt beim \u00f6rtlichen Tr\u00e4ger nach \u00a710 Abs. 2 S\u00e4chsAGSGB.

\u221e A2  type:evidence  q6:-+--++
  level: 2
  \u2500\u2500
  Die \u00f6rtliche Zust\u00e4ndigkeit folgt aus dem gew\u00f6hnlichen Aufenthalt.

\u221e B1  type:claim  q6:+-+-+-
  level: 1
  rel:   stundensatz
  \u2500\u2500
  Stundensatz im Arbeitgebermodell = TV\u00f6D-P + BGW-Umlage + PflegeArbbV-Zuschl\u00e4ge.
"""


def load_seed_blocks(source: Optional[str]) -> List[Dict[str, Any]]:
    if source and infon:
        with open(source, "r", encoding="utf-8") as fh:
            txt = fh.read()
        if source.endswith(".json"):
            txt = infon.from_nodelink(json.loads(txt))   # NormenKG node-link -> .inf
        return graph_to_blocks(infon.parse(txt))
    if infon:
        return graph_to_blocks(infon.parse(SEED_INF))
    raise SystemExit("infon.py is required alongside inf_collab.py")


# --------------------------------------------------------------------------- #
# the demo: two replicas edit the SAME block offline, then converge
# --------------------------------------------------------------------------- #
def demo(source: Optional[str], use_llama: bool, endpoint: str, model: str) -> None:
    task = "Stellungnahme: \u00f6rtliche Zust\u00e4ndigkeit (\u00a710 II) gegen Stundensatz absichern."
    base_blocks = load_seed_blocks(source)
    shared_id = base_blocks[0]["id"]  # the block BOTH replicas will edit (A1)
    ctx = "\n".join(f"{b['id']} [{b.get('type')}] :: {(b.get('body') or '')[:60]}" for b in base_blocks)

    base = crdt.from_blocks(base_blocks, rep="seed")
    repA = base.clone("A")
    repB = base.clone("B")

    print(f"= base: {len(base_blocks)} blocks; both replicas will concurrently edit '{shared_id}'\n")
    print(f"  base body of {shared_id}:\n    {get_block(base.to_blocks(), shared_id)['body']}\n")

    # ---- concurrent ops while OFFLINE (no merge between them) ----
    # 1) same block, same field, concurrent -> CRDT must pick a deterministic winner
    repA.edit_body(shared_id, f"[A] {get_block(base.to_blocks(), shared_id)['body']} "
                              f"Pr\u00e4zisierung A: ma\u00dfgeblich ist der Zeitpunkt der Antragstellung.")
    repB.edit_body(shared_id, f"[B] {get_block(base.to_blocks(), shared_id)['body']} "
                              f"Pr\u00e4zisierung B: bei Wohnsitzwechsel gilt der letzte gew\u00f6hnliche Aufenthalt.")
    # 2) both add a link from the shared block -> OR-Set must keep BOTH
    a_new = agent_contribution("A", "Normen, Zust\u00e4ndigkeit", task, ctx, use_llama, endpoint, model)
    b_new = agent_contribution("B", "Belege, Berechnung", task, ctx, use_llama, endpoint, model)
    for blk in a_new:
        repA.add_block(blk)
        repA.add_link(shared_id, "elaborate", blk["id"], "A-Beleg")
    for blk in b_new:
        repB.add_block(blk)
        repB.add_link(shared_id, "exception", blk["id"], "B-Beleg")

    # ---- divergent state (offline) ----
    print("= DIVERGENT (offline, before sync):")
    print(f"  A sees {shared_id}.body: {get_block(repA.to_blocks(), shared_id)['body'][:72]}\u2026")
    print(f"  B sees {shared_id}.body: {get_block(repB.to_blocks(), shared_id)['body'][:72]}\u2026")
    print(f"  A added: {[b['id'] for b in a_new]} | B added: {[b['id'] for b in b_new]}\n")

    # ---- merge both orders; must converge ----
    merged_AB = repA.clone().merge(repB)
    merged_BA = repB.clone().merge(repA)
    ok = crdt.converged(merged_AB, merged_BA)
    print(f"= MERGE: A\u25c1B vs B\u25c1A converge? {(CHECK + ' yes (order-independent)') if ok else (CROSS + ' NO')}\n")
    if not ok:
        sys.exit(1)

    merged = merged_AB
    mblocks = merged.to_blocks()
    sb = get_block(mblocks, shared_id)
    print(f"= RESOLVED {shared_id}:")
    print(f"  body  -> {sb['body']}")
    print(f"  winner: {merged.winner_reason(shared_id, 'body')}  "
          f"(equal ts \u2192 replica id breaks the tie; B > A)")
    print(f"  links -> {[(l['kind'], l['target']) for l in sb.get('links', [])]}  "
          f"(both agents' links survive via OR-Set)\n")

    print("= MERGED .inf (offline collaboration result):\n")
    print(to_inf(mblocks))
    print("\u2500" * 60)
    print("Concurrent edits to the SAME block converged with no server and no")
    print("partitioning. The infon-board MVP forbade this case by assigning agents")
    print("disjoint Q6 territories; the CRDT permits it and merges deterministically.")


# --------------------------------------------------------------------------- #
# CRDT merge laws (quick check)
# --------------------------------------------------------------------------- #
def laws() -> None:
    base = crdt.from_blocks(load_seed_blocks(None), "seed")
    a, b, c = base.clone("A"), base.clone("B"), base.clone("C")
    a.edit_body("A1", "A-edit"); a.add_link("A1", "elaborate", "x", "a")
    b.edit_body("A1", "B-edit"); b.add_link("A1", "exception", "y", "b")
    c.add_block({"id": "C.k", "type": "claim", "q6": "++++++", "body": "C-only"})

    comm = crdt.converged(a.clone().merge(b), b.clone().merge(a))
    idem = crdt.converged(a.clone().merge(a), a)
    left = a.clone().merge(b.clone().merge(c))
    right = a.clone().merge(b).merge(c)
    assoc = crdt.converged(left, right)
    print(f"commutative  merge(a,b)==merge(b,a) : {CHECK if comm else CROSS}")
    print(f"idempotent   merge(a,a)==a          : {CHECK if idem else CROSS}")
    print(f"associative  a\u2218(b\u2218c)==(a\u2218b)\u2218c       : {CHECK if assoc else CROSS}")
    print("\nThese three laws are exactly Strong Eventual Consistency: replicas that")
    print("have seen the same updates converge regardless of order or duplication.")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="inf_collab")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="two-replica offline collaboration")
    d.add_argument("--source", default=None, help=".inf or networkx node-link .json (e.g. NormenKG)")
    d.add_argument("--llama", action="store_true", help="use a local llama-server for agents")
    d.add_argument("--endpoint", default="http://localhost:8080/v1", help="OpenAI-compatible base URL")
    d.add_argument("--model", default="local-gguf", help="model name for the server")
    sub.add_parser("laws", help="check CRDT merge laws")
    args = p.parse_args(argv)
    if args.cmd == "demo":
        demo(args.source, args.llama, args.endpoint, args.model)
    elif args.cmd == "laws":
        laws()


if __name__ == "__main__":
    main()
