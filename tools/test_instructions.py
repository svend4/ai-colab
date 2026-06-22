#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/instructions.py (T-154)."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instructions


def _run(*args):
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, "instructions.py"), *args],
        cwd=os.path.dirname(HERE),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        timeout=30,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def run():
    manifest = instructions.manifest_payload()["instructions"]
    paths = {item["path"] for item in manifest}
    assert "AGENTS.md" in paths, paths
    assert "PROTOCOL.md" in paths, paths
    assert "docs/top-agent-operating-manual.md" in paths, paths
    assert "docs/instruction-assurance.md" in paths, paths

    payload = instructions.build_preflight("codex", "T-154")
    ids = {item["id"] for item in payload["instructions"]}
    assert "agent-rules" in ids, ids
    assert "collab-protocol" in ids, ids
    assert "task-card" in ids, ids
    assert "task-topic" in ids, ids
    assert payload["task"]["id"] == "T-154", payload["task"]
    rendered = instructions.format_preflight(payload)
    assert "## Applied instructions" in rendered, rendered

    rc, out = _run("manifest", "--json")
    assert rc == 0, out
    data = json.loads(out)
    assert any(i["path"] == "AGENTS.md" for i in data["instructions"]), data

    rc, out = _run("preflight", "codex", "T-154", "--json")
    assert rc == 0, out
    data = json.loads(out)
    assert data["task"]["id"] == "T-154", data
    assert any(i["path"] == "docs/instruction-assurance.md" for i in data["instructions"]), data

    ok_report = """# Report\n\n## Applied instructions\n\n- `AGENTS.md` / `PROTOCOL.md`: ok.\n- Checks: python tools/validate.py -> OK.\n"""
    assert instructions.check_report_text(ok_report) == []
    bad = instructions.check_report_text("# Report\n")
    assert "## Applied instructions" in bad, bad

    print("TESTS OK instructions: manifest/preflight/check-report")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
