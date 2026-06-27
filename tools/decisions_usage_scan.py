#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.decisions_usage_scan
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Read-only счётчик использования решений D-XXX по репозиторию (актив/умеренно/мёртвый-груз).
# ==========================================
"""decisions_usage_scan.py — счётчик использования решений D-NNN по репозиторию (read-only).

Сканирует все .md и .py на ссылки `D-NNN`, считает по каждому решению из `decisions/D-*.md` число
файлов-ссылок, классифицирует: **active** (≥THR_HI), **moderate** (≥THR_LO), **dead-weight** (<THR_LO).
Кодирует docs/decisions-usage.md (который был РУЧНОЙ таблицей от 2026-06-23 — теперь генерируется).
Grow-only: новый read-only тул, в канон ничего не пишет (D-032).

CLI:
  python tools/decisions_usage_scan.py            # таблица
  python tools/decisions_usage_scan.py --json
  python tools/decisions_usage_scan.py --dead     # только мёртвый-груз
"""
import os
import sys
import re
import glob
import json

from _ioutil import configure_output
from _cli import help_guard

configure_output()
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THR_HI, THR_LO = 10, 3
REF = re.compile(r"\bD-\d{3}\b")
# Каталоги, исключаемые ОТНОСИТЕЛЬНО ROOT (а не по абсолютному пути — иначе репо под tmp-work не сканится).
SKIP_TOP = (".git", "tmp-work", "__pycache__")


def _decision_ids():
    ids = []
    for p in sorted(glob.glob(os.path.join(ROOT, "decisions", "D-*.md"))):
        ids.append(os.path.basename(p)[:-3])
    return ids


def _counts():
    """Число ФАЙЛОВ, упоминающих каждое D-NNN (как в исходной таблице дока)."""
    counts = {}
    for pat in ("**/*.md", "**/*.py"):
        for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
            rel = os.path.relpath(p, ROOT)
            if rel.split(os.sep)[0] in SKIP_TOP or "__pycache__" in rel:
                continue
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for did in set(REF.findall(txt)):
                counts[did] = counts.get(did, 0) + 1
    return counts


def scan():
    counts = _counts()
    rows = []
    for did in _decision_ids():
        n = counts.get(did, 0)
        status = "active" if n >= THR_HI else ("moderate" if n >= THR_LO else "dead-weight")
        rows.append({"id": did, "files": n, "status": status})
    return rows


def main(argv):
    help_guard(__doc__, argv)
    rows = scan()
    if "--dead" in argv:
        rows = [r for r in rows if r["status"] == "dead-weight"]
    if "--json" in argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    mark = {"active": "✅", "moderate": "🟡", "dead-weight": "⚪"}
    print("=== ИСПОЛЬЗОВАНИЕ РЕШЕНИЙ D-XXX (файлов-ссылок; ≥%d active · ≥%d moderate) ===" % (THR_HI, THR_LO))
    for r in rows:
        print("  %s %-7s %3d файл(ов)  %s" % (mark.get(r["status"], "?"), r["id"], r["files"], r["status"]))
    dead = sum(1 for r in rows if r["status"] == "dead-weight")
    print("\nвсего: %d решений · мёртвый-груз: %d" % (len(rows), dead))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
