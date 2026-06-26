#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.independent_pipeline
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Оркестратор конвейера независимого консенсуса (D-030) — соединяет 7 тулов оракула в один прогон.
# ==========================================
"""independent_pipeline.py — мета-доска конвейера независимого консенсуса (D-030).

GROW-ONLY connector (контр-инвариант C-II формулы): соединяет 7 ранее-orphan тулов аппарата
семантического оракула в ОДИН прогон по фазам из docs/independent-first-pipeline.md. Существующие
тулы не трогаются — оркестратор только вызывает их `--board` и агрегирует вывод в единую доску:

  2 ripeness_gate · 3 portals · 4 independence_measure · 5 consensus_by_meaning ·
  6 divergence_detail · 7 red_team_gate · 8 oracle_quorum

До этого consensus_by_meaning и oracle_quorum были orphan-корнями (ничто их не вызывало); этот
connector делает весь конвейер D-030 запускаемым одной командой и видимым как целое.

CLI:
  python tools/independent_pipeline.py            # мета-доска всех фаз (--board каждого тула)
  python tools/independent_pipeline.py <topic>    # фазы 4-5 по конкретной теме variants/<topic>/
  python tools/independent_pipeline.py --json
"""
import os
import sys
import json
import subprocess

from _ioutil import configure_output
from _cli import help_guard

configure_output()
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(TOOLS)

# (номер фазы, имя, тул, аргумент для board-режима) — порядок из docs/independent-first-pipeline.md
PHASES = [
    ("2", "Гейт зрелости + печати (вход)", "ripeness_gate", "--board"),
    ("3", "Порталы (средний слой И-8)", "portals", "--board"),
    ("4", "Мера независимости (стена №2)", "independence_measure", "--board"),
    ("5", "Консенсус по смыслу", "consensus_by_meaning", "--board"),
    ("6", "Детализация расхождений", "divergence_detail", "--board"),
    ("7", "Red-team-гейт (выход)", "red_team_gate", "--board"),
    ("8", "Оракул-кворум", "oracle_quorum", "--board"),
]
# фазы, у которых есть осмысленный per-topic режим (вместо --board)
PER_TOPIC = {"independence_measure", "consensus_by_meaning"}


def _run(tool, *args):
    cmd = [sys.executable, os.path.join(TOOLS, tool + ".py"), *args]
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", stdin=subprocess.DEVNULL, timeout=120)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:  # инструмент не упасть не должен ронять оркестратор
        return 1, "", str(exc)


def _variant_topics():
    vdir = os.path.join(ROOT, "variants")
    if not os.path.isdir(vdir):
        return []
    return sorted(d for d in os.listdir(vdir) if os.path.isdir(os.path.join(vdir, d)))


def run(topic=None):
    rows = []
    topics = _variant_topics()
    rows.append({"phase": "1", "name": "Производство (вслепую)", "tool": None, "rc": 0,
                 "summary": "%d тем в variants/%s" % (len(topics), (" · фокус: " + topic) if topic else "")})
    for num, name, tool, board in PHASES:
        if topic and tool in PER_TOPIC:
            rc, so, se = _run(tool, topic)
        else:
            rc, so, se = _run(tool, board)
        rows.append({"phase": num, "name": name, "tool": tool, "rc": rc, "summary": so or se})
    return rows


def _print(rows):
    print("=== КОНВЕЙЕР НЕЗАВИСИМОГО КОНСЕНСУСА (D-030) — мета-доска ===")
    print("grow-only оркестратор: ripeness_gate · portals · independence_measure · consensus_by_meaning · "
          "divergence_detail · red_team_gate · oracle_quorum")
    for r in rows:
        tag = "✓" if r["rc"] == 0 else "✗ rc%s" % r["rc"]
        print("\nФаза %s. %s%s  [%s]" % (r["phase"], r["name"],
              (" · %s" % r["tool"]) if r["tool"] else "", tag))
        body = (r["summary"] or "").splitlines()
        for ln in body[:6]:
            print("    " + ln)
        if len(body) > 6:
            print("    … (+%d строк — python tools/%s.py --board)" % (len(body) - 6, r["tool"]))


def main(argv):
    help_guard(__doc__, argv)
    topic = None
    for a in argv:
        if not a.startswith("-"):
            topic = a
    rows = run(topic)
    if "--json" in argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        _print(rows)
    return 0  # доска, не гейт


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
