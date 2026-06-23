#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест _assurance_currency_drift (tools/drift_check.py) — только HIGH currency-находки → дрейф."""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
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
