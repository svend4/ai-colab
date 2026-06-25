#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.info_draft
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: No-canon manager for documentation and information draft packets.
# ==========================================
"""
"""
Info/document draft packet manager.

This tool manages structured, non-canonical information draft packets under
sandbox/info-drafts/. It does not accept decisions, overwrite clean docs, delete
divergence, or promote files into docs/, topics/, core/, or portals/.

Commands:
    python tools/info_draft.py create <draft-id> --owner <agent> --purpose "..."
    python tools/info_draft.py check <draft-id-or-path> [--json]
    python tools/info_draft.py review <draft-id-or-path> [--json]
    python tools/info_draft.py list [--json]

Policy:
    info draft is evidence, not canon.
    promotion requires synthesis and a separate claimed task.
"""
import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from _cli import help_guard
from _ioutil import configure_output

configure_output()

DEFAULT_DRAFT_ROOT = os.path.join(ROOT, "sandbox", "info-drafts")
CANON_STATUS = "not-canonical-until-synthesized-and-promoted"
REQUIRED_FILES = [
    "manifest.json",
    "README.md",
    "brief.md",
    "outline.md",
    "claims.md",
    "sources.md",
    "open_questions.md",
    "divergence.md",
    "notes.md",
]
REQUIRED_MANIFEST = [
    "schema",
    "id",
    "title",
    "status",
    "owner_agent",
    "created_at",
    "kind",
    "purpose",
    "canon_status",
    "contains_private_data",
    "contains_secrets",
]
ALLOWED_KINDS = {"doc", "question-tree", "source-map", "decision-material", "portal-note", "research-notes"}
FORBIDDEN = [
    "accepted decision without governance",
    "direct overwrite of clean docs",
    "deleting divergence",
    "secrets in repository",
    "promotion without separate task",
]
ALLOWED_REVIEW = [
    "read-only file review",
    "structural review",
    "source/evidence review",
    "synthesis readiness review",
]


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


def _resolve_repo_dir(path):
    if not path:
        return DEFAULT_DRAFT_ROOT
    dest = path if os.path.isabs(path) else os.path.join(ROOT, path)
    dest = os.path.abspath(dest)
    if not _inside(dest, os.path.abspath(ROOT)):
        raise ValueError("refusing path outside repo: %s" % path)
    return dest


def _slug(value):
    value = (value or "").strip()
    if not value:
        raise ValueError("draft id is required")
    chars = []
    for ch in value.lower():
        if ch.isalnum():
            chars.append(ch)
        elif ch in "._-":
            chars.append(ch)
        elif chars and chars[-1] != "-":
            chars.append("-")
    slug = "".join(chars).strip("-._")
    if not slug:
        raise ValueError("draft id must contain letters or digits")
    if len(slug) > 96:
        slug = slug[:96].rstrip("-._")
    if not re.match(r"^[a-z0-9][a-z0-9._-]*$", slug):
        raise ValueError("unsafe draft id: %s" % value)
    return slug


def _resolve_draft(target, root=None, must_exist=True):
    draft_root = _resolve_repo_dir(root)
    raw = (target or "").strip().strip('"')
    if not raw:
        raise ValueError("draft id/path is required")
    if os.path.isabs(raw) or "/" in raw or "\\" in raw:
        path = raw if os.path.isabs(raw) else os.path.join(ROOT, raw)
    else:
        path = os.path.join(draft_root, _slug(raw))
    path = os.path.abspath(path)
    if not _inside(path, os.path.abspath(ROOT)):
        raise ValueError("draft path must stay inside repo")
    if must_exist and not os.path.isdir(path):
        raise ValueError("draft not found: %s" % raw)
    return path


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _load_manifest(path):
    try:
        with open(os.path.join(path, "manifest.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _source_context(args):
    items = []
    for label, value in [("task", args.task), ("stream", args.stream), ("topic", args.topic)]:
        if value:
            items.append("%s:%s" % (label, value))
    return items


def _manifest(draft_id, args, draft_path):
    rel = _repo_rel(draft_path)
    return {
        "schema": "info-draft-proposal.v1",
        "id": draft_id,
        "title": args.title or draft_id,
        "status": "draft",
        "owner_agent": args.owner,
        "created_at": datetime.date.today().isoformat(),
        "kind": args.kind,
        "purpose": args.purpose,
        "source_context": _source_context(args),
        "allowed_review": ALLOWED_REVIEW,
        "canon_status": CANON_STATUS,
        "contains_private_data": bool(args.contains_private_data),
        "contains_secrets": False,
        "target_promotion": {
            "kind": args.promotion_kind,
            "candidate_paths": list(args.target or []),
        },
        "forbidden": FORBIDDEN,
        "suggested_static_checks": [
            "python tools\\info_draft.py check %s --json" % rel,
            "python tools\\info_draft.py review %s --json" % rel,
            "python tools\\top.py synthesize-docs %s --ready-only --json" % (args.topic or draft_id),
        ],
        "review_notes": "",
    }


def _readme_text(draft_id, args):
    return """# %s

This is a non-canonical information draft packet.

## Purpose

%s

## Policy

- Info draft is evidence, not canon.
- Do not treat this packet as an accepted decision.
- Do not overwrite clean docs directly from this folder.
- Preserve divergence and alternative positions.
- Promotion requires synthesis and a separate claimed task.
""" % (args.title or draft_id, args.purpose)


def _brief_text(draft_id, args):
    return """# Brief

Draft id: `%s`

## One Sentence

%s

## Intended Reader

- human reviewers
- AI agents comparing variants

## Not Canonical

This brief is not accepted documentation until synthesis and promotion.
""" % (draft_id, args.purpose)


def _outline_text():
    return """# Outline

## 01. Context

## 02. Main Claims

## 03. Evidence

## 04. Open Questions

## 05. Divergence

## 06. Promotion Target
"""


def _claims_text():
    return """# Claims

Write one claim per bullet. Claims should be comparable across agent variants.

- claim:
"""


def _sources_text():
    return """# Sources

List repo files, reports, streams, external citations, or user messages used as evidence.

- source:
"""


def _questions_text():
    return """# Open Questions

Questions that must not be silently decided.

- question:
"""


def _divergence_text():
    return """# Divergence

Alternative positions, edge cases, or unresolved choices.

## DVG-001

- option A:
- option B:
- evidence needed:
"""


def cmd_create(args):
    if args.kind not in ALLOWED_KINDS:
        raise ValueError("--kind must be one of: %s" % ", ".join(sorted(ALLOWED_KINDS)))
    if not args.owner:
        raise ValueError("--owner is required")
    if not args.purpose:
        raise ValueError("--purpose is required")
    draft_root = _resolve_repo_dir(args.root)
    draft_id = _slug(args.draft_id)
    draft_path = os.path.join(draft_root, draft_id)
    if os.path.exists(draft_path):
        raise ValueError("draft already exists: %s" % _repo_rel(draft_path))

    os.makedirs(draft_root, exist_ok=True)
    os.mkdir(draft_path)
    manifest = _manifest(draft_id, args, draft_path)
    _write_json(os.path.join(draft_path, "manifest.json"), manifest)
    _write_text(os.path.join(draft_path, "README.md"), _readme_text(draft_id, args))
    _write_text(os.path.join(draft_path, "brief.md"), _brief_text(draft_id, args))
    _write_text(os.path.join(draft_path, "outline.md"), _outline_text())
    _write_text(os.path.join(draft_path, "claims.md"), _claims_text())
    _write_text(os.path.join(draft_path, "sources.md"), _sources_text())
    _write_text(os.path.join(draft_path, "open_questions.md"), _questions_text())
    _write_text(os.path.join(draft_path, "divergence.md"), _divergence_text())
    _write_text(os.path.join(draft_path, "notes.md"), "# Notes\n\n")

    payload = {
        "schema": "info_draft_create.v1",
        "mutates": True,
        "draft": {
            "id": draft_id,
            "path": draft_path,
            "relpath": _repo_rel(draft_path),
            "manifest": _repo_rel(os.path.join(draft_path, "manifest.json")),
        },
        "write_scope": [_repo_rel(draft_path) + "/**"],
        "canon_status": CANON_STATUS,
        "next_commands": manifest["suggested_static_checks"],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("INFO DRAFT CREATED: %s" % payload["draft"]["relpath"])
        print("canon_status: %s" % CANON_STATUS)
        print("")
        print("Next commands:")
        for cmd in payload["next_commands"]:
            print("- %s" % cmd)
    return 0


def _read_nonempty_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return [ln.strip() for ln in f.read().splitlines() if ln.strip() and not ln.strip().startswith("#")]
    except OSError:
        return []


def _check_payload(path):
    manifest = _load_manifest(path)
    issues = []
    for name in REQUIRED_FILES:
        if not os.path.isfile(os.path.join(path, name)):
            issues.append({"code": "missing-file", "file": name, "severity": "error"})
    for field in REQUIRED_MANIFEST:
        if field not in manifest:
            issues.append({"code": "missing-%s" % field, "severity": "error"})
    if manifest.get("schema") not in (None, "info-draft-proposal.v1"):
        issues.append({"code": "invalid-schema", "severity": "error"})
    if manifest.get("canon_status") not in (None, CANON_STATUS):
        issues.append({"code": "canon-status-invalid", "severity": "error"})
    if manifest.get("contains_secrets") is True:
        issues.append({"code": "secrets-in-draft", "severity": "error"})
    if manifest.get("contains_private_data") is True:
        issues.append({"code": "private-data-in-draft", "severity": "warning"})
    kind = manifest.get("kind")
    if kind is not None and kind not in ALLOWED_KINDS:
        issues.append({"code": "invalid-kind", "severity": "error"})
    errors = [i for i in issues if i.get("severity") != "warning"]
    return {
        "schema": "info_draft_check.v1",
        "status": "ok" if not errors else "error",
        "draft": {"path": path, "relpath": _repo_rel(path)},
        "manifest": {"exists": os.path.isfile(os.path.join(path, "manifest.json")), "data": manifest},
        "issues": issues,
        "canon_status": CANON_STATUS,
    }


def cmd_check(args):
    path = _resolve_draft(args.draft, args.root)
    payload = _check_payload(path)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("INFO DRAFT CHECK: %s" % payload["draft"]["relpath"])
        print("status: %s" % payload["status"])
        print("canon_status: %s" % CANON_STATUS)
        for issue in payload["issues"]:
            print("%s: %s" % (issue.get("severity", "error"), issue.get("code")))
    return 0 if payload["status"] == "ok" else 1


def _section_count(path, filename):
    lines = _read_nonempty_lines(os.path.join(path, filename))
    return sum(1 for ln in lines if ln.startswith("- "))


def _review_payload(path):
    check = _check_payload(path)
    claims = _section_count(path, "claims.md")
    sources = _section_count(path, "sources.md")
    questions = _section_count(path, "open_questions.md")
    divergences = len(re.findall(r"(?mi)^##\s+", open(os.path.join(path, "divergence.md"), encoding="utf-8", errors="replace").read())) if os.path.isfile(os.path.join(path, "divergence.md")) else 0
    warnings = []
    if claims <= 1:
        warnings.append("claims-underfilled")
    if sources <= 1:
        warnings.append("sources-underfilled")
    if questions <= 1:
        warnings.append("open-questions-underfilled")
    if divergences == 0:
        warnings.append("divergence-not-structured")
    blocking = check["status"] != "ok"
    if blocking:
        route = "ask-agent-revision"
        level = "high"
    elif warnings:
        route = "keep-quarantine"
        level = "medium"
    else:
        route = "ready-for-synthesis"
        level = "low"
    manifest = check["manifest"]["data"]
    topic = None
    for item in manifest.get("source_context", []):
        if str(item).startswith("topic:"):
            topic = str(item).split(":", 1)[1]
            break
    topic = topic or manifest.get("id") or os.path.basename(path)
    return {
        "schema": "info_draft_review.v1",
        "source": {
            "id": manifest.get("id") or os.path.basename(path),
            "kind": manifest.get("kind") or "unknown",
            "path": _repo_rel(path),
            "mode": "read-only",
            "canon_status": CANON_STATUS,
        },
        "counts": {
            "claims": claims,
            "sources": sources,
            "open_questions": questions,
            "divergence_sections": divergences,
        },
        "check": check,
        "risk_summary": {
            "level": level,
            "blocking": blocking,
            "warnings": warnings,
        },
        "recommendation": {
            "route": route,
            "next_task_proposal": "synthesize, then create a separate promotion task if useful",
            "synthesis_command": "python tools\\top.py synthesize-docs %s --ready-only --json" % topic,
        },
    }


def cmd_review(args):
    path = _resolve_draft(args.draft, args.root)
    payload = _review_payload(path)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("INFO DRAFT REVIEW")
        print("source: %s" % payload["source"]["path"])
        print("risk: %s" % payload["risk_summary"]["level"])
        print("route: %s" % payload["recommendation"]["route"])
        print("canon_status: %s" % CANON_STATUS)
        for key, value in payload["counts"].items():
            print("- %s: %s" % (key, value))
    return 1 if payload["risk_summary"]["level"] == "high" else 0


def cmd_list(args):
    root = _resolve_repo_dir(args.root)
    rows = []
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            if not os.path.isdir(path):
                continue
            manifest = _load_manifest(path)
            rows.append({
                "id": manifest.get("id") or name,
                "title": manifest.get("title") or "",
                "status": manifest.get("status") or "unknown",
                "kind": manifest.get("kind") or "",
                "owner_agent": manifest.get("owner_agent") or "",
                "created_at": manifest.get("created_at") or "",
                "path": _repo_rel(path),
                "canon_status": CANON_STATUS,
            })
    payload = {"schema": "info_draft_list.v1", "root": _repo_rel(root), "drafts": rows}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("INFO DRAFT PACKETS")
        if not rows:
            print("(none)")
        for row in rows:
            print("- {id} [{status}] {kind} {owner_agent} {path}".format(**row))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="No-canon manager for documentation/information draft packets.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("create", help="create a non-canonical information draft packet")
    p.add_argument("draft_id")
    p.add_argument("--owner", required=True)
    p.add_argument("--title")
    p.add_argument("--purpose", required=True)
    p.add_argument("--kind", default="doc", choices=sorted(ALLOWED_KINDS))
    p.add_argument("--task")
    p.add_argument("--stream")
    p.add_argument("--topic")
    p.add_argument("--target", action="append")
    p.add_argument("--promotion-kind", default="doc", choices=["none", "task", "doc", "topic", "decision-material", "portal-note", "question-tree"])
    p.add_argument("--contains-private-data", action="store_true")
    p.add_argument("--root", help="draft root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("check", help="validate draft manifest and required files")
    p.add_argument("draft")
    p.add_argument("--root", help="draft root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("review", help="read-only structural synthesis-readiness review")
    p.add_argument("draft")
    p.add_argument("--root", help="draft root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("list", help="list information draft packets")
    p.add_argument("--root", help="draft root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)
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