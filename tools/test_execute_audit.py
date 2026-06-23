#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import unittest
import shutil
import tempfile
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import execute_audit

class TestExecuteAudit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.logger = execute_audit.AuditLogger(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_prepare_workspace(self):
        work_dir, out_dir = self.logger.prepare_workspace()
        self.assertTrue(os.path.exists(work_dir))
        self.assertTrue(os.path.exists(out_dir))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "reports")))
        self.assertIsNotNone(self.logger.audit_file)

    def test_record_start_finish(self):
        self.logger.prepare_workspace()
        self.logger.record_start(["echo", "hello"])
        
        with open(self.logger.audit_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["status"], "running")
            self.assertEqual(data["command"], ["echo", "hello"])
            
        self.logger.record_finish(0, "hello\n", "", 1.0)
        
        with open(self.logger.audit_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["status"], "finished")
            self.assertEqual(data["exit_code"], 0)
            self.assertTrue("output_file" in data)
            
            output_file = data["output_file"]
            self.assertTrue(os.path.exists(output_file))
            with open(output_file, "r", encoding="utf-8") as of:
                content = of.read()
                self.assertIn("hello\n", content)

    def test_collect_diff(self):
        work_dir, out_dir = self.logger.prepare_workspace()
        self.logger.record_start(["touch", "test.txt"])
        
        # Simulate creating a file in out_dir
        with open(os.path.join(out_dir, "test.txt"), "w") as f:
            f.write("test content")
            
        self.logger.record_finish(0, "", "", 0.1)
        diff = self.logger.collect_diff()
        
        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["file"], "test.txt")
        self.assertTrue(diff[0]["size"] > 0)

    def test_rollback(self):
        work_dir, out_dir = self.logger.prepare_workspace()
        self.logger.record_start(["test"])
        self.assertTrue(os.path.exists(work_dir))
        self.logger.rollback()
        self.assertFalse(os.path.exists(work_dir))
        self.assertFalse(os.path.exists(out_dir))

    def test_wrap_and_execute(self):
        # Using python to echo something as it works cross-platform
        cmd = [sys.executable, "-c", "print('hello audit')"]
        
        audit_data = execute_audit.wrap_and_execute(self.test_dir, cmd)
        
        self.assertEqual(audit_data["exit_code"], 0)
        self.assertEqual(audit_data["status"], "finished")
        self.assertTrue(audit_data["rollback_completed"])
        
        # Verify temporary dirs are gone
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, ".sandbox_work")))

if __name__ == "__main__":
    unittest.main()
