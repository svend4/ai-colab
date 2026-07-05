#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_onboard
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_onboard.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест onboard (tools/onboard.py) — агрегатор входа."""
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
import io
import contextlib

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import onboard as ob


def run():
    ok = True
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ob.onboard("claude")
        out = buf.getvalue()
        assert rc == 0, rc
        for marker in ("AI-OS Bridge — onboard", "Драйверов:", "конвейере", "Дрейф", "Читать:"):
            assert marker in out, "нет секции %r" % marker
        print("TESTS OK onboard: все секции присутствуют")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
