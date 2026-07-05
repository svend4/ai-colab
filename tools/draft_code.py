#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.draft_code
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: No-execute manager for agent draft-code packets in sandbox/drafts.
# ==========================================
"""
"""
Draft-code packet manager.

This tool manages no-execute code proposal packets for agents and humans.
It creates and reviews quarantine evidence under sandbox/drafts/. It never
executes draft code, installs dependencies, imports draft modules, or promotes
files into tools/, drivers/, core/, or portals/.

Commands:
    python tools/draft_code.py create <draft-id> --owner <agent> --title "..." --purpose "..."
    python tools/draft_code.py check <draft-id-or-path> [--json]
    python tools/draft_code.py review <draft-id-or-path> [--json|--text]
    python tools/draft_code.py list [--json]

Optional create context:
    --task T-260
    --stream 20260625-1942-codex
    --topic code-variant-draft-manager
    --target tools/example.py --target tools/tests/test_example.py
    --root tmp-work/drafts-test

Policy:
    draft code is evidence, not implementation.
    execution is forbidden until a separate accepted run plan exists.
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
import sandbox_intake_chain
import sandbox_schema_validator

configure_output()

DEFAULT_DRAFT_ROOT = os.path.join(ROOT, "sandbox", "drafts")
EXECUTION_FORBIDDEN = "forbidden-until-accepted-run-plan"
FORBIDDEN = [
    "automatic execution",
    "dependency install",
    "network access",
    "secrets in repository",
    "promotion without separate task",
    "importing draft code from mainline",
]
ALLOWED_REVIEW = [
    "read-only file review",
    "static analysis",
    "diff review",
    "manifest/schema review",
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


def _load_manifest(path):
    manifest_path = os.path.join(path, "manifest.json")
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _source_context(args):
    items = []
    for label, value in [("task", args.task), ("stream", args.stream), ("topic", args.topic)]:
        if value:
            items.append("%s:%s" % (label, value))
    return items


def _manifest(draft_id, args, draft_path):
    rel = _repo_rel(draft_path)
    checks = [
        "python tools\\draft_code.py check %s --json" % rel,
        "python tools\\draft_code.py review %s --json" % rel,
        "python tools\\sandbox_intake_chain.py %s --kind agent-draft --json" % rel,
    ]
    return {
        "schema": "draft-code-proposal.v1",
        "id": draft_id,
        "title": args.title or draft_id,
        "status": "draft",
        "owner_agent": args.owner,
        "created_at": datetime.date.today().isoformat(),
        "purpose": args.purpose,
        "source_context": _source_context(args),
        "allowed_review": ALLOWED_REVIEW,
        "execution": EXECUTION_FORBIDDEN,
        "contains_external_code": bool(args.contains_external_code),
        "contains_secrets": False,
        "target_promotion": {
            "kind": args.promotion_kind,
            "candidate_paths": list(args.target or []),
        },
        "forbidden": FORBIDDEN,
        "suggested_static_checks": checks,
        "review_notes": "",
    }


def _readme_text(draft_id, args):
    return """# %s

This is a no-execute draft-code packet.

## Purpose

%s

## Policy

- Draft code is evidence, not implementation.
- Do not run files from this folder.
- Do not install dependencies from this folder.
- Do not import this code from mainline.
- Promotion requires a separate claimed task, tests, report, and review.

## Suggested Static Checks

```powershell
python tools\\draft_code.py check %s --json
python tools\\draft_code.py review %s --json
```
""" % (args.title or draft_id, args.purpose, draft_id, draft_id)


def _pseudocode_text(draft_id):
    return """# Pseudocode for %s

## Data Model

- input:
- output:
- state:

## Control Flow

1. ...

## Error Cases

- ...

## Test Intent

- ...

## Promotion Notes

This pseudocode is review material. It is not executable approval.
""" % draft_id


def cmd_create(args):
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
    os.mkdir(os.path.join(draft_path, "src"))
    os.mkdir(os.path.join(draft_path, "tests"))
    manifest = _manifest(draft_id, args, draft_path)
    _write_json(os.path.join(draft_path, "manifest.json"), manifest)
    _write_text(os.path.join(draft_path, "README.md"), _readme_text(draft_id, args))
    _write_text(os.path.join(draft_path, "pseudocode.md"), _pseudocode_text(draft_id))
    _write_text(os.path.join(draft_path, "notes.md"), "# Review Notes\n\n")
    _write_text(os.path.join(draft_path, "src", "README.md"), "# src\n\nDraft source goes here. Do not execute it from sandbox.\n")
    _write_text(os.path.join(draft_path, "tests", "README.md"), "# tests\n\nDraft test intent goes here. Do not execute it from sandbox.\n")

    payload = {
        "schema": "draft_code_create.v1",
        "mutates": True,
        "draft": {
            "id": draft_id,
            "path": draft_path,
            "relpath": _repo_rel(draft_path),
            "manifest": _repo_rel(os.path.join(draft_path, "manifest.json")),
        },
        "write_scope": [_repo_rel(draft_path) + "/**"],
        "execution_allowed": False,
        "next_commands": manifest["suggested_static_checks"],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("DRAFT CREATED: %s" % payload["draft"]["relpath"])
        print("execution_allowed: false")
        print("")
        print("Next commands:")
        for cmd in payload["next_commands"]:
            print("- %s" % cmd)
    return 0


def _check_payload(path):
    report = sandbox_schema_validator.scan(path)
    summary = report.get("summary", {})
    manifest_path = os.path.join(path, "manifest.json")
    manifest = _load_manifest(path)
    errors = summary.get("errors", 0)
    status = "ok" if errors == 0 and os.path.isfile(manifest_path) else "error"
    issues = []
    if not os.path.isfile(manifest_path):
        issues.append({"code": "missing-manifest", "message": "manifest.json is required", "severity": "error"})
        status = "error"
    if manifest.get("execution") not in (None, EXECUTION_FORBIDDEN):
        issues.append({"code": "execution-not-forbidden", "message": "draft execution must remain forbidden", "severity": "error"})
        status = "error"
    if manifest.get("contains_secrets") is True:
        issues.append({"code": "secrets-in-draft", "message": "drafts with secrets must not be stored", "severity": "error"})
        status = "error"
    return {
        "schema": "draft_code_check.v1",
        "status": status,
        "draft": {"path": path, "relpath": _repo_rel(path)},
        "manifest": {"exists": os.path.isfile(manifest_path), "data": manifest},
        "schema_report": report,
        "issues": issues,
        "execution_allowed": False,
    }


def cmd_check(args):
    path = _resolve_draft(args.draft, args.root)
    payload = _check_payload(path)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("DRAFT CHECK: %s" % payload["draft"]["relpath"])
        print("status: %s" % payload["status"])
        print("execution_allowed: false")
        for issue in payload["issues"]:
            print("%s: %s" % (issue["code"], issue["message"]))
    return 0 if payload["status"] == "ok" else 1


def cmd_review(args):
    path = _resolve_draft(args.draft, args.root)
    result = sandbox_intake_chain.scan(path, kind="agent-draft", source_id=os.path.basename(path))
    result["schema"] = "draft_code_review.v1"
    result["draft_policy"] = {
        "draft_code_is": "evidence-not-implementation",
        "execution_allowed": False,
        "promotion": "separate claimed task only",
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(sandbox_intake_chain.render_text(result))
        print("draft_policy: evidence-not-implementation; no execute; promotion task required")
    return 1 if result.get("risk_summary", {}).get("level") == "high" else 0


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
                "owner_agent": manifest.get("owner_agent") or "",
                "created_at": manifest.get("created_at") or "",
                "path": _repo_rel(path),
                "execution_allowed": False,
            })
    payload = {"schema": "draft_code_list.v1", "root": _repo_rel(root), "drafts": rows}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("DRAFT CODE PACKETS")
        if not rows:
            print("(none)")
        for row in rows:
            print("- {id} [{status}] {owner_agent} {path}".format(**row))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="No-execute manager for sandbox/drafts code packets.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("create", help="create a no-execute draft-code packet")
    p.add_argument("draft_id")
    p.add_argument("--owner", required=True)
    p.add_argument("--title")
    p.add_argument("--purpose", required=True)
    p.add_argument("--task")
    p.add_argument("--stream")
    p.add_argument("--topic")
    p.add_argument("--target", action="append")
    p.add_argument("--promotion-kind", default="task", choices=["none", "task", "tool", "driver", "doc", "test-fixture"])
    p.add_argument("--contains-external-code", action="store_true")
    p.add_argument("--root", help="draft root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("check", help="validate draft manifest and no-execute policy")
    p.add_argument("draft")
    p.add_argument("--root", help="draft root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("review", help="run read-only sandbox intake chain over a draft")
    p.add_argument("draft")
    p.add_argument("--root", help="draft root override; must stay inside repo")
    p.add_argument("--json", action="store_true")
    p.add_argument("--text", action="store_true")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("list", help="list draft packets")
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