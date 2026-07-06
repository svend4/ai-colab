# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_synthesis_helper
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_synthesis_helper.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест synthesis_helper (tools/synthesis_helper.py) — скелет синтеза из форк-вариантов.

Read-only против реального репо: тема agent-onboarding имеет 2 варианта (Claude doc + Codex doc),
поэтому она должна быть кандидатом и давать осмысленный скелет."""
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
import subprocess

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _run(*args):
    p = subprocess.run([sys.executable, os.path.join(HERE, "synthesis_helper.py"), *args],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def run():
    ok = True
    try:
        # topics --json: agent-onboarding имеет 2 варианта -> кандидат
        rc, out = _run("topics", "--json")
        d = json.loads(out)
        assert "agent-onboarding" in d, "agent-onboarding нет в кандидатах: %s" % list(d)[:5]
        assert len(d["agent-onboarding"]) >= 2, "должно быть >=2 вариантов"

        # report agent-onboarding: скелет с нужными секциями + оба файла
        rc, out = _run("report", "agent-onboarding")
        assert rc == 0, "report rc=%d" % rc
        for marker in ("Синтез (скелет)", "## Варианты", "Консенсус", "Расхождения",
                       "Двойная перепроверка", "docs/agent-onboarding.md",
                       "docs/top-agent-operating-manual.md"):
            assert marker in out, "нет %r в скелете" % marker
        # status: proposed — материал, не решение
        assert "status: proposed" in out, "скелет должен быть proposed"

        # неизвестная тема -> rc=1, без падения
        rc, out = _run("report", "no-such-topic-xyz")
        assert rc == 1, "неизвестная тема должна давать rc=1"

        print("TESTS OK synthesis_helper: topics-кандидаты + скелет (стороны/консенсус/расхождения/D-018)")
    except (AssertionError, ValueError) as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
