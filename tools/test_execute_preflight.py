#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_execute_preflight
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_execute_preflight.py. Описание сгенерировано автоматически.
# ==========================================
"""
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

    # --- Регрессия аудита C8: дырявый Gate 4/5 (host-mount и --net host) ---

    def test_isolation_net_alias_host(self):
        # Алиас --net host раньше проходил рядом с обязательным --network none
        cmd = ["docker", "run", "--rm", "--network", "none", "--net", "host", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Host network is strictly forbidden", msg)

    def test_isolation_net_alias_host_equals(self):
        cmd = ["docker", "run", "--rm", "--network", "none", "--net=host", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Host network is strictly forbidden", msg)

    def test_isolation_network_last_value_wins(self):
        # docker берёт последнее значение: none, затем bridge -> none не действует
        cmd = ["docker", "run", "--network", "none", "--network", "bridge", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Explicit --network none is required", msg)

    def test_isolation_mount_two_arg_userprofile(self):
        # Двухаргументная форма `-v <путь>` раньше вообще не инспектировалась
        cmd = ["docker", "run", "--rm", "--network", "none",
               "-v", "C:\\Users\\stefan:/mnt:rw", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Gate 4", msg)

    def test_isolation_mount_inline_users_without_ssh(self):
        # Слитная форма: весь C:\Users без .ssh раньше проходил
        cmd = ["docker", "run", "--rm", "--network", "none",
               "--volume=C:\\Users\\stefan:/mnt:rw", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Gate 4", msg)

    def test_isolation_mount_ssh_fragment(self):
        cmd = ["docker", "run", "--rm", "--network", "none",
               "-v", "D:\\keys\\.ssh:/keys:ro", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Mounting sensitive host paths is forbidden", msg)

    def test_isolation_mount_docker_sock(self):
        cmd = ["docker", "run", "--rm", "--network", "none",
               "-v", "/var/run/docker.sock:/var/run/docker.sock", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Mounting sensitive host paths is forbidden", msg)

    def test_isolation_mount_flag_source(self):
        # Форма --mount type=bind,source=...
        cmd = ["docker", "run", "--rm", "--network", "none",
               "--mount", "type=bind,source=C:\\Users\\stefan,target=/mnt", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("Gate 4", msg)

    def test_isolation_mount_outside_whitelist(self):
        # Deny-by-default: хостовый путь вне work/out каталогов sandbox запрещён
        cmd = ["docker", "run", "--rm", "--network", "none",
               "-v", "D:\\data:/data:ro", "alpine"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertFalse(ok)
        self.assertIn("outside sandbox work/out whitelist", msg)

    def test_isolation_sandbox_mounts_allowed(self):
        # Реальная команда sandbox_runner.py (work/out из белого списка) проходит
        root = os.path.dirname(HERE)
        work_dir = os.path.join(root, ".sandbox_work")
        out_dir = os.path.join(root, ".sandbox_out")
        cmd = ["docker", "run", "--rm", "--network", "none",
               "--memory", "2g", "--cpus", "2", "--pids-limit", "256",
               "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
               "-v", f"{work_dir}:/work:ro",
               "-v", f"{out_dir}:/out:rw",
               "--workdir", "/work", "alpine", "echo", "hello"]
        ok, msg = execute_preflight.check_sandbox_isolation(cmd)
        self.assertTrue(ok, msg)

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
