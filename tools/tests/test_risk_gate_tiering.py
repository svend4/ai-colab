#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_risk_gate_tiering
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_risk_gate_tiering.py. Описание сгенерировано автоматически.
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
import shutil
import uuid
import sys
import unittest

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import risk_gate


def make_project_tmp(prefix):
    base = os.path.join(ROOT, "tmp-work")
    os.makedirs(base, exist_ok=True)
    for _ in range(100):
        path = os.path.join(base, prefix + uuid.uuid4().hex[:12])
        try:
            os.makedirs(path, exist_ok=False)
            return path
        except FileExistsError:
            pass
    raise RuntimeError("cannot create project temp dir")


class TestRiskGateTiering(unittest.TestCase):
    def setUp(self):
        self.tmp = make_project_tmp("risk_gate_test_")
        self.old_root = os.environ.get("COLLAB_ROOT")
        os.environ["COLLAB_ROOT"] = self.tmp
        risk_gate.ROOT = self.tmp
        
        os.makedirs(os.path.join(self.tmp, "tasks"))
        os.makedirs(os.path.join(self.tmp, "decisions"))
        
        self.create_entity("tasks", "T-TEST-LOW", "low")
        self.create_entity("decisions", "D-TEST-MED", "medium")
        self.create_entity("tasks", "T-TEST-HIGH", "high")
        self.create_entity("tasks", "T-TEST-NONE", "")
        self.create_entity("tasks", "T-TEST-MISSING", None)
        
    def create_entity(self, subdir, eid, risk):
        path = os.path.join(self.tmp, subdir, eid + ".md")
        content = "---\n"
        if risk is not None:
            content += "risk: %s\n" % risk
        content += "status: proposed\n---\nBody\n"
        with open(path, "w", newline="\n") as f:
            f.write(content)
            
    def tearDown(self):
        shutil.rmtree(self.tmp)
        if self.old_root is not None:
            os.environ["COLLAB_ROOT"] = self.old_root
        else:
            if "COLLAB_ROOT" in os.environ:
                del os.environ["COLLAB_ROOT"]
            
    def test_find_entity(self):
        fm = risk_gate.find_entity("T-TEST-LOW")
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("risk"), "low")
        
        fm_missing = risk_gate.find_entity("T-NOT-EXIST")
        self.assertIsNone(fm_missing)

    def test_tier_mapping(self):
        def get_tier(eid):
            fm = risk_gate.find_entity(eid)
            risk = fm.get("risk", "")
            return risk_gate.TIER.get(risk, risk_gate.TIER[""])

        self.assertTrue("AUTO" in get_tier("T-TEST-LOW"))
        self.assertTrue("REVIEW" in get_tier("D-TEST-MED"))
        self.assertTrue("HUMAN" in get_tier("T-TEST-HIGH"))
        self.assertTrue("REVIEW" in get_tier("T-TEST-NONE"))
        self.assertTrue("REVIEW" in get_tier("T-TEST-MISSING"))

if __name__ == "__main__":
    unittest.main()
