#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.question_tree
# TYPE: active-script
# DOMAIN: core.reflection
# DEPTH_LEVEL: 1
# SUMMARY: Read-only extractor for numbered question trees: questions, answers, statuses, next-action hints.
# ==========================================
"""
question_tree.py — read-only analysis of numbered question-tree Markdown documents.

It does not edit the source document. It extracts `**Вопрос X.Y.Z.**`, nearby
`**Ответ:**` and `**Статус:**` markers, then prints a text or JSON summary.

CLI:
    python tools/question_tree.py topics/information-refactoring-question-tree-2026-06-25.md
    python tools/question_tree.py topics/information-refactoring-question-tree-2026-06-25.md --json
    python tools/question_tree.py <file> --category open --limit 20
    python tools/question_tree.py <file> --action-plan
"""
import argparse
import json
import os
import re
import sys

from _ioutil import configure_output


configure_output()
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "question_tree.v1"
ACTION_PLAN_SCHEMA = "question_tree.action_plan.v1"
ACTION_ORDER = [
    ("requires-decision", 1, "decision-lane"),
    ("open", 2, "answer-or-question-lane"),
    ("unknown", 3, "status-backfill-lane"),
    ("partial", 4, "implementation-lane"),
    ("other", 5, "manual-review-lane"),
    ("solved", 6, "reference-or-archive-lane"),
]
QUESTION_RE = re.compile(r"^\*\*Вопрос\s+([0-9]+(?:\.[0-9]+)*)\.\*\*\s*(.+?)\s*$")
ANSWER_RE = re.compile(r"^\*\*Ответ:\*\*\s*(.*)")
STATUS_RE = re.compile(r"^\*\*Статус:\*\*\s*(.*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def rel(path):
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def resolve(path_value):
    raw = os.path.expanduser(path_value)
    path = raw if os.path.isabs(raw) else os.path.join(ROOT, raw)
    path = os.path.abspath(path)
    root = os.path.abspath(ROOT)
    if not (path == root or path.startswith(root + os.sep)):
        raise ValueError("path must stay inside repository root")
    if not path.lower().endswith(".md"):
        raise ValueError("question tree must be a Markdown file")
    return path


def status_category(status):
    s = (status or "").lower()
    if not s:
        return "unknown"
    if "частично" in s or "partial" in s:
        return "partial"
    if "requires decision" in s or "requires-decision" in s or ("треб" in s and "реш" in s):
        return "requires-decision"
    if "откры" in s or "open" in s:
        return "open"
    if "решено" in s or "solved" in s:
        return "solved"
    return "other"


def action_hint(category):
    return {
        "solved": "no-action or promote to reference",
        "partial": "create follow-up task or top-layer wrapper",
        "open": "write answer draft or create decision question",
        "requires-decision": "route to QUESTIONS/DECISIONS with human/integrator approval",
        "unknown": "add explicit status marker",
        "other": "review manually",
    }.get(category, "review manually")


def _consume_block(lines, start, stop_patterns):
    parts = []
    i = start
    while i < len(lines):
        line = lines[i]
        if any(p.match(line) for p in stop_patterns):
            break
        if line.strip() == "" and parts:
            break
        if line.strip():
            parts.append(line.strip())
        i += 1
    return " ".join(parts), i


def parse_text(text):
    lines = text.splitlines()
    questions = []
    headings = []
    current = None
    i = 0
    while i < len(lines):
        line = lines[i]
        hm = HEADING_RE.match(line)
        if hm:
            level = len(hm.group(1))
            title = hm.group(2).strip()
            headings = [h for h in headings if h[0] < level]
            headings.append((level, title))
        qm = QUESTION_RE.match(line)
        if qm:
            current = {
                "id": qm.group(1),
                "question": qm.group(2).strip(),
                "answer": "",
                "status": "",
                "category": "unknown",
                "section": " > ".join(h[1] for h in headings),
                "line": i + 1,
            }
            questions.append(current)
            i += 1
            continue
        am = ANSWER_RE.match(line)
        if am and current is not None:
            first = am.group(1).strip()
            if first:
                current["answer"] = first
            else:
                block, _ = _consume_block(lines, i + 1, [QUESTION_RE, STATUS_RE, HEADING_RE])
                current["answer"] = block
        sm = STATUS_RE.match(line)
        if sm and current is not None:
            current["status"] = sm.group(1).strip()
            current["category"] = status_category(current["status"])
        i += 1
    for q in questions:
        q["next_action"] = action_hint(q["category"])
    return questions


def analyze(path_value):
    path = resolve(path_value)
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    questions = parse_text(text)
    counts = {}
    for q in questions:
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    return {
        "schema": SCHEMA,
        "source": rel(path),
        "counts": {
            "questions": len(questions),
            "by_category": counts,
        },
        "questions": questions,
    }


def text_report(data, category=None, limit=80):
    qs = data["questions"]
    if category:
        qs = [q for q in qs if q["category"] == category]
    lines = [
        "QUESTION TREE",
        "schema: %s" % data["schema"],
        "source: %s" % data["source"],
        "questions: %d" % data["counts"]["questions"],
        "",
        "Categories:",
    ]
    for key in sorted(data["counts"]["by_category"]):
        lines.append("  %-18s %d" % (key, data["counts"]["by_category"][key]))
    lines.extend(["", "Questions:"])
    for q in qs[:limit]:
        answer = (q["answer"] or "").strip()
        if len(answer) > 110:
            answer = answer[:107] + "..."
        lines.append("  Q%-8s %-17s line %-4s %s" % (q["id"], q["category"], q["line"], q["question"]))
        lines.append("      status: %s" % (q["status"] or "<missing>"))
        lines.append("      next: %s" % q["next_action"])
        if answer:
            lines.append("      answer: %s" % answer)
    if len(qs) > limit:
        lines.append("  ... %d more" % (len(qs) - limit))
    return "\n".join(lines) + "\n"


def build_action_plan(data, category=None, limit=80):
    groups = []
    total_items = 0
    for cat, priority, lane in ACTION_ORDER:
        if category and cat != category:
            continue
        qs = [q for q in data["questions"] if q["category"] == cat]
        if not qs:
            continue
        shown = []
        for q in qs[:limit]:
            shown.append({
                "id": q["id"],
                "line": q["line"],
                "question": q["question"],
                "status": q["status"] or "<missing>",
                "answer_present": bool((q["answer"] or "").strip()),
                "next_action": q["next_action"],
            })
        total_items += len(qs)
        groups.append({
            "category": cat,
            "priority": priority,
            "lane": lane,
            "action": action_hint(cat),
            "count": len(qs),
            "showing": len(shown),
            "questions": shown,
        })
    return {
        "schema": ACTION_PLAN_SCHEMA,
        "source": data["source"],
        "question_tree_schema": data["schema"],
        "counts": data["counts"],
        "action_item_count": total_items,
        "group_count": len(groups),
        "recommended_sequence": [g["category"] for g in groups],
        "groups": groups,
    }


def action_plan_report(plan):
    lines = [
        "QUESTION TREE ACTION PLAN",
        "schema: %s" % plan["schema"],
        "source: %s" % plan["source"],
        "action items: %d" % plan["action_item_count"],
        "groups: %d" % plan["group_count"],
        "sequence: %s" % (" -> ".join(plan["recommended_sequence"]) or "<empty>"),
        "",
    ]
    for group in plan["groups"]:
        lines.append("%d. %s (%d) [%s]" % (group["priority"], group["category"], group["count"], group["lane"]))
        lines.append("   action: %s" % group["action"])
        for q in group["questions"]:
            marker = "answer" if q["answer_present"] else "no-answer"
            lines.append("   - Q%s line %s [%s] %s" % (q["id"], q["line"], marker, q["question"]))
            lines.append("     status: %s" % q["status"])
        if group["count"] > group["showing"]:
            lines.append("   ... %d more" % (group["count"] - group["showing"]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Read-only extractor for numbered question-tree Markdown documents.")
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--action-plan", action="store_true", help="group questions into action lanes")
    parser.add_argument("--category", choices=["solved", "partial", "open", "requires-decision", "unknown", "other"])
    parser.add_argument("--limit", type=int, default=80)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    data = analyze(args.path)
    if args.action_plan:
        plan = build_action_plan(data, category=args.category, limit=args.limit)
        if args.json:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            sys.stdout.write(action_plan_report(plan))
    elif args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(text_report(data, category=args.category, limit=args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())