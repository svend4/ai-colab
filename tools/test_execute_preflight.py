#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import execute_preflight

class TestExecutePreflight(unittest.TestCase):
    def test_isolation_network_none(self):
        cmd = ["docker", "run", "--rm", "--network", "none", "alpine", "echo", "hello"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertTrue(ok, msg)

    def test_isolation_no_network(self):
        cmd = ["docker", "run", "--rm", "alpine", "echo", "hello"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Explicit --network none is required", msg)

    def test_isolation_host_network(self):
        cmd = ["docker", "run", "--network", "host", "alpine", "echo", "hello"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Host network is strictly forbidden", msg)

    def test_isolation_privileged(self):
        cmd = ["docker", "run", "--network", "none", "--privileged", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Privileged mode is strictly forbidden", msg)

    def test_limits_all_present(self):
        cmd = ["docker", "run", "--network", "none", "--memory", "1g", "--cpus", "1", "--pids-limit", "100", "alpine"]
        ok, msg = execute_preflight.check_sandbox_limits(cmd)
        self.assertTrue(ok, msg)

    def test_limits_missing(self):
        cmd = ["docker", "run", "--network", "none", "--memory", "1g", "alpine"]
        ok, msg = execute_preflight.check_sandbox_limits(cmd)
        self.assertFalse(ok)
        self.assertIn("--cpus", msg)
        self.assertIn("--pids-limit", msg)

    def test_check_all_no_human(self):
        # Even if docker and limits are fine, human approval is missing
        import subprocess
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        preflight_script = os.path.join(here, "execute_preflight.py")
        
        cmd = [
            "python", preflight_script, "check-all", "dummy-driver", "docker",
            "docker", "run", "--rm", "--network", "none", "--memory", "1g", "--cpus", "1", "--pids-limit", "100", "alpine"
        ]
        
        p = subprocess.run(cmd, capture_output=True, text=True)
        # Should fail due to either docker probe timeout or human approval missing
        self.assertNotEqual(p.returncode, 0)
        self.assertTrue("ERROR" in p.stdout or "ERROR" in p.stderr)

if __name__ == "__main__":
    unittest.main()
