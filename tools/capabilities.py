#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Capability manifest (C1, консенсус Claude+Codex) — один машиночитаемый файл «что умеет слой».

Генерирует `system-capabilities.json` детерминированно из манифестов драйверов + курируемой
карты команд/доков. Идея: агент при подключении читает ОДИН файл и сразу знает свои возможности,
не перечитывая историю. Файл — производный (как index.json): правишь источники → перегенерируешь.

    python tools/capabilities.py snapshot   # записать system-capabilities.json
    python tools/capabilities.py --check     # проверить свежесть (для drift/pre-commit)
"""
import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _canon import parse_front_matter  # единый парсер front-matter (T-085)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS = os.path.join(ROOT, "drivers")
OUT = os.path.join(ROOT, "system-capabilities.json")


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _list(value):
    s = (value or "").strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip() for x in s.split(",") if x.strip()]


# Курируемая карта ключевых команд входа (как пользоваться слоем).
COMMANDS = [
    {"cmd": "python tools/top.py buttons", "does": "верхняя панель сценариев для людей и агентов"},
    {"cmd": "python tools/top.py health", "does": "групповая проверка здоровья канона"},
    {"cmd": "python tools/top.py report-diff reports/a.md reports/b.md --out reports/diff.md", "does": "сравнить два knowledge-отчёта"},
    {"cmd": "python tools/cohort.py board", "does": "dashboard параллельной многоагентной работы"},
    {"cmd": "python tools/cohort.py self --json", "does": "самопроверка движка и next maintenance hints"},
    {"cmd": "python tools/variants.py list --topic <topic>", "does": "найти fork-варианты для синтеза"},
    {"cmd": "python tools/synthesis_helper.py report <topic> --out темы/<topic>-synthesis.md", "does": "собрать scaffold синтеза из fork-вариантов"},
    {"cmd": "python tools/merge_gate.py check <agent>", "does": "read-only merge gate перед вливанием"},
    {"cmd": "python tools/stream.py list [topic]", "does": "список semi-commit stream-пакетов"},
    {"cmd": "python tools/promote.py check --artifact <path>", "does": "проверить promotion L4→L3→L2→L1"},
    {"cmd": "python tools/sandbox_intake_demo.py --out tmp-work/sandbox-demo", "does": "read-only demo intake внешнего источника"},
    {"cmd": "python tools/demo_bridge.py", "does": "увидеть слой в действии (read-only)"},
    {"cmd": "python tools/pipeline.py status", "does": "состояние конвейера задач"},
    {"cmd": "python tools/pipeline.py next <agent>", "does": "атомарно взять следующую ready-задачу"},
    {"cmd": "python tools/pipeline.py claim <agent> <T-id>", "does": "атомарно взять конкретную ready-задачу без wrong-next"},
    {"cmd": "python tools/validate.py", "does": "проверить канон (ERROR=0)"},
    {"cmd": "python tools/knowledge.py report <корпус> --query <t>", "does": "L6 ingest→query→report"},
    {"cmd": "python tools/knowledge.py search <db> <t>", "does": "ранжированный поиск FTS5"},
    {"cmd": "python drivers/mcp_sync_acceptance.py", "does": "переносимая MCP tools/call приёмка"},
]

DOCS = {
    "onboarding_human": "docs/agent-onboarding.md",
    "onboarding_agent": "docs/top-agent-operating-manual.md",
    "usage": "docs/bridge-usage.md",
    "layers": "docs/layers-coverage.md",
    "driver_catalog": "drivers/CATALOG.md",
    "rules": "AGENTS.md",
    "skills": "skills/README.md",
}


def build():
    drivers = []
    for fn in sorted(os.listdir(DRIVERS)):
        if not fn.endswith(".md") or fn in {"README.md", "SCHEMA.md"} or fn.startswith("_"):
            continue
        with open(os.path.join(DRIVERS, fn), encoding="utf-8") as f:
            fm = parse_front_matter(f.read())
        if fm.get("type") != "driver":
            continue
        drivers.append({
            "id": fm.get("id"),
            "title": fm.get("title", ""),
            "status": fm.get("status"),
            "level": fm.get("level"),
            "mode": fm.get("mode"),
            "risk": fm.get("risk"),
            "audit": fm.get("audit") == "true",
            "tools": _list(fm.get("tools") or fm.get("interfaces")),
        })
    drivers.sort(key=lambda d: d.get("id") or "")
    ready = sum(1 for d in drivers if d.get("status") == "ready")
    return {
        "system": "AI-OS Bridge / Information Workbench Layer",
        "purpose": "Средний слой между AI-клиентом и Windows/файлами/репозиториями/данными",
        "stage": "Рабочий read-only прототип среднего слоя (не execute-платформа)",
        "default_mode": "read-only",
        "execute_policy": "forbidden_until_sandbox_and_accepted_decision (D-010, находка G)",
        "driver_status_gate": "D-015 (код работает + сверка >=2 агентами)",
        "drivers_total": len(drivers),
        "drivers_ready": ready,
        "drivers": drivers,
        "commands": COMMANDS,
        "docs": DOCS,
        "note": "Производный файл: генерируется tools/capabilities.py из drivers/*.md. Не править руками.",
    }


def _dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def snapshot():
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(_dumps(build()) + "\n")
    print("SNAPSHOT: system-capabilities.json — драйверов %d (ready %d)"
          % (build()["drivers_total"], build()["drivers_ready"]))
    return 0


def check():
    want = _dumps(build())
    if not os.path.exists(OUT):
        print("STALE: system-capabilities.json отсутствует — запусти snapshot")
        return 1
    with open(OUT, encoding="utf-8") as f:
        have = f.read().rstrip("\n")
    if have != want:
        print("STALE: system-capabilities.json устарел — запусти: python tools/capabilities.py snapshot")
        return 1
    print("OK: system-capabilities.json актуален")
    return 0


def main():
    a = sys.argv[1:]
    if a and a[0] == "snapshot":
        return snapshot()
    if a and a[0] == "--check":
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
