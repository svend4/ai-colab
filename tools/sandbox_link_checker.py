#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.sandbox_link_checker
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Проверка локальных Markdown ссылок во входящей песочнице (read-only)
# ==========================================
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import unquote


LINK_REGEX = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")
EXTERNAL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
IGNORED_SCHEMES = ("http:", "https:", "mailto:", "tel:", "data:", "ftp:")


def _display_path(path, base_dir):
    rel = os.path.relpath(path, base_dir)
    return rel.replace(os.sep, "/")


def _is_inside(root, target):
    root_norm = os.path.normcase(os.path.abspath(root))
    target_norm = os.path.normcase(os.path.abspath(target))
    try:
        return os.path.commonpath([root_norm, target_norm]) == root_norm
    except ValueError:
        return False


def _clean_link(raw_target):
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target or target.startswith("#"):
        return None

    low = target.lower()
    if low.startswith(IGNORED_SCHEMES):
        return None
    if EXTERNAL_RE.match(target) and not re.match(r"^[a-zA-Z]:[\\/]", target):
        return None

    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target:
        return None
    return unquote(target)


def _resolve_target(source_file, base_dir, target):
    if target.startswith(("/", "\\")):
        raw = os.path.join(base_dir, target.lstrip("/\\"))
    else:
        raw = os.path.join(os.path.dirname(source_file), target)
    return os.path.abspath(os.path.normpath(raw))


def check_markdown_file(filepath, base_dir):
    base_dir = os.path.abspath(base_dir)
    source_file = os.path.abspath(filepath)
    broken_links = []

    try:
        with open(source_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as exc:
        return {
            "file": _display_path(source_file, base_dir),
            "abs_file": source_file,
            "broken_links": [
                {
                    "line": 0,
                    "text": "<file>",
                    "target": source_file,
                    "kind": "read-error",
                    "message": str(exc),
                }
            ],
        }

    for line_no, line in enumerate(lines, start=1):
        for match in LINK_REGEX.finditer(line):
            link_text, raw_target = match.groups()
            clean_target = _clean_link(raw_target)
            if clean_target is None:
                continue

            target_path = _resolve_target(source_file, base_dir, clean_target)
            if not _is_inside(base_dir, target_path):
                broken_links.append(
                    {
                        "line": line_no,
                        "text": link_text,
                        "target": raw_target,
                        "kind": "outside-root",
                        "resolved": os.path.relpath(target_path, base_dir).replace(os.sep, "/"),
                    }
                )
                continue

            if not os.path.exists(target_path):
                broken_links.append(
                    {
                        "line": line_no,
                        "text": link_text,
                        "target": raw_target,
                        "kind": "missing",
                        "resolved": _display_path(target_path, base_dir),
                    }
                )

    return {
        "file": _display_path(source_file, base_dir),
        "abs_file": source_file,
        "broken_links": broken_links,
    }


def scan(target_dir):
    base_dir = os.path.abspath(target_dir)
    issues = []
    files_scanned = 0

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = sorted(dirs)
        for name in sorted(files):
            if not name.lower().endswith(".md"):
                continue
            files_scanned += 1
            result = check_markdown_file(os.path.join(root, name), base_dir)
            if result.get("broken_links"):
                issues.append(result)

    issue_count = sum(len(item.get("broken_links", [])) for item in issues)
    return {
        "base_dir": base_dir,
        "files_scanned": files_scanned,
        "files_with_issues": len(issues),
        "issue_count": issue_count,
        "ok": issue_count == 0,
        "issues": issues,
    }


def scan_directory(target_dir):
    """Backward-compatible helper: return only files with issues."""
    return scan(target_dir)["issues"]


def _print_text(report):
    if report["ok"]:
        print("OK: %d Markdown files checked; no broken local links" % report["files_scanned"])
        return
    print("BROKEN: %d issue(s) in %d file(s)" % (report["issue_count"], report["files_with_issues"]))
    for item in report["issues"]:
        for link in item["broken_links"]:
            print("%s:%s %s %s -> %s" % (
                item["file"],
                link.get("line", 0),
                link.get("kind", "missing"),
                link.get("text", ""),
                link.get("target", ""),
            ))


def build_parser():
    parser = argparse.ArgumentParser(description="Check local Markdown links inside an isolated sandbox directory.")
    parser.add_argument("target", help="Directory to scan")
    parser.add_argument("--json", action="store_true", help="Print JSON report (default)")
    parser.add_argument("--text", action="store_true", help="Print compact text report")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    target = os.path.abspath(args.target)

    if not os.path.isdir(target):
        payload = {"error": "not-a-directory", "path": args.target}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    report = scan(target)
    if args.text:
        _print_text(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())