#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.execute_human_gate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт execute_human_gate.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Механизм человеко-подтверждения для execute-sandbox (Gate 10).
Обеспечивает соблюдение D-006 (явное разрешение на запуск).

Использование:
    python tools/execute_human_gate.py request <driver_id> "<cmd_pattern>"
    python tools/execute_human_gate.py check <driver_id>
"""
import os
import sys
import re
from datetime import datetime
from _ioutil import configure_output

configure_output()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def _get_approval_file(driver_id):
    # Для упрощения Gate 10 использует отдельную папку подтверждений,
    # которая может управляться человеком напрямую или через D-карточки.
    approvals_dir = os.path.join(ROOT, "sandbox", "approvals")
    os.makedirs(approvals_dir, exist_ok=True)
    return os.path.join(approvals_dir, f"{driver_id}_approval.md")

def request_approval(driver_id, cmd_pattern):
    approval_file = _get_approval_file(driver_id)
    if os.path.exists(approval_file):
        print(f"Approval file already exists for {driver_id}")
        return 0
        
    content = f"""---
id: approval-{driver_id}
type: human-gate-approval
driver: {driver_id}
status: requested
date: {datetime.now().strftime("%Y-%m-%d")}
---

# Запрос на исполнение: {driver_id}

**Команда/Паттерн:** `{cmd_pattern}`

## Внимание (Gate 10)
Этот драйвер запрашивает разрешение на `mode: execute`.
Чтобы разрешить запуск, измените `status: requested` на `status: approved` в front-matter этого файла.

**Сценарий использования:** 
(Опишите зачем нужен запуск)
"""
    with open(approval_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Generated approval request for {driver_id} at {approval_file}")
    return 0

def check_approval(driver_id):
    approval_file = _get_approval_file(driver_id)
    if not os.path.exists(approval_file):
        print(f"ERROR: No human approval requested or found for {driver_id} (Gate 10)")
        return 1
        
    with open(approval_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    match = re.search(r"^status:\s*(.+)$", content, re.MULTILINE)
    if not match:
        print(f"ERROR: Could not parse status in {approval_file}")
        return 1
        
    status = match.group(1).strip()
    if status == "approved":
        print(f"OK: Human approval confirmed for {driver_id} (Gate 10)")
        return 0
    else:
        print(f"ERROR: Human approval for {driver_id} is '{status}', not 'approved'")
        return 1

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
        
    cmd = args[0]
    if cmd == "request":
        if len(args) < 3:
            print("Usage: execute_human_gate.py request <driver_id> <cmd_pattern>")
            return 2
        return request_approval(args[1], args[2])
    elif cmd == "check":
        if len(args) < 2:
            print("Usage: execute_human_gate.py check <driver_id>")
            return 2
        return check_approval(args[1])
    else:
        print(f"Unknown command: {cmd}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
