#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.cli_inventory
# TYPE: active-script
# DOMAIN: core.cli
# DEPTH_LEVEL: 1
# SUMMARY: Read-only inventory of tools/*.py CLI help/json safety patterns.
# ==========================================
"""
CLI inventory (T-243) — read-only map of repository tools by CLI safety pattern.

This tool does not import or execute scanned tools. It reads source files as text
and classifies them so agents can see which tools already have safe probing and
which ones still need help_guard/argparse follow-up.

CLI:
    python tools/cli_inventory.py
    python tools/cli_inventory.py --json
    python tools/cli_inventory.py --status unsafe-sysargv --status manual-help
    python tools/cli_inventory.py --include-tests --tools-dir tools
"""
import argparse
import ast
import json
import os
import re
import sys
import time

from _ioutil import configure_output


configure_output()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_TOOLS_DIR = HERE
SCHEMA = "cli_inventory.v1"
ORDER = [
    "ok-argparse",
    "ok-help-guard",
    "manual-help",
    "unsafe-sysargv",
    "entrypoint-no-argv",
    "library-or-helper",
]
RISK = {
    "ok-argparse": "low",
    "ok-help-guard": "low",
    "manual-help": "medium",
    "unsafe-sysargv": "high",
    "entrypoint-no-argv": "medium",
    "library-or-helper": "low",
}


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def module_doc(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""
    return ast.get_docstring(tree) or ""


def rel(path, base=ROOT):
    try:
        return os.path.relpath(path, base).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def has(pattern, text):
    return re.search(pattern, text, re.MULTILINE) is not None


def classify(features):
    if not features["cli_candidate"]:
        return "library-or-helper"
    if features["uses_argparse"]:
        return "ok-argparse"
    if features["uses_help_guard"]:
        return "ok-help-guard"
    if features["uses_sys_argv"] and features["manual_help"]:
        return "manual-help"
    if features["uses_sys_argv"]:
        return "unsafe-sysargv"
    return "entrypoint-no-argv"


def first_doc_line(doc):
    for line in (doc or "").splitlines():
        line = line.strip()
        if line:
            return line[:160]
    return ""


def feature_map(text):
    doc = module_doc(text)
    has_main_def = has(r"^\s*def\s+main\s*\(", text)
    has_main_guard = "__main__" in text and ("sys.exit" in text or "main(" in text)
    uses_sys_argv = "sys.argv" in text
    uses_argparse = (
        has(r"^\s*import\s+argparse\b", text)
        or has(r"^\s*from\s+argparse\s+import\b", text)
        or "argparse." in text
    )
    uses_help_guard = "help_guard(" in text and ("from _cli import" in text or "import _cli" in text)
    manual_help = '"--help"' in text or "'--help'" in text or '"-h"' in text or "'-h'" in text
    cli_candidate = has_main_guard or (has_main_def and uses_sys_argv)
    return {
        "cli_candidate": cli_candidate,
        "has_main_def": has_main_def,
        "has_main_guard": has_main_guard,
        "uses_sys_argv": uses_sys_argv,
        "uses_argparse": uses_argparse,
        "uses_help_guard": uses_help_guard,
        "manual_help": manual_help,
        "has_cli_doc": "CLI:" in doc,
        "json_mode": "--json" in text or "json.dumps" in text,
        "doc_summary": first_doc_line(doc),
    }


def scan_file(path):
    text = read_text(path)
    features = feature_map(text)
    status = classify(features)
    reasons = []
    if status == "unsafe-sysargv":
        reasons.append("uses sys.argv without argparse/help_guard/manual help")
    elif status == "manual-help":
        reasons.append("manual help detected; consider _cli.help_guard for consistency")
    elif status == "entrypoint-no-argv":
        reasons.append("has entrypoint but no visible argv/help contract")
    elif status == "ok-help-guard" and not features["has_cli_doc"]:
        reasons.append("help_guard is present but module docstring has no CLI section")
    return {
        "path": rel(path),
        "name": os.path.basename(path),
        "status": status,
        "risk": RISK[status],
        "features": features,
        "reasons": reasons,
    }


def iter_python_files(tools_dir, include_tests=False):
    for name in sorted(os.listdir(tools_dir)):
        path = os.path.join(tools_dir, name)
        if not os.path.isfile(path):
            continue
        if not name.endswith(".py"):
            continue
        if not include_tests and name.startswith("test_"):
            continue
        yield path


def scan_dir(tools_dir=DEFAULT_TOOLS_DIR, include_tests=False):
    tools_dir = os.path.abspath(tools_dir)
    entries = []
    for path in iter_python_files(tools_dir, include_tests=include_tests):
        try:
            entries.append(scan_file(path))
        except OSError as exc:
            entries.append({
                "path": rel(path),
                "name": os.path.basename(path),
                "status": "scan-error",
                "risk": "high",
                "features": {},
                "reasons": [str(exc)],
            })
    entries.sort(key=lambda e: (ORDER.index(e["status"]) if e["status"] in ORDER else 99, e["path"]))
    return entries


def build_report(tools_dir=DEFAULT_TOOLS_DIR, include_tests=False):
    entries = scan_dir(tools_dir=tools_dir, include_tests=include_tests)
    counts = {key: 0 for key in ORDER}
    counts["scan-error"] = 0
    for entry in entries:
        counts.setdefault(entry["status"], 0)
        counts[entry["status"]] += 1
    risky = [
        e for e in entries
        if e["status"] in ("manual-help", "unsafe-sysargv", "entrypoint-no-argv", "scan-error")
    ]
    return {
        "schema": SCHEMA,
        "generated_epoch": int(time.time()),
        "tools_dir": rel(os.path.abspath(tools_dir)),
        "include_tests": bool(include_tests),
        "totals": {
            "files": len(entries),
            "cli_candidates": sum(1 for e in entries if e.get("features", {}).get("cli_candidate")),
            "risky": len(risky),
            "by_status": counts,
        },
        "entries": entries,
        "risky": risky,
    }


def filtered(entries, statuses):
    wanted = set(statuses or [])
    if not wanted:
        return entries
    return [e for e in entries if e["status"] in wanted]


def text_report(data, statuses=None, limit=40):
    entries = filtered(data["entries"], statuses)
    lines = [
        "CLI INVENTORY",
        "schema: %s" % data["schema"],
        "tools_dir: %s" % data["tools_dir"],
        "files: %d" % data["totals"]["files"],
        "cli_candidates: %d" % data["totals"]["cli_candidates"],
        "risky: %d" % data["totals"]["risky"],
        "",
        "Status counts:",
    ]
    for key in ORDER:
        lines.append("  %-18s %d" % (key, data["totals"]["by_status"].get(key, 0)))
    if data["totals"]["by_status"].get("scan-error", 0):
        lines.append("  %-18s %d" % ("scan-error", data["totals"]["by_status"].get("scan-error", 0)))
    lines.extend(["", "Entries:"])
    for entry in entries[:limit]:
        suffix = ""
        if entry["reasons"]:
            suffix = " — " + "; ".join(entry["reasons"])
        lines.append("  %-18s %-6s %s%s" % (entry["status"], entry["risk"], entry["path"], suffix))
    if len(entries) > limit:
        lines.append("  ... %d more (use --limit %d or --json)" % (len(entries) - limit, len(entries)))
    return "\n".join(lines) + "\n"


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Read-only inventory of tools/*.py CLI safety patterns.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--text", action="store_true", help="print human text report (default)")
    parser.add_argument("--include-tests", action="store_true", help="include tools/test_*.py files")
    parser.add_argument("--tools-dir", default=DEFAULT_TOOLS_DIR, help="directory to scan")
    parser.add_argument("--status", action="append", default=[], help="filter text entries by status")
    parser.add_argument("--limit", type=int, default=40, help="max entries in text mode")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    data = build_report(args.tools_dir, include_tests=args.include_tests)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(text_report(data, statuses=args.status, limit=args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())