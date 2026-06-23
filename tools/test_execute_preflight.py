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

if __name__ == "__main__":
    unittest.main()
