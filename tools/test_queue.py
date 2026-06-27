#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест queue.py — совместимостный алиас на agent_queue.py (делегирование).

Subprocess-smoke (избегаем теневого импорта stdlib `queue`): `queue.py check` должен дать rc=0 и
напечатать в stderr имя канонического модуля agent_queue.
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _ioutil import configure_output  # UTF-8 stdout на Windows
configure_output()
Q = os.path.join(HERE, "queue.py")


def run():
    p = subprocess.run([sys.executable, Q, "check"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    assert p.returncode == 0, "queue.py check rc=%s\n%s" % (p.returncode, p.stderr)
    assert "agent_queue" in p.stderr, "shim должен назвать канонический модуль agent_queue: %r" % p.stderr
    assert "check" in (p.stdout + p.stderr).lower(), "должен делегировать команду check"
    print("TESTS OK queue: алиас делегирует в agent_queue (check rc=0, депрекейшн в stderr)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
