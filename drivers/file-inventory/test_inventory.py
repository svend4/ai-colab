#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-tests for file-inventory driver (T-059)."""
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import inventory
from test_tmp import make_temp_dir


def run():
    tmp = make_temp_dir("file_inventory_test_")
    ok = True
    try:
        root = Path(tmp)
        (root / "README.md").write_text("# Hello\n", encoding="utf-8")
        (root / "run.sh").write_text("echo hi\n", encoding="utf-8")
        (root / ".hidden").write_text("hidden\n", encoding="utf-8")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "skip.js").write_text("x\n", encoding="utf-8")

        report = inventory.scan(tmp)
        paths = {item["path"] for item in report["files"]}
        assert "README.md" in paths, "README.md missing"
        assert "run.sh" in paths, "run.sh missing"
        assert ".hidden" not in paths, "hidden file included by default"
        assert "node_modules/skip.js" not in paths, "skip dir included"
        assert report["summary"]["by_type"]["text"] >= 1, "text type missing"
        assert report["summary"]["risk_flags"]["shell-script"] == 1, "shell risk missing"

        limited = inventory.scan(tmp, max_files=1)
        assert limited["truncated"] is True and len(limited["files"]) == 1, "max_files broken"

        hashed = inventory.scan(tmp, hash_files=True)
        assert any(item.get("sha256") for item in hashed["files"] if item["path"] == "README.md"), "hash missing"

        inside = inventory.resolve_root(".", base_dir=tmp)
        assert str(inside).startswith(tmp), "relative base resolution broken"
        try:
            inventory.resolve_root(os.path.dirname(tmp), base_dir=tmp)
            assert False, "base_dir did not reject outside path"
        except inventory.PathAccessError:
            pass

        md = inventory.render_markdown(report)
        assert "| Path | Size | Type | MIME | Risk |" in md, "markdown output missing table"

        print("TESTS OK files=%d" % report["summary"]["total_files"])
    except AssertionError as exc:
        ok = False
        print("TEST FAIL:", exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(run())
