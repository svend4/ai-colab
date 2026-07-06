# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_queue
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_queue.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест queue.py — совместимостный алиас на agent_queue.py (делегирование).

Subprocess-smoke (избегаем теневого импорта stdlib `queue`): `queue.py check` должен дать rc=0 и
напечатать в stderr имя канонического модуля agent_queue.
"""
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
import subprocess

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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
