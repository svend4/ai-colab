#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermetic tests for tools/sandbox_intake_demo.py.

Run the demo into a TEMP --out dir and assert:
  - the S7 inventory report is non-empty and lists fixture files;
  - the S1 manifest is read-only and the demo never takes an execute path
    (no `mode: execute`, no run/execute call into the inventory driver).
No real streams/, sandbox/reports, or collab dirs are touched.
"""
import importlib.util
import os
import sys
import shutil
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_PATH = os.path.join(ROOT, "tools", "sandbox_intake_demo.py")
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir


def _load_demo():
    spec = importlib.util.spec_from_file_location("sandbox_intake_demo_under_test", DEMO_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SandboxIntakeDemoTest(unittest.TestCase):
    def setUp(self):
        self.demo = _load_demo()
        self.out = make_temp_dir("sandbox_intake_demo_test_")

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_demo_produces_nonempty_inventory_listing_fixtures(self):
        result = self.demo.run_demo(out_dir=self.out)

        report_path = result["report"]
        manifest_path = result["manifest"]

        # Outputs must live under the temp --out dir (hermetic).
        self.assertTrue(os.path.abspath(report_path).startswith(os.path.abspath(self.out)))
        self.assertTrue(os.path.abspath(manifest_path).startswith(os.path.abspath(self.out)))

        self.assertTrue(os.path.isfile(report_path), "report not written")
        with open(report_path, encoding="utf-8") as fh:
            report = fh.read()
        self.assertTrue(report.strip(), "inventory report is empty")

        # Report reflects the fixture source.
        self.assertIn("data", report)
        self.assertIn("fixtures", report)

        # The demo's read-only S3 scan must have inventoried the fixture files.
        self.assertIsNotNone(result.get("inventoried_files"))
        self.assertGreater(int(result["inventoried_files"]), 0, "no fixture files inventoried")
        structure = result.get("structure") or []
        self.assertIn("sample-data.json", structure)
        self.assertIn("README.md", structure)

    def test_manifest_is_read_only_no_execute_mode(self):
        result = self.demo.run_demo(out_dir=self.out)
        with open(result["manifest"], encoding="utf-8") as fh:
            manifest = fh.read()
        self.assertIn("mode: read-only", manifest)
        self.assertNotIn("mode: execute", manifest)

        with open(result["report"], encoding="utf-8") as fh:
            report = fh.read()
        self.assertNotIn("mode: execute", report)

    def test_demo_never_calls_a_run_or_execute_path(self):
        # The inventory driver loaded by sandbox.py has NO execute/run API; the
        # demo must rely solely on read-only scan_repo. Two guards:
        #   1) the driver must expose no run/execute callable at all;
        #   2) if such a callable were ever introduced and invoked, fail.
        sb = self.demo._load_sandbox()
        inv = sb.inv

        # (1) Structural guard: no execute/run surface exists on the driver.
        run_like = [n for n in dir(inv)
                    if n in ("execute", "run", "run_repo", "execute_repo")
                    and callable(getattr(inv, n))]
        self.assertEqual(run_like, [], "inventory driver exposes a run/execute API")

        # (2) Behavioral guard: trap any such callable if it ever appears, and
        # positively assert the read-only scan_repo IS the path actually taken.
        for name in ("execute", "run", "run_repo", "execute_repo"):
            def _boom(*a, _n=name, **k):
                raise AssertionError("execute path invoked: inventory.%s" % _n)
            setattr(inv, name, _boom)

        called = {"scan": 0}
        real_scan = inv.scan_repo

        def _tracked_scan(*a, **k):
            called["scan"] += 1
            return real_scan(*a, **k)

        inv.scan_repo = _tracked_scan
        try:
            result = self.demo.run_demo(out_dir=self.out, _sandbox=sb)
        finally:
            inv.scan_repo = real_scan
        self.assertTrue(os.path.isfile(result["report"]))
        self.assertGreater(called["scan"], 0,
                           "demo did not perform the read-only scan_repo path")

    def test_out_dir_isolation_does_not_touch_real_sandbox(self):
        real_reports = os.path.join(ROOT, "sandbox", "reports", "%s-inventory.md" % self.demo.DEMO_ID)
        existed_before = os.path.exists(real_reports)
        self.demo.run_demo(out_dir=self.out)
        existed_after = os.path.exists(real_reports)
        # Using --out must not create/modify the real sandbox report.
        self.assertEqual(existed_before, existed_after,
                         "demo with --out polluted real sandbox/reports")


if __name__ == "__main__":
    unittest.main()
