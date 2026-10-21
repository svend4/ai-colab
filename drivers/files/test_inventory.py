#!/usr/bin/env python3
"""Self-tests for drivers/files/inventory.py."""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inventory import inventory
from test_tmp import temp_dir


def inventory_temp_dir():
    return temp_dir("files_inventory_")


def test_empty_directory():
    with inventory_temp_dir() as tmp:
        report = inventory(tmp, base_dir=tmp)
        assert report["summary"]["total_files"] == 0
        assert report["summary"]["total_size_bytes"] == 0
        assert report["truncated"] is False
        print("PASS: empty directory")


def test_basic_inventory_and_kinds():
    with inventory_temp_dir() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Hello\n", encoding="utf-8")
        (root / "data.json").write_text('{"a": 1}\n', encoding="utf-8")
        (root / "image.png").write_bytes(b"\x89PNG\r\n")
        (root / "sub").mkdir()
        (root / "sub" / "notes.txt").write_text("notes\n", encoding="utf-8")

        report = inventory(tmp, base_dir=tmp)
        assert report["summary"]["total_files"] == 4
        assert report["summary"]["extensions"][".md"] == 1
        assert report["summary"]["extensions"][".json"] == 1
        assert report["summary"]["kinds"]["text"] == 3
        assert report["summary"]["kinds"]["image"] == 1
        assert any(item["path"] == "sub/notes.txt" for item in report["files"])
        print("PASS: basic inventory and kinds")


def test_skips_hidden_and_common_dirs_by_default():
    with inventory_temp_dir() as tmp:
        root = Path(tmp)
        (root / ".secret").write_text("hidden\n", encoding="utf-8")
        (root / ".git").mkdir()
        (root / ".git" / "config").write_text("config\n", encoding="utf-8")
        (root / "visible.txt").write_text("visible\n", encoding="utf-8")

        report = inventory(tmp, base_dir=tmp)
        paths = {item["path"] for item in report["files"]}
        assert "visible.txt" in paths
        assert ".secret" not in paths
        assert ".git/config" not in paths
        assert ".git" in report["skipped_dirs"]
        print("PASS: hidden and common dirs skipped")


def test_hash_and_truncation():
    with inventory_temp_dir() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        (root / "b.txt").write_text("bbb", encoding="utf-8")

        report = inventory(tmp, max_files=1, hash_files=True, base_dir=tmp)
        assert report["summary"]["total_files"] == 1
        assert report["truncated"] is True
        assert "sha256" in report["files"][0]
        print("PASS: hash and truncation")


def test_cli_json():
    with inventory_temp_dir() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("aaa", encoding="utf-8")
        script = Path(__file__).with_name("inventory.py")
        completed = subprocess.run(
            [sys.executable, str(script), tmp, "--hash", "--base", tmp],
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        assert report["summary"]["total_files"] == 1
        assert report["files"][0]["sha256"]
        print("PASS: cli json")


if __name__ == "__main__":
    test_empty_directory()
    test_basic_inventory_and_kinds()
    test_skips_hidden_and_common_dirs_by_default()
    test_hash_and_truncation()
    test_cli_json()
    print("\nAll tests passed!")
