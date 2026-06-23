#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест trace (tools/instructions.py) — base→apex по shared-ключу surfaces (two-spine, pieces 1+2)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instructions as ins


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    try:
        # D-008 заземлено двумя поверхностями (agent-rules AGENTS.md + collab-protocol PROTOCOL.md)
        r8 = ins.trace("D-008")
        assert r8["grounded"], r8
        ids8 = {s["id"] for s in r8["surfaced_by"]}
        assert {"agent-rules", "collab-protocol"} <= ids8, ids8
        assert r8["apex"] and "assurance" in r8["apex"]

        # case-insensitive; D-009 surface'ится agent-rules + agent-onboarding
        r9 = ins.trace("d-009")
        assert r9["grounded"], r9
        assert {"agent-rules", "agent-onboarding"} <= {s["id"] for s in r9["surfaced_by"]}, r9

        # D-001 (Markdown-аксиома, background-only) — НЕ заземлено (висячее, как и должно)
        r1 = ins.trace("D-001")
        assert not r1["grounded"] and r1["surfaced_by"] == [], r1

        # уровень вычисляется для каждой поверхности (base для root/docs-файлов)
        assert all(s["level"] for s in r8["surfaced_by"]), r8

        # instruction_entry прокидывает surfaces в manifest
        entry = ins.instruction_entry(ins.BY_ID["agent-rules"])
        assert "D-008" in entry["surfaces"] and "D-009" in entry["surfaces"], entry

        # пустой/мусорный ввод безопасен
        assert ins.trace("")["grounded"] is False

        print("TESTS OK instruction trace: surfaces join key + base→apex трассировка (grounded/висячее/level)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
