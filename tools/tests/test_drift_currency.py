#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_drift_currency
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_drift_currency.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест _assurance_currency_drift (tools/drift_check.py) — только HIGH currency-находки → дрейф."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import json

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import drift_check as dc


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    try:
        sample = json.dumps({"sections": [{"name": "currency", "findings": [
            {"level": "high", "msg": "docs/x.md: битая структурная ссылка на decisions/D-999.md"},
            {"level": "high", "msg": "docs/y.md: ссылается на D-002 со статусом superseded"},
            {"level": "info", "msg": "accepted-доков без last_verified: 20"},
            {"level": "medium", "msg": "что-то medium"},
        ]}]})
        drift = dc._assurance_currency_drift(sample)
        assert len(drift) == 2, "только 2 HIGH должны попасть в дрейф: %s" % drift
        assert all("assurance currency:" in d for d in drift), drift
        assert any("битая структурная" in d for d in drift) and any("superseded" in d for d in drift), drift
        assert not any("last_verified" in d for d in drift), "info-нудж НЕ дрейф: %s" % drift

        # мусор / пусто → пусто, без падений
        assert dc._assurance_currency_drift("") == []
        assert dc._assurance_currency_drift("not json{") == []
        assert dc._assurance_currency_drift(json.dumps({"sections": []})) == []

        print("TESTS OK drift currency: HIGH→дрейф, info/medium игнор, мусор безопасен")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
