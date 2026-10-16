#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_cli_inventory
# TYPE: active-script
# DOMAIN: core.cli
# DEPTH_LEVEL: 1
# SUMMARY: Focused tests for tools/cli_inventory.py classification and JSON mode.
# ==========================================
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import io
import json
import os
import shutil
import sys
from contextlib import redirect_stdout


HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cli_inventory as ci


def prepare_root():
    candidates = [
        os.path.join(ROOT, "tmp-work", "cli_inventory_test_runtime"),
    ]
    if os.name == "nt":  # C:\tmp только на Windows; на Linux это относительный путь в cwd
        candidates.insert(0, os.path.join(r"C:\tmp", "ai_colab_cli_inventory_test"))
    last_error = None
    for root in candidates:
        try:
            shutil.rmtree(root, ignore_errors=True)
            os.makedirs(root, exist_ok=True)
            probe = os.path.join(root, ".write_probe")
            with open(probe, "w", encoding="utf-8", newline="\n") as f:
                f.write("ok")
            os.remove(probe)
            return root
        except OSError as exc:
            last_error = exc
    raise RuntimeError("no writable cli_inventory test root: %r" % (last_error,))


def write(root, name, text):
    path = os.path.join(root, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def build_fixtures(root):
    write(root, "argparse_tool.py", '''"""Argparse tool.

CLI:
    python argparse_tool.py --help
"""
import argparse

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')
    write(root, "guard_tool.py", '''"""Guard tool.

CLI:
    python guard_tool.py --help
"""
import sys
from _cli import help_guard

def main(argv):
    help_guard(__doc__, argv)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
''')
    write(root, "manual_tool.py", '''"""Manual help tool."""
import sys

def main(argv):
    if "--help" in argv:
        print("help")
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
''')
    write(root, "unsafe_tool.py", '''"""Unsafe argv tool."""
import sys

def main(argv):
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
''')
    write(root, "library.py", '''"""Library only."""

def helper():
    return 1
''')


def run():
    tmp = prepare_root()
    try:
        build_fixtures(tmp)
        data = ci.build_report(tmp, include_tests=True)
        by_name = {entry["name"]: entry for entry in data["entries"]}
        assert by_name["argparse_tool.py"]["status"] == "ok-argparse", by_name["argparse_tool.py"]
        assert by_name["guard_tool.py"]["status"] == "ok-help-guard", by_name["guard_tool.py"]
        assert by_name["manual_tool.py"]["status"] == "manual-help", by_name["manual_tool.py"]
        assert by_name["unsafe_tool.py"]["status"] == "unsafe-sysargv", by_name["unsafe_tool.py"]
        assert by_name["library.py"]["status"] == "library-or-helper", by_name["library.py"]
        assert data["totals"]["by_status"]["unsafe-sysargv"] == 1, data["totals"]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ci.main(["--tools-dir", tmp, "--include-tests", "--json"])
        payload = json.loads(buf.getvalue())
        assert code == 0, code
        assert payload["schema"] == "cli_inventory.v1", payload
        assert payload["totals"]["files"] == 5, payload["totals"]

        text = ci.text_report(data, statuses=["unsafe-sysargv"], limit=10)
        assert "unsafe_tool.py" in text, text
        assert "manual_tool.py" not in text, text
        print("OK test_cli_inventory: classification + JSON/text output")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run())