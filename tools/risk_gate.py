#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Риск-гейтинг / многоуровневая автономия (Этап E, пункт 6 из scaling-design).

Чтобы D-006 (человек утверждает) не стал бутылочным горлышком при многих
агентах, изменения классифицируются по риску, и только высокорисковые требуют
человека. Источник риска — поле `risk` во front-matter задачи/решения.

    python tools/risk_gate.py <id>     # тир для задачи/решения (T-XXX или D-XXX)
    python tools/risk_gate.py policy   # показать политику

Тиры:
    low    → AUTO   (можно автоутвердить/автомерж при зелёном каноне)
    medium → REVIEW (нужен ревьюер: агент-reviewer или человек)
    high   → HUMAN  (утверждает только человек, D-006)

Это политика-советчик; финальное действие остаётся за человеком/сборщиком.
"""
import os
import sys


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TIER = {
    "low": "AUTO — низкий риск: можно автоутвердить/автомерж при зелёном каноне (validate + generate --check + permissions).",
    "medium": "REVIEW — средний риск: нужен ревьюер (агент-reviewer или человек).",
    "high": "HUMAN — высокий риск: утверждает только человек (D-006).",
    "": "REVIEW — риск не указан: по умолчанию ревью.",
}


def parse_fm(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def find_entity(eid):
    for sub in ("tasks", "decisions", "questions"):
        path = os.path.join(ROOT, sub, eid + ".md")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return parse_fm(f.read())
    return None


def main():
    args = sys.argv[1:]
    if not args:
        print("usage: risk_gate.py <id> | policy")
        return 2
    if args[0] == "policy":
        for k in ("low", "medium", "high"):
            print("  %-6s → %s" % (k, TIER[k]))
        return 0
    eid = args[0]
    fm = find_entity(eid)
    if fm is None:
        print("ERROR: нет задачи/решения %s" % eid)
        return 1
    risk = fm.get("risk", "")
    print("%s [risk=%s, status=%s]" % (eid, risk or "—", fm.get("status", "?")))
    print("  → " + TIER.get(risk, TIER[""]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
