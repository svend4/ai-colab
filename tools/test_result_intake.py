#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_result_intake
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_result_intake.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Tests for tools/result_intake.py."""
import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir
sys.path.insert(0, HERE)
import result_intake as ri


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _write(base, rel, body):
    path = os.path.join(base, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    return path


def run():
    ok = True
    base = make_temp_dir("result_intake_")
    try:
        build = _write(base, "queues/outbox/build.md", """---
type: report
agent: codex
task: T-178
title: build tool result
---

# Build result

## What changed

Updated `tools/result_intake.py` and `tools/test_result_intake.py`.

## Checks

Checks:
python -m py_compile tools\\result_intake.py
python tools\\test_result_intake.py

## Applied instructions

- `AGENTS.md`
""")
        r = ri.classify_path(build, root=base)
        assert r["class"] == "build-change", r
        assert r["evidence"]["has_applied_instructions"] and r["evidence"]["has_checks"], r
        assert any("py_compile" in x for x in r["recommended_next_checks"]), r

        gov = _write(base, "queues/outbox/gov.md", """---
type: report
status: proposed
title: D-014 human approval packet
---

# Governance

Human approval required before accepted status. This is a proposed decision for D-014.

## Applied instructions

- `decisions/D-006.md`
""")
        r = ri.classify_path(gov, root=base)
        assert r["class"] == "governance", r
        assert r["evidence"]["has_status_proposed"], r

        ext = _write(base, "queues/outbox/external.md", """---
type: report
---

# External code

svend4 source intake must stay in sandbox quarantine. execute stays OFF.
""")
        r = ri.classify_path(ext, root=base)
        assert r["class"] == "external-code", r

        variant = _write(base, "streams/topic/a/STREAM.md", """---
type: stream
---

# Variant

Alternative fork with disagreement evidence.
""")
        r = ri.classify_path(variant, root=base)
        assert r["class"] == "variant", r

        docs = _write(base, "queues/outbox/docs.md", """---
type: report
---

# Documentation update

Updated docs/top-layer-throughput-methodology.md and topics/perspective-backlog-2026-06-23.md.
""")
        r = ri.classify_path(docs, root=base)
        assert r["class"] == "docs-change", r

        report = _write(base, "queues/outbox/audit.md", """---
type: audit
---

# Audit

Read-only summary of current status with no file edits.
""")
        r = ri.classify_path(report, root=base)
        assert r["class"] == "read-only-report", r

        pipeline_py = _write(base, "queues/outbox/pipeline.py", """# pipeline.py
# Updated tools/pipeline.py and implemented a new task runner.
print('hello')
""")
        r = ri.classify_path(pipeline_py, root=base)
        assert r["class"] == "external-code", r
        assert any(s["reason"] == "python source file path" for s in r["signals"]), r

        sandbox_md = _write(base, "sandbox/inbox/source.md", """---
type: report
---

# Intake note

Documentation-like source note from quarantine.
""")
        r = ri.classify_path(sandbox_md, root=base)
        assert r["class"] == "external-code", r
        assert any(s["reason"] == "sandbox path" for s in r["signals"]), r

        p = subprocess.run([
            sys.executable, os.path.join(HERE, "result_intake.py"), "classify", build, "--json",
        ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        assert p.returncode == 0 and '"class": "build-change"' in p.stdout, (p.returncode, p.stdout, p.stderr)

        print("TESTS OK result_intake: classify report/variant/docs/build/governance/external + CLI JSON")
    except AssertionError as exc:
        ok = False
        print("TEST FAIL:", exc)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())