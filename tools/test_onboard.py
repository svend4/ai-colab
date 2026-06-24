#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_onboard
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_onboard.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест onboard (tools/onboard.py) — агрегатор входа."""
import os
import sys
import io
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
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
