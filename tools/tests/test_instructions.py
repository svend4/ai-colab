#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_instructions
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_instructions.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Tests for tools/instructions.py (T-154)."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import json
import os
import subprocess
import sys

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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

    agent_payload = instructions.build_preflight("codex")
    agent_ids = {item["id"] for item in agent_payload["instructions"]}
    assert agent_payload["task"] is None, agent_payload
    assert "human-map" in agent_ids and "agent-onboarding" in agent_ids, agent_ids
    assert "task-card" not in agent_ids, agent_ids
    assert "<not specified>" in instructions.format_preflight(agent_payload), agent_payload

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

    rc, out = _run("preflight", "codex", "--json")
    assert rc == 0, out
    data = json.loads(out)
    assert data["task"] is None, data
    assert any(i["path"] == "docs/agent-onboarding.md" for i in data["instructions"]), data

    rc, out = _run("preflight", "codex", "T-154", "--json")
    assert rc == 0, out
    data = json.loads(out)
    assert data["task"]["id"] == "T-154", data
    assert any(i["path"] == "docs/instruction-assurance.md" for i in data["instructions"]), data

    ok_report = """# Report\n\n## Applied instructions\n\n- `AGENTS.md` / `PROTOCOL.md`: ok.\n- Checks: python tools/validate.py -> OK.\n"""
    assert instructions.check_report_text(ok_report) == []
    ok_done = """---\ntask: T-156\nagent: codex\napplied: AGENTS.md, PROTOCOL.md, docs/instruction-assurance.md\n---\n\nDone.\n\nApplied instructions: AGENTS.md, PROTOCOL.md\n"""
    assert instructions.check_report_text(ok_done) == []
    no_checks = """# Report\n\n## Applied instructions\n\n- `AGENTS.md` / `PROTOCOL.md`: ok.\n"""
    assert "Checks:" in instructions.check_report_text(no_checks)
    bad = instructions.check_report_text("# Report\n")
    assert "Applied instructions evidence" in bad, bad

    assert instructions.report_reference_findings(ok_report) == []
    missing_doc = ok_report + "\nSee `docs/does-not-exist.md`.\n"
    findings = instructions.report_reference_findings(missing_doc)
    assert any("referenced path not found: docs/does-not-exist.md" in x for x in findings), findings
    missing_script = ok_report.replace("tools/validate.py", "tools/nope.py")
    findings = instructions.report_reference_findings(missing_script)
    assert any("checks command references missing script: tools/nope.py" in x for x in findings), findings
    bogus_cmd = ok_report.replace("python tools/validate.py", "frobnicate the repo")
    findings = instructions.report_reference_findings(bogus_cmd)
    assert any("checks command not runnable-shape: frobnicate the repo" in x for x in findings), findings
    noisy_words = ok_report + "\nMention applied/currency/coverage/flow, ревью/CI, `top.py`, and Checks: as prose.\n"
    findings = instructions.report_reference_findings(noisy_words)
    assert findings == [], findings

    print("TESTS OK instructions: manifest/preflight/check-report/advisory refs")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
