#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inf_crdt.py  —  a minimal state-based CRDT (CvRDT) over .inf blocks.

This is the substrate that lets several offline replicas (humans / agents)
edit the SAME .inf graph concurrently and converge without a server — the
real answer to the concurrency fork the infon-board MVP dodged by partitioning
agents into disjoint Q6 territories.

Design (same convergence guarantee as Automerge, simplified to the block-map
case so it stays zero-dependency and runs on Termux):

  - scalar block fields (type, q6, rel, pol, body, level)  -> LWW-Register
        value tagged with a Lamport timestamp + replica id; merge keeps the
        max (ts, replica). Total order on (ts, replica) => deterministic winner.
  - list fields (links, args)                              -> OR-Set
        add-wins set with unique tags + tombstones; concurrent adds BOTH
        survive, removes are observed-remove. (No lost links on merge.)
  - block membership                                        -> OR-Set of ids

merge() is a join on a semilattice => commutative, associative, idempotent
=> Strong Eventual Consistency: any replicas that have seen the same updates
converge to the same state, regardless of order.

For full concurrent *character-level* merge inside a body you'd swap the body
LWW-Register for a sequence CRDT (Yjs/Automerge RGA). For block-structured
legal knowledge, field-level LWW + link OR-Set is the right and simple choice.

Zero dependencies. Python 3.8+. Stdlib only.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

SCALAR_FIELDS = ("type", "q6", "rel", "pol", "body", "level")
SET_FIELDS = ("links", "args")


# --------------------------------------------------------------------------- #
# LWW-Register
# --------------------------------------------------------------------------- #
@dataclass
class LWW:
    value: Any
    ts: int           # Lamport timestamp
    rep: str          # replica id (tiebreak)

    def _key(self):
        return (self.ts, self.rep)

    @staticmethod
    def merge(a: "LWW", b: "LWW") -> "LWW":
        if a is None:
            return b
        if b is None:
            return a
        return a if a._key() >= b._key() else b


# --------------------------------------------------------------------------- #
# OR-Set (observed-remove set, add-wins)
# --------------------------------------------------------------------------- #
@dataclass
class ORSet:
    adds: Dict[Any, Set[str]] = field(default_factory=dict)   # element -> set of tags
    tombs: Set[str] = field(default_factory=set)              # removed tags

    def add(self, el: Any, tag: str) -> None:
        self.adds.setdefault(el, set()).add(tag)

    def remove(self, el: Any) -> None:
        for t in self.adds.get(el, set()):
            self.tombs.add(t)

    def values(self) -> List[Any]:
        out = []
        for el, tags in self.adds.items():
            if tags - self.tombs:
                out.append(el)
        return out

    @staticmethod
    def merge(a: "ORSet", b: "ORSet") -> "ORSet":
        a = a or ORSet()
        b = b or ORSet()
        out = ORSet()
        for el, tags in a.adds.items():
            out.adds.setdefault(el, set()).update(tags)
        for el, tags in b.adds.items():
            out.adds.setdefault(el, set()).update(tags)
        out.tombs = set(a.tombs) | set(b.tombs)
        return out


# --------------------------------------------------------------------------- #
# Document
# --------------------------------------------------------------------------- #
class Doc:
    def __init__(self, rep: str = "0"):
        self.rep = rep
        self.clock = 0
        self.members = ORSet()                       # block ids present
        self.regs: Dict[Tuple[str, str], LWW] = {}   # (id, field) -> LWW
        self.sets: Dict[Tuple[str, str], ORSet] = {} # (id, field) -> ORSet

    # ---- local ops (each ticks the Lamport clock) ----
    def _tick(self) -> int:
        self.clock += 1
        return self.clock

    def _tag(self) -> str:
        return f"{self.rep}:{self.clock}"

    def put(self, bid: str, fieldname: str, value: Any) -> None:
        t = self._tick()
        self.members.add(bid, f"{bid}@{self.rep}:{t}")
        self.regs[(bid, fieldname)] = LWW(value, t, self.rep)

    def add_set(self, bid: str, fieldname: str, element: Any) -> None:
        t = self._tick()
        self.members.add(bid, f"{bid}@{self.rep}:{t}")
        self.sets.setdefault((bid, fieldname), ORSet()).add(element, self._tag())

    def remove_set(self, bid: str, fieldname: str, element: Any) -> None:
        self._tick()
        self.sets.setdefault((bid, fieldname), ORSet()).remove(element)

    def add_block(self, b: Dict[str, Any]) -> None:
        bid = b["id"]
        for f in SCALAR_FIELDS:
            if b.get(f) is not None:
                self.put(bid, f, b[f])
        for l in (b.get("links") or []):
            self.add_set(bid, "links", _link_tuple(l))
        for a in (b.get("args") or []):
            self.add_set(bid, "args", a)
        # ensure membership even for an empty block
        t = self._tick()
        self.members.add(bid, f"{bid}@{self.rep}:{t}")

    def edit_body(self, bid: str, value: str) -> None:
        self.put(bid, "body", value)

    def add_link(self, bid: str, kind: str, target: str, label: Optional[str] = None) -> None:
        self.add_set(bid, "links", (kind, target, label or ""))

    def remove_block(self, bid: str) -> None:
        self.members.remove(bid)

    # ---- merge (state-based join) ----
    def merge(self, other: "Doc") -> "Doc":
        self.members = ORSet.merge(self.members, other.members)
        for k, v in other.regs.items():
            self.regs[k] = LWW.merge(self.regs.get(k), v)
        for k, v in other.sets.items():
            self.sets[k] = ORSet.merge(self.sets.get(k), v)
        self.clock = max(self.clock, other.clock)
        return self

    def clone(self, rep: Optional[str] = None) -> "Doc":
        d = copy.deepcopy(self)
        if rep is not None:
            d.rep = rep
        return d

    # ---- materialise ----
    def block_ids(self) -> List[str]:
        # an id is present if its membership tags survive, OR it has live data
        live = set(_id_of(tag) for tag in _surviving(self.members))
        live |= {bid for (bid, _f) in self.regs}
        live |= {bid for (bid, _f) in self.sets if self.sets[(bid, _f)].values()}
        return sorted(live)

    def to_blocks(self) -> List[Dict[str, Any]]:
        out = []
        for bid in self.block_ids():
            b: Dict[str, Any] = {"id": bid}
            for f in SCALAR_FIELDS:
                r = self.regs.get((bid, f))
                if r is not None:
                    b[f] = r.value
            links = self.sets.get((bid, "links"))
            if links:
                b["links"] = [{"kind": k, "target": t, "label": (lab or None)}
                              for (k, t, lab) in sorted(links.values())]
            args = self.sets.get((bid, "args"))
            if args:
                b["args"] = sorted(args.values())
            b.setdefault("pol", "+")
            out.append(b)
        return out

    def canonical(self) -> str:
        """Deterministic snapshot for convergence checks."""
        return json.dumps(self.to_blocks(), sort_keys=True, ensure_ascii=False)

    def winner_reason(self, bid: str, fieldname: str) -> str:
        r = self.regs.get((bid, fieldname))
        return f"{fieldname} of {bid}: replica {r.rep} @ ts {r.ts}" if r else "—"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _link_tuple(l: Any) -> Tuple[str, str, str]:
    if isinstance(l, dict):
        return (l.get("kind", "context"), l.get("target", ""), l.get("label") or "")
    if isinstance(l, (list, tuple)):
        return (l[0], l[1], (l[2] if len(l) > 2 else "") or "")
    return ("context", str(l), "")


def _surviving(s: ORSet) -> List[str]:
    return s.values()


def _id_of(tag: str) -> str:
    # membership tags look like "<id>@<rep>:<n>"
    return tag.split("@", 1)[0]


def from_blocks(blocks: List[Dict[str, Any]], rep: str = "0") -> Doc:
    d = Doc(rep)
    for b in blocks:
        d.add_block(b)
    return d


def converged(*docs: Doc) -> bool:
    canon = [d.canonical() for d in docs]
    return all(c == canon[0] for c in canon)
