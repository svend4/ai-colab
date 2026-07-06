#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_code_activation
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_code_activation.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Tests for tools/code_activation.py read-only activation planning."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import json
import os
import sys

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import code_activation as ca


def run():
    payload = ca.activation_plan("tools/code_activation.py", driver_id="code-activation-test")
    assert payload["schema"] == "code_activation_plan.v1", payload
    assert payload["mutates"] is False and payload["execution_allowed"] is False, payload
    assert payload["target"]["exists"] is True and payload["target"]["kind"] == "repo-tool", payload
    gates = {g["id"]: g for g in payload["gates"]}
    assert gates["D-014-policy"]["status"] == "ok", gates
    assert gates["specific-accepted-run-decision"]["status"] == "open", gates
    assert any("py_compile" in cmd for cmd in payload["next_commands"]), payload
    json.dumps(payload, ensure_ascii=False)

    missing = ca.activation_plan("missing/not-here.py")
    assert missing["target"]["inside_repo"] is True and missing["target"]["exists"] is False, missing
    assert missing["state"] == "blocked" and any("target-exists" in b for b in missing["blockers"]), missing

    good_cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2", "--pids-limit", "256", "image", "cmd"]
    good = ca.activation_plan("tools/code_activation.py", command=good_cmd)
    assert good["static_command"]["provided"] is True and good["static_command"]["verdict"] == "ok", good

    bad_cmd = ["docker", "run", "--rm", "image", "cmd"]
    bad = ca.activation_plan("tools/code_activation.py", command=bad_cmd)
    assert bad["static_command"]["verdict"] == "blocked", bad
    assert any("network" in issue.lower() or "limits" in issue.lower() for issue in bad["static_command"]["issues"]), bad

    print("TESTS OK code_activation: read-only plan/gates/static-command checks")
    return 0


if __name__ == "__main__":
    sys.exit(run())
