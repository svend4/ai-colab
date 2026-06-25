#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.independent_first
# TYPE: active-script
# DOMAIN: core.coordination
# DEPTH_LEVEL: 1
# SUMMARY: Checks that an independent-first stream has real own sections before repo-search/comparison.
# ==========================================
"""
"""
Independent-first guard.

Checks that a stream packet has a real independent answer before an agent proceeds
to repo-search, comparison, or synthesis. This is an order guard, not a quality
judge: it catches empty/template sections and missing algorithm/pseudocode.

CLI:
    python tools/independent_first.py check <stream-id-or-path> [--root streams-root] [--json]

Policy:
    for methodology/architecture/variant tasks, write your own model, algorithm,
    pseudocode and risks before repo-search/comparison.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from _cli import help_guard
from _canon import parse_front_matter
from _ioutil import configure_output
import stream as stream_tool

configure_output()

REQUIRED = [
    "01. Условия применимости",
    "02. Независимый ответ агента",
    "03. Потенциал, который нужно раскрыть до синтеза",
]
PLACEHOLDERS = [
    "Опишите, при каких условиях",
    "Заполните свой полный вариант",
    "- новые под-вопросы:",
    "- edge cases:",
    "- альтернативные реализации:",
    "- риски и ограничения:",
]
ALGORITHM_MARKERS = ["алгоритм", "algorithm"]
PSEUDOCODE_MARKERS = ["псевдокод", "pseudocode", "pseudo-code"]
MIN_SECTION_CHARS = 120


def _repo_rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), ROOT).replace(os.sep, "/")
    except ValueError:
        return os.path.abspath(path)


def _inside(path, base):
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(base)]) == os.path.abspath(base)
    except ValueError:
        return False


def _resolve_root(root):
    if not root:
        return stream_tool.streams_root()
    dest = root if os.path.isabs(root) else os.path.join(ROOT, root)
    dest = os.path.abspath(dest)
    if not _inside(dest, os.path.abspath(ROOT)):
        raise ValueError("refusing root outside repo: %s" % root)
    return dest


def _resolve_target(target, root=None):
    raw = (target or "").strip().strip('"')
    if not raw:
        raise ValueError("stream target is required")
    base = _resolve_root(root)
    if os.path.isabs(raw) or "/" in raw or "\\" in raw:
        path = raw if os.path.isabs(raw) else os.path.join(ROOT, raw)
        path = os.path.abspath(path)
        if os.path.isdir(path):
            path = os.path.join(path, "STREAM.md")
        if not _inside(path, os.path.abspath(ROOT)):
            raise ValueError("stream path must stay inside repo")
        return path
    for packet in stream_tool.list_packets(root=base):
        if packet.get("id") == raw:
            return packet.get("path")
    raise ValueError("stream not found: %s" % raw)


def _section_body(text, marker):
    needle = "## " + marker
    start = text.find(needle)
    if start == -1:
        return ""
    start = text.find("\n", start)
    if start == -1:
        return ""
    end = text.find("\n## ", start + 1)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def _compact(value):
    return re.sub(r"\s+", " ", value or "").strip()


def check_text(text):
    issues = []
    sections = {}
    for marker in REQUIRED:
        body = _section_body(text, marker)
        compact = _compact(body)
        section = {
            "present": bool(body),
            "chars": len(compact),
            "placeholder_hits": [p for p in PLACEHOLDERS if p in body],
        }
        if not body:
            issues.append({"code": "missing-section", "section": marker})
        elif len(compact) < MIN_SECTION_CHARS:
            issues.append({"code": "section-too-short", "section": marker, "chars": len(compact)})
        if section["placeholder_hits"]:
            issues.append({"code": "placeholder-section", "section": marker, "hits": section["placeholder_hits"]})
        sections[marker] = section

    body03 = _section_body(text, REQUIRED[2]).lower()
    has_algorithm = any(m in body03 for m in ALGORITHM_MARKERS)
    has_pseudocode = any(m in body03 for m in PSEUDOCODE_MARKERS)
    if not has_algorithm:
        issues.append({"code": "missing-algorithm-marker", "section": REQUIRED[2]})
    if not has_pseudocode:
        issues.append({"code": "missing-pseudocode-marker", "section": REQUIRED[2]})

    return {
        "sections": sections,
        "has_algorithm_marker": has_algorithm,
        "has_pseudocode_marker": has_pseudocode,
        "issues": issues,
    }


def check_path(path):
    if not os.path.isfile(path):
        raise ValueError("STREAM.md not found: %s" % path)
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    fm = parse_front_matter(text)
    result = check_text(text)
    ok = not result["issues"]
    return {
        "schema": "independent_first_check.v1",
        "status": "ok" if ok else "error",
        "ready_for_repo_search": ok,
        "path": path,
        "relpath": _repo_rel(path),
        "front_matter": {
            "id": fm.get("id"),
            "topic": fm.get("topic"),
            "agent": fm.get("agent"),
            "status": fm.get("status"),
        },
        **result,
        "next": "repo-search/comparison allowed" if ok else "fill sections 01-03 with own model, algorithm and pseudocode before repo-search",
    }


def render(payload):
    lines = [
        "INDEPENDENT-FIRST CHECK",
        "path: %s" % payload.get("relpath"),
        "status: %s" % payload.get("status"),
        "ready_for_repo_search: %s" % payload.get("ready_for_repo_search"),
    ]
    if payload.get("issues"):
        lines.append("issues:")
        for issue in payload["issues"]:
            if issue.get("section"):
                lines.append("- %s: %s" % (issue["code"], issue["section"]))
            else:
                lines.append("- %s" % issue["code"])
    lines.append("next: %s" % payload.get("next"))
    return "\n".join(lines)


def cmd_check(args):
    path = _resolve_target(args.target, root=args.root)
    payload = check_path(path)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(payload))
    return 0 if payload["status"] == "ok" else 1


def build_parser():
    parser = argparse.ArgumentParser(description="Check independent-first stream readiness before repo-search/comparison.")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("check", help="check stream sections 01-03 and algorithm/pseudocode markers")
    p.add_argument("target", help="stream id, STREAM.md path, or stream packet directory")
    p.add_argument("--root", help="streams root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_check)
    return parser


def main(argv=None):
    help_guard(__doc__, argv)
    args = build_parser().parse_args(argv)
    if not hasattr(args, "func"):
        build_parser().print_help()
        return 2
    try:
        return args.func(args)
    except ValueError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())