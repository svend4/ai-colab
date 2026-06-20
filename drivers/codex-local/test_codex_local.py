#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты codex-local driver (работают независимо от наличия Codex)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codex_local as cl


def run():
    ok = True
    try:
        av = cl.available()
        assert isinstance(av, bool), "available() не bool"

        inf = cl.info()
        assert "available" in inf, "info() без ключа available"

        # whitelist: небезопасный флаг должен отвергаться
        try:
            cl._run_safe("--evil")
            assert False, "whitelist не enforce — пропущен небезопасный флаг"
        except ValueError:
            pass

        print("TESTS OK available=%s" % av)
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
