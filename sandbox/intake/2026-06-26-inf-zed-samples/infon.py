#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
infon.py — reference parser & tooling for the .inf block format.

The .inf format is a thin plaintext envelope over an infon graph:
each block is a typed unit of information (relation + args + polarity),
carrying a Q6 semantic address in {-1,+1}^6 and typed links to other blocks.

It is optimised for MACHINE clustering and traversal, not human prettiness:
  - blocks are greppable (each starts at column 0 with the block sigil)
  - the Q6 address makes clustering a Hamming-distance op (no re-embedding)
  - typed links form the "domino" graph an agent walks instead of full-scan
  - the body stays Markdown-ish, so the model still writes what it is good at

Zero dependencies. Python 3.8+. Stdlib only.

Usage:
    python infon.py view       FILE.inf [--no-color]
    python infon.py tree       FILE.inf ID [--kind elaborate] [--depth N]
    python infon.py clusters   FILE.inf [--r N]
    python infon.py validate   FILE.inf
    python infon.py stats      FILE.inf
    python infon.py from-nodelink FILE.json [-o OUT.inf]

See SPEC.md for the full grammar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Grammar constants
# --------------------------------------------------------------------------- #

BLOCK_SIGILS = ("\u221e", "@@")          # ∞  (canonical) and @@ (ASCII alias)
BODY_SEPARATORS = ("\u2500\u2500", "---")  # ──  and ---
COMMENT_PREFIX = "#"

# arrow glyph -> edge kind ; ASCII aliases included
ARROW_KIND = {
    "\u2192": "elaborate",   # →
    "->": "elaborate",
    "\u21d2": "exception",   # ⇒
    "=>": "exception",
    "\u00b7": "context",     # ·
    "..": "context",
    "\u22a2": "entails",     # ⊢
    "|-": "entails",
}
# longest-first so multi-char ASCII aliases match before single glyphs
_ARROWS = sorted(ARROW_KIND, key=len, reverse=True)

POL_TRUE = {"+", "1", "true", "yes", "holds"}
POL_FALSE = {"-", "0", "false", "no"}

Q6_RE = re.compile(r"^[+\-]{6}$")


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

@dataclass
class Link:
    kind: str                 # elaborate | exception | context | entails
    target: str               # target block id
    label: Optional[str] = None  # parenthetical relation label


@dataclass
class Block:
    id: str
    type: Optional[str] = None
    q6: Optional[str] = None              # e.g. "-+--+-"
    rel: Optional[str] = None             # infon relation name
    args: List[str] = field(default_factory=list)
    pol: str = "+"                        # "+" (holds) or "-" (does not hold)
    links: List[Link] = field(default_factory=list)
    attrs: Dict[str, str] = field(default_factory=dict)  # any non-reserved keys
    body: str = ""
    line: int = 0                         # 1-based source line of the header


@dataclass
class Graph:
    blocks: Dict[str, Block] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)        # source order of ids
    warnings: List[str] = field(default_factory=list)

    def __iter__(self):
        for bid in self.order:
            yield self.blocks[bid]

    def __len__(self):
        return len(self.order)


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

def _strip_sigil(line: str) -> Optional[str]:
    """Return the remainder after a block sigil, or None if not a block start."""
    for sig in BLOCK_SIGILS:
        if line.startswith(sig):
            return line[len(sig):].lstrip()
    return None


def _is_separator(line: str) -> bool:
    s = line.strip()
    return s in BODY_SEPARATORS


def _parse_inline_attrs(rest: str) -> Tuple[str, Dict[str, str]]:
    """Header tail: first token is the id; remaining `k:v` tokens are attrs."""
    toks = rest.split()
    if not toks:
        return "", {}
    bid = toks[0]
    attrs: Dict[str, str] = {}
    for tok in toks[1:]:
        if ":" in tok:
            k, _, v = tok.partition(":")
            attrs[k.strip()] = v.strip()
    return bid, attrs


def _parse_args(value: str) -> List[str]:
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    return [a.strip() for a in v.split(",") if a.strip()]


def _parse_links(value: str) -> List[Link]:
    links: List[Link] = []
    for tok in value.split():
        kind = None
        rest = tok
        for arrow in _ARROWS:
            if tok.startswith(arrow):
                kind = ARROW_KIND[arrow]
                rest = tok[len(arrow):]
                break
        if kind is None:
            # bare id with no arrow -> default to context (weak association)
            kind = "context"
        label = None
        m = re.match(r"^([^(]+)(?:\(([^)]*)\))?$", rest)
        if m:
            target = m.group(1).strip()
            label = (m.group(2) or "").strip() or None
        else:
            target = rest.strip()
        if target:
            links.append(Link(kind=kind, target=target, label=label))
    return links


def _normalise_pol(value: str) -> str:
    v = value.strip().lower()
    if v in POL_TRUE:
        return "+"
    if v in POL_FALSE:
        return "-"
    return "+"  # default


def _finalise(block: Block, raw_attrs: Dict[str, str], graph: Graph) -> None:
    """Lift reserved keys out of raw_attrs into typed fields; keep the rest."""
    for key, val in raw_attrs.items():
        lk = key.lower()
        if lk == "type":
            block.type = val
        elif lk == "q6":
            if Q6_RE.match(val):
                block.q6 = val
            else:
                graph.warnings.append(
                    f"line {block.line}: block '{block.id}' has malformed q6 "
                    f"'{val}' (expected 6 chars of + / -)"
                )
        elif lk == "rel":
            block.rel = val
        elif lk == "args":
            block.args = _parse_args(val)
        elif lk == "pol":
            block.pol = _normalise_pol(val)
        elif lk == "links":
            block.links.extend(_parse_links(val))
        else:
            block.attrs[key] = val


def parse(text: str) -> Graph:
    """Parse .inf source into a Graph. Collects non-fatal issues in .warnings."""
    graph = Graph()
    lines = text.splitlines()

    cur: Optional[Block] = None
    cur_attrs: Dict[str, str] = {}
    in_body = False
    body_lines: List[str] = []

    def close():
        nonlocal cur, cur_attrs, in_body, body_lines
        if cur is None:
            return
        _finalise(cur, cur_attrs, graph)
        cur.body = textwrap.dedent("\n".join(body_lines)).strip("\n")
        if cur.id in graph.blocks:
            graph.warnings.append(
                f"line {cur.line}: duplicate block id '{cur.id}' "
                f"(previous definition kept)"
            )
        else:
            graph.blocks[cur.id] = cur
            graph.order.append(cur.id)
        cur, cur_attrs, in_body, body_lines = None, {}, False, []

    for i, raw in enumerate(lines, start=1):
        rest = _strip_sigil(raw)
        if rest is not None:                       # new block starts
            close()
            bid, inline = _parse_inline_attrs(rest)
            cur = Block(id=bid or f"_anon{i}", line=i)
            cur_attrs = dict(inline)
            in_body = False
            body_lines = []
            if not bid:
                graph.warnings.append(f"line {i}: block has no id (named '{cur.id}')")
            continue

        if cur is None:
            if raw.strip() and not raw.lstrip().startswith(COMMENT_PREFIX):
                graph.warnings.append(f"line {i}: text outside any block ignored")
            continue

        if in_body:
            body_lines.append(raw)
            continue

        if _is_separator(raw):
            in_body = True
            continue

        stripped = raw.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIX):
            continue

        # metadata line:  key: value   (space after colon required)
        m = re.match(r"^\s*([A-Za-z_][\w\-]*):\s+(.*)$", raw)
        if m:
            cur_attrs[m.group(1)] = m.group(2).strip()
        else:
            graph.warnings.append(
                f"line {i}: unrecognised line in block '{cur.id}' "
                f"(no ':' attr, no body separator yet): {stripped!r}"
            )

    close()
    return graph


# --------------------------------------------------------------------------- #
# Q6 semantics: Hamming distance and clustering
# --------------------------------------------------------------------------- #

def q6_vec(code: str) -> Tuple[int, ...]:
    """Map a q6 string to a tuple in {-1,+1}^6."""
    return tuple(1 if c == "+" else -1 for c in code)


def hamming(a: str, b: str) -> int:
    """Hamming distance between two equal-length q6 strings."""
    if len(a) != len(b):
        raise ValueError("q6 codes must be equal length")
    return sum(1 for x, y in zip(a, b) if x != y)


def cluster(graph: Graph, radius: int = 1) -> List[List[str]]:
    """
    Group blocks by Q6 proximity. Two blocks join the same cluster when their
    Hamming distance is <= radius (single-linkage / connected components).
    Blocks without a q6 are returned as their own singleton clusters at the end.
    """
    addressed = [b for b in graph if b.q6]
    unaddressed = [b.id for b in graph if not b.q6]

    parent = {b.id: b.id for b in addressed}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for i in range(len(addressed)):
        for j in range(i + 1, len(addressed)):
            if hamming(addressed[i].q6, addressed[j].q6) <= radius:
                union(addressed[i].id, addressed[j].id)

    groups: Dict[str, List[str]] = defaultdict(list)
    for b in addressed:
        groups[find(b.id)].append(b.id)

    clusters = sorted(groups.values(), key=lambda g: (-len(g), g[0]))
    clusters.extend([uid] for uid in unaddressed)
    return clusters


# --------------------------------------------------------------------------- #
# Graph traversal: the "domino" walk
# --------------------------------------------------------------------------- #

def walk(graph: Graph, start: str, kind: Optional[str] = None,
         max_depth: int = 6) -> List[Tuple[int, str, Optional[Link]]]:
    """
    Depth-first walk from `start` following links (optionally only one kind).
    Returns (depth, block_id, incoming_link) tuples in visit order.
    Cycle-safe.
    """
    out: List[Tuple[int, str, Optional[Link]]] = []
    seen = set()

    def visit(bid: str, depth: int, via: Optional[Link]):
        if depth > max_depth or bid in seen:
            if bid in seen:
                out.append((depth, bid, via))  # show the back-edge once, no recurse
            return
        seen.add(bid)
        out.append((depth, bid, via))
        block = graph.blocks.get(bid)
        if not block:
            return
        for link in block.links:
            if kind and link.kind != kind:
                continue
            visit(link.target, depth + 1, link)

    visit(start, 0, None)
    return out


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def validate(graph: Graph) -> List[str]:
    issues = list(graph.warnings)
    ids = set(graph.blocks)
    for b in graph:
        for link in b.links:
            if link.target not in ids:
                issues.append(
                    f"block '{b.id}': dangling link {link.kind} -> "
                    f"'{link.target}' (no such block)"
                )
        for a in b.args:
            # args may be external literals; only warn when they look like ids
            if a in ids:
                continue
        if not b.q6:
            issues.append(f"block '{b.id}': no q6 address (excluded from clustering)")
        if not b.body:
            issues.append(f"block '{b.id}': empty body")
    return issues


# --------------------------------------------------------------------------- #
# ANSI rendering (pure stdlib; auto-disables when not a TTY or --no-color)
# --------------------------------------------------------------------------- #

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


_USE_COLOR = True


def _c(code: str, text: str) -> str:
    return f"{code}{text}{C.RESET}" if _USE_COLOR else text


TYPE_COLOR = {
    "claim": C.CYAN,
    "evidence": C.GREEN,
    "definition": C.YELLOW,
    "context": C.DIM,
    "question": C.MAGENTA,
    "decision": C.BOLD + C.CYAN,
}

KIND_COLOR = {
    "elaborate": C.BLUE,
    "exception": C.RED,
    "context": C.DIM,
    "entails": C.MAGENTA,
}

KIND_GLYPH = {
    "elaborate": "\u2192",   # →
    "exception": "\u21d2",   # ⇒
    "context": "\u00b7",     # ·
    "entails": "\u22a2",     # ⊢
}


def _render_q6(code: Optional[str]) -> str:
    if not code:
        return _c(C.DIM, "······")
    out = []
    for ch in code:
        out.append(_c(C.GREEN, ch) if ch == "+" else _c(C.RED, ch))
    return "".join(out)


def render_block(b: Block) -> str:
    tcol = TYPE_COLOR.get((b.type or "").lower(), C.WHITE)
    head = (
        _c(C.BOLD, b.id)
        + "  " + _c(tcol, f"[{b.type or '—'}]")
        + "  q6:" + _render_q6(b.q6)
        + ("  " + _c(C.DIM, f"pol:{b.pol}") if b.pol == "-" else "")
    )
    lines = [head]
    if b.rel:
        argstr = ", ".join(b.args)
        lines.append("  " + _c(C.DIM, f"<<{b.rel}({argstr})>>"))
    for link in b.links:
        g = KIND_GLYPH.get(link.kind, "->")
        lab = f"({link.label})" if link.label else ""
        lines.append("  " + _c(KIND_COLOR.get(link.kind, C.WHITE),
                               f"{g} {link.target}{lab}"))
    for k, v in b.attrs.items():
        lines.append("  " + _c(C.DIM, f"{k}: {v}"))
    if b.body:
        for bl in b.body.splitlines():
            lines.append("  " + bl)
    return "\n".join(lines)


def cmd_view(graph: Graph) -> None:
    for i, b in enumerate(graph):
        if i:
            print()
        print(render_block(b))


def cmd_tree(graph: Graph, start: str, kind: Optional[str], depth: int) -> None:
    if start not in graph.blocks:
        print(_c(C.RED, f"no such block: {start}"), file=sys.stderr)
        sys.exit(1)
    steps = walk(graph, start, kind=kind, max_depth=depth)
    drawn = set()
    for d, bid, via in steps:
        b = graph.blocks.get(bid)
        indent = "  " * d
        if via:
            g = KIND_GLYPH.get(via.kind, "->")
            arrow = _c(KIND_COLOR.get(via.kind, C.WHITE),
                       f"{g}{('(' + via.label + ')') if via.label else ''} ")
        else:
            arrow = ""
        tcol = TYPE_COLOR.get((b.type if b else "" or "").lower(), C.WHITE)
        label = _c(C.BOLD, bid)
        if b:
            label += " " + _c(tcol, f"[{b.type or '—'}]")
            first = (b.body.splitlines()[0] if b.body else "")
            if first:
                label += "  " + _c(C.DIM, first[:60])
        else:
            label += " " + _c(C.RED, "(missing)")
        cyc = _c(C.DIM, "  ⟲") if bid in drawn else ""
        print(f"{indent}{arrow}{label}{cyc}")
        drawn.add(bid)


def cmd_clusters(graph: Graph, radius: int) -> None:
    clusters = cluster(graph, radius=radius)
    print(_c(C.BOLD, f"Q6 clusters at Hamming radius ≤ {radius}: "
                     f"{sum(1 for c in clusters if len(c) > 1)} multi-block, "
                     f"{sum(1 for c in clusters if len(c) == 1)} singletons"))
    for n, members in enumerate(clusters, 1):
        if len(members) == 1:
            b = graph.blocks[members[0]]
            tag = "" if b.q6 else _c(C.DIM, " (unaddressed)")
            print(f"\n{_c(C.DIM, f'cluster {n}:')} {members[0]} "
                  f"{_render_q6(b.q6)}{tag}")
            continue
        print(f"\n{_c(C.BOLD + C.CYAN, f'cluster {n}')} "
              f"({len(members)} blocks):")
        for mid in members:
            b = graph.blocks[mid]
            first = (b.body.splitlines()[0] if b.body else "")
            print(f"  {_render_q6(b.q6)}  {_c(C.BOLD, mid)}  "
                  f"{_c(C.DIM, first[:50])}")


def cmd_validate(graph: Graph) -> None:
    issues = validate(graph)
    if not issues:
        print(_c(C.GREEN, "ok — no issues"))
        return
    errs = [m for m in issues if "dangling" in m or "duplicate" in m or "malformed" in m]
    warns = [m for m in issues if m not in errs]
    for m in errs:
        print(_c(C.RED, "✗ ") + m)
    for m in warns:
        print(_c(C.YELLOW, "! ") + m)
    print(_c(C.DIM, f"\n{len(errs)} errors, {len(warns)} warnings"))
    if errs:
        sys.exit(1)


def cmd_stats(graph: Graph) -> None:
    by_type: Dict[str, int] = defaultdict(int)
    by_kind: Dict[str, int] = defaultdict(int)
    addressed = 0
    dangling = 0
    ids = set(graph.blocks)
    for b in graph:
        by_type[b.type or "—"] += 1
        if b.q6:
            addressed += 1
        for link in b.links:
            by_kind[link.kind] += 1
            if link.target not in ids:
                dangling += 1
    print(_c(C.BOLD, "stats"))
    print(f"  blocks:        {len(graph)}")
    print(f"  with q6:       {addressed}/{len(graph)}")
    print(f"  links:         {sum(by_kind.values())} "
          f"({', '.join(f'{k}:{v}' for k, v in sorted(by_kind.items()))})")
    print(f"  dangling:      {dangling}")
    print(f"  types:         {', '.join(f'{k}:{v}' for k, v in sorted(by_type.items()))}")
    print(f"  warnings:      {len(graph.warnings)}")


# --------------------------------------------------------------------------- #
# Converter: networkx node-link JSON  ->  .inf
# --------------------------------------------------------------------------- #

_BODY_KEYS = ("label", "text", "name", "title", "body", "summary")
_TYPE_KEYS = ("type", "kind", "category", "class", "label_type")


def _derive_q6(seed: str) -> str:
    """Deterministic placeholder Q6 from a seed (e.g. node type).

    NOTE: this is ONLY for demos so clustering has signal. In production the
    q6 must come from your real routing (Q6 / {-1,+1}^6), not a hash.
    """
    h = hashlib.sha1(seed.encode("utf-8")).digest()
    bits = bin(int.from_bytes(h[:1], "big"))[2:].zfill(8)[:6]
    return "".join("+" if c == "1" else "-" for c in bits)


def from_nodelink(data: dict) -> str:
    """Convert a networkx node-link dict into .inf source text."""
    nodes = data.get("nodes", [])
    links = data.get("links", data.get("edges", []))

    out_links: Dict[str, List[str]] = defaultdict(list)
    for e in links:
        src = str(e.get("source"))
        tgt = str(e.get("target"))
        rel = e.get("relation") or e.get("label") or e.get("key") or ""
        arrow = "\u2192"  # default elaborate
        rl = str(rel).lower()
        if rl in ("exception", "ausnahme", "override", "supersedes"):
            arrow = "\u21d2"
        elif rl in ("context", "kontext", "related"):
            arrow = "\u00b7"
        out_links[src].append(f"{arrow}{tgt}({rel})" if rel else f"{arrow}{tgt}")

    parts: List[str] = ["# generated by infon.py from networkx node-link JSON",
                        "# q6 values are DERIVED PLACEHOLDERS (from node type) "
                        "— replace with real routing", ""]
    for node in nodes:
        nid = str(node.get("id"))
        ntype = next((str(node[k]) for k in _TYPE_KEYS if k in node), None)
        q6 = node.get("q6")
        if not (isinstance(q6, str) and Q6_RE.match(q6)):
            q6 = _derive_q6(ntype or nid)
        body = next((str(node[k]) for k in _BODY_KEYS if k in node), "")

        header = f"\u221e {nid}"
        if ntype:
            header += f"  type:{ntype}"
        header += f"  q6:{q6}"
        parts.append(header)

        extra = {k: v for k, v in node.items()
                 if k not in ("id", "q6") and k not in _TYPE_KEYS and k not in _BODY_KEYS}
        for k, v in extra.items():
            parts.append(f"  {k}: {v}")
        if out_links.get(nid):
            parts.append("  links: " + "  ".join(out_links[nid]))
        parts.append("  \u2500\u2500")
        parts.append(f"  {body}" if body else "  (no body)")
        parts.append("")

    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _load(path: str) -> Graph:
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read())


def main(argv: Optional[List[str]] = None) -> None:
    global _USE_COLOR
    p = argparse.ArgumentParser(prog="infon", description="infon .inf tooling")
    p.add_argument("--no-color", action="store_true", help="disable ANSI colour")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("view", help="render all blocks")
    sp.add_argument("file")

    sp = sub.add_parser("tree", help="walk the domino graph from a block")
    sp.add_argument("file")
    sp.add_argument("id")
    sp.add_argument("--kind", choices=sorted(set(ARROW_KIND.values())), default=None)
    sp.add_argument("--depth", type=int, default=6)

    sp = sub.add_parser("clusters", help="Q6 Hamming clusters")
    sp.add_argument("file")
    sp.add_argument("--r", type=int, default=1, help="Hamming radius (default 1)")

    sp = sub.add_parser("validate", help="report structural issues")
    sp.add_argument("file")

    sp = sub.add_parser("stats", help="summary counts")
    sp.add_argument("file")

    sp = sub.add_parser("from-nodelink", help="convert networkx node-link JSON to .inf")
    sp.add_argument("file")
    sp.add_argument("-o", "--out", default=None)

    args = p.parse_args(argv)

    _USE_COLOR = (not args.no_color) and sys.stdout.isatty()

    if args.cmd == "from-nodelink":
        with open(args.file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        text = from_nodelink(data)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"wrote {args.out}", file=sys.stderr)
        else:
            sys.stdout.write(text)
        return

    graph = _load(args.file)
    if args.cmd == "view":
        cmd_view(graph)
    elif args.cmd == "tree":
        cmd_tree(graph, args.id, args.kind, args.depth)
    elif args.cmd == "clusters":
        cmd_clusters(graph, args.r)
    elif args.cmd == "validate":
        cmd_validate(graph)
    elif args.cmd == "stats":
        cmd_stats(graph)


if __name__ == "__main__":
    main()
