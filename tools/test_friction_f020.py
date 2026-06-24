#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_friction_f020
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_friction_f020.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест F-020 gate-poison (tools/friction.py) — детектор + резолв сломанного cross-link + роутинг L1."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import friction as f


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    try:
        # отравлённый гейт (validate ERROR>0, rc=1) → warn F-020 с evidence
        poison = f.check_gate_poison(1, "ERROR: T-099 done но tasks/T-099.md нет\n----\nOK=40 WARN=2 ERROR=1\n")
        assert poison["id"] == "F-020" and poison["status"] == "warn", poison
        assert any("ERROR" in ev for ev in poison["evidence"]), poison
        # чистый гейт → ok
        clean = f.check_gate_poison(0, "OK=42 WARN=0 ERROR=0\n")
        assert clean["id"] == "F-020" and clean["status"] == "ok", clean
        # rc!=0 даже без ERROR= строки → warn (truncated output)
        assert f.check_gate_poison(1, "")["status"] == "warn"

        # КЛЮЧЕВОЕ: сломанный сегодня cross-link cohort→friction теперь резолвится
        assert f.resolve_fid("gate-poison") == "F-020", "alias gate-poison должен резолвиться в F-020"
        assert f.resolve_fid("F-020") == "F-020"
        assert "validate.py" in f.recipe_text("F-020"), "рецепт ссылается на validate.py"

        # отравлённый гейт роутится в сильный вердикт (не git add -A)
        rec = f.recommendation([poison])
        assert "LEVEL 1" in rec or "SELECTIVE-ADD" in rec, rec

        print("TESTS OK F-020 gate-poison: детектор(poison/clean/truncated) + резолв cross-link gate-poison→F-020 + роутинг L1")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
