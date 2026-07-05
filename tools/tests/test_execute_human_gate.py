#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_execute_human_gate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_execute_human_gate.py. Описание сгенерировано автоматически.
# ==========================================
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
import unittest
import shutil
import uuid

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)

import execute_human_gate

ROOT = os.path.dirname(HERE)

def make_project_tmp(prefix):
    base = os.path.join(ROOT, "tmp-work")
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, f"{prefix}{uuid.uuid4().hex}")
    os.makedirs(path)
    return path

class TestExecuteHumanGate(unittest.TestCase):
    def setUp(self):
        # Redirect the approvals dir for testing
        self.old_get_approval_file = execute_human_gate._get_approval_file
        self.test_dir = make_project_tmp("human_gate_test_")
        execute_human_gate._get_approval_file = lambda driver_id: os.path.join(self.test_dir, f"{driver_id}_approval.md")

    def tearDown(self):
        execute_human_gate._get_approval_file = self.old_get_approval_file
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_request_and_check(self):
        driver_id = "test-driver"
        
        # 1. Check should fail before request
        self.assertEqual(execute_human_gate.check_approval(driver_id), 1)
        
        # 2. Request approval
        execute_human_gate.request_approval(driver_id, "echo hello")
        approval_file = execute_human_gate._get_approval_file(driver_id)
        self.assertTrue(os.path.exists(approval_file))
        
        # 3. Check should still fail because it's 'requested'
        self.assertEqual(execute_human_gate.check_approval(driver_id), 1)
        
        # 4. Simulate human approval
        with open(approval_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("status: requested", "status: approved")
        with open(approval_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            
        # 5. Check should now succeed
        self.assertEqual(execute_human_gate.check_approval(driver_id), 0)

if __name__ == "__main__":
    unittest.main()
