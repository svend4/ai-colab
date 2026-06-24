#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_sandbox_runner
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_sandbox_runner.py. Описание сгенерировано автоматически.
# ==========================================
"""
import os
import sys
import unittest
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import sandbox_runner
import execute_human_gate

class TestSandboxRunner(unittest.TestCase):
    @patch('subprocess.run')
    def test_run_sandbox_success(self, mock_run):
        # Setup mock to simulate a successful preflight and docker run
        class DummyProcess:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
                
        def side_effect(cmd, *args, **kwargs):
            if "execute_preflight.py" in cmd[1]:
                # preflight check returns success
                return DummyProcess(0, "OK: All passed", "")
            elif cmd[0] == "docker":
                # docker run returns success
                return DummyProcess(0, "hello sandbox", "")
            return DummyProcess(1, "", "Unknown command")

        mock_run.side_effect = side_effect
        
        exit_code = sandbox_runner.run_sandbox("test-driver", "alpine", ["echo", "hello sandbox"])
        self.assertEqual(exit_code, 0)
        
        # Verify that subprocess was called exactly twice (preflight, then docker run)
        self.assertEqual(mock_run.call_count, 2)
        
        # Check docker command structure
        docker_cmd_call = mock_run.call_args_list[1][0][0]
        self.assertEqual(docker_cmd_call[0:3], ["docker", "run", "--rm"])
        self.assertIn("--network", docker_cmd_call)
        self.assertIn("none", docker_cmd_call)
        self.assertIn("--pids-limit", docker_cmd_call)
        self.assertIn("alpine", docker_cmd_call)
        self.assertEqual(docker_cmd_call[-2:], ["echo", "hello sandbox"])

    @patch('subprocess.run')
    def test_run_sandbox_preflight_fail(self, mock_run):
        class DummyProcess:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
                
        def side_effect(cmd, *args, **kwargs):
            if "execute_preflight.py" in cmd[1]:
                # preflight check returns failure
                return DummyProcess(1, "ERROR: Preflight failed", "")
            return DummyProcess(1, "", "")

        mock_run.side_effect = side_effect
        
        exit_code = sandbox_runner.run_sandbox("test-driver", "alpine", ["echo", "hello sandbox"])
        self.assertEqual(exit_code, 1)
        
        # Subprocess should be called only once (preflight fails -> no docker run)
        self.assertEqual(mock_run.call_count, 1)

if __name__ == "__main__":
    unittest.main()
