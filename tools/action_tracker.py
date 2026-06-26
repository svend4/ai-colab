#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.action_tracker
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Утилита для гранулярного трекинга состояния отчетов (Traceability Matrix).
# ==========================================
"""
import os
import sys
import re
import time
import json
import argparse
from _cli import help_guard
from _ioutil import configure_output, safe_write

configure_output()

try:
    from _canon import parse_fm, dump_fm
except ImportError:
    # Fallback if _canon is not available or path is wrong
    def parse_fm(text):
        m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
        if not m:
            return {}
        d = {}
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                d[k.strip()] = v.strip()
        return d
        
    def dump_fm(d):
        lines = ["---"]
        for k, v in d.items():
            lines.append(f"{k}: {v}")
        lines.append("---")
        return "\n".join(lines) + "\n"

def replace_fm(text, d):
    fm_text = dump_fm(d) if "dump_fm" in globals() else "---" # simple fallback logic is handled
    # proper implementation
    lines = ["---"]
    for k, v in d.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    fm_text = "\n".join(lines) + "\n"
    
    m = re.match(r"^---\r?\n.*?\r?\n---\r?\n", text, re.S)
    if m:
        return fm_text + text[m.end():]
    return fm_text + text

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX = os.path.join(ROOT, "queues", "outbox")

HELP = """action_tracker — утилита гранулярного трекинга параграфов (Action Items).

Анализирует Markdown-чекбоксы `- [ ]` и `- [x]` внутри отчетов в queues/outbox/.
Вычисляет статус каждого документа на лету:
  - unprocessed : есть только [ ]
  - partial     : есть и [ ], и [x]
  - shipped     : есть только [x]
  - no-actions  : чекбоксов нет
  - historical  : помечено в front-matter (status: historical)

Использование:
  python tools/action_tracker.py status [--json]
  python tools/action_tracker.py archive-old [--apply]
"""

def parse_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"file": os.path.basename(filepath), "status": "error", "error": str(e)}

    fm = parse_fm(content)
    if fm.get("status") == "historical" or fm.get("type") == "info":
        return {"file": os.path.basename(filepath), "status": "historical", "checked": 0, "unchecked": 0, "total": 0}

    lines = content.split("\n")
    unchecked = 0
    checked = 0
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
            
        m = re.match(r"^\s*-\s+\[(.)\]\s", line)
        if m:
            char = m.group(1).lower()
            if char == " ":
                unchecked += 1
            elif char == "x":
                checked += 1

    total = unchecked + checked
    if total == 0:
        status = "no-actions"
    elif unchecked > 0 and checked == 0:
        status = "unprocessed"
    elif unchecked > 0 and checked > 0:
        status = "partial"
    elif unchecked == 0 and checked > 0:
        status = "shipped"
    else:
        status = "unknown"

    return {
        "file": os.path.basename(filepath),
        "status": status,
        "checked": checked,
        "unchecked": unchecked,
        "total": total
    }

def get_all_reports():
    if not os.path.exists(OUTBOX):
        return []
    reports = []
    for f in os.listdir(OUTBOX):
        if f.endswith(".md"):
            reports.append(os.path.join(OUTBOX, f))
    return reports

def cmd_status(args):
    reports = get_all_reports()
    results = [parse_file(r) for r in reports]
    
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
        
    counts = {"unprocessed": 0, "partial": 0, "shipped": 0, "no-actions": 0, "historical": 0, "error": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        
    print(f"Всего отчетов: {len(results)}")
    print(f"unprocessed: {counts['unprocessed']}")
    print(f"partial:     {counts['partial']}")
    print(f"shipped:     {counts['shipped']}")
    print(f"no-actions:  {counts['no-actions']}")
    print(f"historical:  {counts['historical']}")
    
    if counts["unprocessed"] > 0 or counts["partial"] > 0:
        print("\nТребуют внимания (unprocessed / partial):")
        for r in results:
            if r["status"] in ("unprocessed", "partial"):
                print(f"  [{r['status'].upper():11s}] {r['file']} (выполнено {r['checked']}/{r['total']})")
                
    return 0

def cmd_archive_old(args):
    reports = get_all_reports()
    
    to_archive = []
    for r in reports:
        info = parse_file(r)
        if info["status"] not in ("historical", "error"):
            to_archive.append(r)
                
    if not args.apply:
        print(f"DRY RUN: Найдено {len(to_archive)} старых файлов для архивации (status: historical).")
        print("Запустите с флагом --apply для применения изменений.")
        return 0
        
    print(f"Архивация {len(to_archive)} файлов...")
    for filepath in to_archive:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            fm = parse_fm(content)
            fm["status"] = "historical"
            new_content = replace_fm(content, fm)
            
            safe_write(filepath, new_content)
        except Exception as e:
            print(f"Ошибка при архивации {os.path.basename(filepath)}: {e}")
            
    print("Готово. Старые файлы помечены как historical.")
    return 0

def main():
    help_guard(HELP, sys.argv[1:])
    parser = argparse.ArgumentParser(prog="action_tracker", description="Action Tracker", add_help=False)
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    
    p_status = subparsers.add_parser("status")
    p_status.add_argument("--json", action="store_true")
    
    p_archive = subparsers.add_parser("archive-old")
    p_archive.add_argument("--apply", action="store_true")
    
    args, _ = parser.parse_known_args()
    
    if args.cmd == "status":
        return cmd_status(args)
    elif args.cmd == "archive-old":
        return cmd_archive_old(args)
    else:
        print(HELP)
        return 1

if __name__ == "__main__":
    sys.exit(main())
