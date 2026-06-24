#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.sandbox_schema_validator
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Read-only JSON and manifest schema validator for sandbox intake folders.
# ==========================================
"""

import argparse
import json
import os
import re
import sys

DRIVER_REQUIRED = [
    "id",
    "type",
    "title",
    "status",
    "level",
    "mode",
    "owner",
    "risk",
    "activation",
    "interfaces",
    "inputs",
    "outputs",
    "sandbox",
    "secrets",
    "source_last_verified",
    "timeout_seconds",
    "max_output_bytes",
    "audit",
    "related",
]
LEGACY_REQUIRED = ["name", "version", "entrypoint", "schema_version"]
DRAFT_REQUIRED = [
    "schema",
    "id",
    "title",
    "status",
    "owner_agent",
    "created_at",
    "purpose",
    "execution",
    "contains_external_code",
    "contains_secrets",
]
VALID_RISK = {"low", "medium", "high"}
VALID_MODE = {"read-only", "manual", "safe-write", "execute"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}


def _rel(path, base):
    return os.path.relpath(os.path.abspath(path), os.path.abspath(base)).replace(os.sep, "/")


def _issue(code, message, severity="error"):
    return {"code": code, "message": message, "severity": severity}


def _missing_issues(data, fields):
    issues = []
    for field in fields:
        if field not in data:
            issues.append(_issue("missing-%s" % field, "missing required field `%s`" % field))
    return issues


def _is_manifest(path):
    return os.path.basename(path).lower() == "manifest.json"


def _validate_driver_manifest(data):
    issues = _missing_issues(data, DRIVER_REQUIRED)
    risk = data.get("risk")
    if risk is not None and risk not in VALID_RISK:
        issues.append(_issue("invalid-risk", "risk must be low, medium, or high"))
    mode = data.get("mode")
    if mode is not None and mode not in VALID_MODE:
        issues.append(_issue("invalid-mode", "mode is not in the allowed set"))
    for field in ("interfaces", "inputs", "outputs"):
        if field in data and not isinstance(data.get(field), list):
            issues.append(_issue("invalid-%s" % field, "%s must be a list" % field))
    if data.get("source_last_verified") is not None and not DATE_RE.match(str(data.get("source_last_verified"))):
        issues.append(_issue("invalid-source-last-verified", "source_last_verified must be YYYY-MM-DD"))
    for field in ("timeout_seconds", "max_output_bytes"):
        if field in data:
            value = data.get(field)
            if not isinstance(value, int) or value <= 0:
                issues.append(_issue("invalid-%s" % field, "%s must be a positive integer" % field))
    if data.get("secrets") == "in-repo":
        issues.append(_issue("secrets-in-repo", "secrets must not be stored in repository"))
    if data.get("risk") in {"medium", "high"} and data.get("audit") is not True:
        issues.append(_issue("audit-required", "risk medium/high requires audit: true"))
    return issues


def _validate_legacy_manifest(data):
    return _missing_issues(data, LEGACY_REQUIRED)


def _validate_draft_manifest(data):
    issues = _missing_issues(data, DRAFT_REQUIRED)
    if data.get("schema") != "draft-code-proposal.v1":
        issues.append(_issue("invalid-schema", "draft manifest schema must be draft-code-proposal.v1"))
    if data.get("execution") and data.get("execution") != "forbidden-until-accepted-run-plan":
        issues.append(_issue("invalid-execution", "draft execution must remain forbidden until an accepted run plan"))
    for field in ("contains_external_code", "contains_secrets"):
        if field in data and not isinstance(data.get(field), bool):
            issues.append(_issue("invalid-%s" % field, "%s must be boolean" % field))
    if data.get("contains_secrets") is True:
        issues.append(_issue("secrets-in-repo", "drafts with secrets must not be stored in repository"))
    return issues


def _validate_manifest_data(data):
    if not isinstance(data, dict):
        return [_issue("manifest-not-object", "manifest.json must contain a JSON object")]
    if data.get("schema") == "draft-code-proposal.v1":
        return _validate_draft_manifest(data)
    if data.get("type") == "driver" or any(k in data for k in ("level", "mode", "activation", "interfaces")):
        return _validate_driver_manifest(data)
    return _validate_legacy_manifest(data)


def validate_manifest(filepath):
    """Compatibility API: validate one manifest.json and return old status shape."""
    report = _scan_file(filepath, os.path.dirname(os.path.abspath(filepath)), max_bytes=None)
    status = "error" if any(i["severity"] == "error" for i in report["issues"]) else "ok"
    out = {"file": filepath, "status": status}
    if report["issues"]:
        out["message"] = "; ".join("%s: %s" % (i["code"], i["message"]) for i in report["issues"])
        out["issues"] = report["issues"]
    return out


def _scan_file(path, base, max_bytes):
    rel = _rel(path, base)
    item = {"path": rel, "file": path, "kind": "json", "issues": []}
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        item["issues"].append(_issue("stat-error", str(exc)))
        return item
    item["bytes"] = size
    if max_bytes is not None and size > max_bytes:
        item["issues"].append(_issue("too-large", "file exceeds max_bytes", severity="warning"))
        return item
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        item["issues"].append(_issue("invalid-json", str(exc)))
        return item
    if _is_manifest(path):
        item["kind"] = "manifest"
        item["issues"].extend(_validate_manifest_data(data))
    return item


def scan(root, max_bytes=None):
    base = os.path.abspath(os.path.expanduser(root))
    files = []
    for current, dirs, names in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if name.lower().endswith(".json"):
                files.append(_scan_file(os.path.join(current, name), base, max_bytes=max_bytes))
    errors = 0
    warnings = 0
    manifests = 0
    for item in files:
        if item["kind"] == "manifest":
            manifests += 1
        for issue in item["issues"]:
            if issue["severity"] == "warning":
                warnings += 1
            else:
                errors += 1
    return {
        "schema": "sandbox-schema-validator.v1",
        "root": base,
        "files": files,
        "summary": {
            "ok": errors == 0,
            "json_files": len(files),
            "manifest_files": manifests,
            "errors": errors,
            "warnings": warnings,
        },
    }


def scan_directory(target_dir):
    """Compatibility API used by the intake chain."""
    report = scan(target_dir)
    results = []
    for item in report["files"]:
        if item["kind"] != "manifest":
            continue
        errors = [i for i in item["issues"] if i["severity"] != "warning"]
        copied = {
            "file": os.path.join(os.path.abspath(target_dir), item["path"].replace("/", os.sep)),
            "status": "error" if errors else "ok",
        }
        if item["issues"]:
            copied["message"] = "; ".join("%s: %s" % (i["code"], i["message"]) for i in item["issues"])
            copied["issues"] = item["issues"]
        results.append(copied)
    return results


def build_parser():
    parser = argparse.ArgumentParser(description="Read-only JSON and manifest validator.")
    parser.add_argument("target", help="Directory to scan")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument("--max-bytes", type=int, default=None)
    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(json.dumps({"error": "No directory provided"}, ensure_ascii=False, indent=2))
        return 2
    args = build_parser().parse_args(argv)
    if not os.path.isdir(args.target):
        print(json.dumps({"error": "not-a-directory", "path": args.target}, ensure_ascii=False, indent=2))
        return 2
    report = scan(args.target, max_bytes=args.max_bytes)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        summary = report["summary"]
        print(
            "json=%d manifests=%d errors=%d warnings=%d"
            % (summary["json_files"], summary["manifest_files"], summary["errors"], summary["warnings"])
        )
        for item in report["files"]:
            for issue in item["issues"]:
                print("%s: %s [%s]" % (item["path"], issue["code"], issue["severity"]))
    return 0 if report["summary"]["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())