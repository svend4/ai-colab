#!/usr/bin/env python3
"""Tests for repo-runner/inventory.py"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add repo-runner to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inventory import scan_repo


def test_scan_empty_repo():
    with tempfile.TemporaryDirectory() as tmp:
        report = scan_repo(tmp)
        assert report["path"] == str(Path(tmp).resolve())
        assert report["summary"]["total_files"] == 0
        assert report["summary"]["total_size_mb"] == 0.0
        assert report["summary"]["has_tests"] is False
        print("PASS: empty repo")


def test_scan_python_repo():
    with tempfile.TemporaryDirectory() as tmp:
        # Create mock Python repo
        (Path(tmp) / "setup.py").write_text("from setuptools import setup\nsetup(name='test')\n")
        (Path(tmp) / "requirements.txt").write_text("requests\npytest\n")
        (Path(tmp) / "src").mkdir()
        (Path(tmp) / "src" / "main.py").write_text("import requests\n")
        (Path(tmp) / "tests").mkdir()
        (Path(tmp) / "tests" / "test_main.py").write_text("def test_main(): pass\n")
        (Path(tmp) / "README.md").write_text("# Test repo\n")

        report = scan_repo(tmp)
        assert report["summary"]["total_files"] == 5
        assert "Python" in report["summary"]["languages"]
        assert report["summary"]["has_tests"] is True
        assert report["summary"]["has_package_files"] is True
        assert len(report["risks"]) > 0  # requests import is a risk pattern
        print("PASS: python repo")


def test_scan_risk_patterns():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "danger.py").write_text("eval('1+1')\n")
        report = scan_repo(tmp)
        assert any(r["risk"] == "potentially dangerous eval" for r in report["risks"])
        print("PASS: risk patterns")


def test_nonexistent_path():
    report = scan_repo("/nonexistent/path/12345")
    assert "error" in report
    print("PASS: nonexistent path")


if __name__ == "__main__":
    test_scan_empty_repo()
    test_scan_python_repo()
    test_scan_risk_patterns()
    test_nonexistent_path()
    print("\nAll tests passed!")
