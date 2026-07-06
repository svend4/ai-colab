# ast: allow-subprocess
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_independent_first
# TYPE: active-script
# DOMAIN: core.coordination
# DEPTH_LEVEL: 1
# SUMMARY: Tests for independent-first guard before repo-search/comparison.
# ==========================================
"""
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
import shutil
import subprocess
import sys

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
TOOL = os.path.join(HERE, "independent_first.py")
STREAM_TOOL = os.path.join(HERE, "stream.py")
STREAM_ROOT_REL = os.path.join("tmp-work", "independent-first-test")
STREAM_ROOT = os.path.join(ROOT, STREAM_ROOT_REL)


def run_cmd(args, expect=0):
    p = subprocess.run(
        [sys.executable, TOOL] + args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert p.returncode == expect, (args, p.returncode, p.stdout, p.stderr)
    return p


def create_stream(topic, agent, reason):
    p = subprocess.run(
        [sys.executable, STREAM_TOOL, "create", topic, agent, reason, "--root", STREAM_ROOT_REL],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert p.returncode == 0, (p.stdout, p.stderr)
    # Do not parse localized human output. The contract under test is the file tree.
    matches = []
    for root, _dirs, files in os.walk(STREAM_ROOT):
        if "STREAM.md" in files:
            matches.append(os.path.relpath(os.path.join(root, "STREAM.md"), ROOT).replace(os.sep, "/"))
    assert len(matches) == 1, matches
    return matches[0]


def replace_section(text, marker, body):
    needle = "## " + marker
    start = text.find(needle)
    assert start >= 0, marker
    body_start = text.find("\n", start)
    end = text.find("\n## ", body_start + 1)
    if end < 0:
        end = len(text)
    return text[:body_start + 1] + "\n" + body.strip() + "\n" + text[end:]


def run():
    shutil.rmtree(STREAM_ROOT, ignore_errors=True)
    os.makedirs(STREAM_ROOT, exist_ok=True)

    rel = create_stream("guard-topic", "codex", "template should fail")
    failed = subprocess.run(
        [sys.executable, TOOL, "check", rel, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert failed.returncode == 1, (failed.stdout, failed.stderr)
    payload = json.loads(failed.stdout)
    assert payload["schema"] == "independent_first_check.v1", payload
    assert payload["ready_for_repo_search"] is False, payload
    assert any(i["code"] == "placeholder-section" for i in payload["issues"]), payload

    path = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = replace_section(text, "01. Условия применимости", """
This independent-first guard applies to methodology, architecture, synthesis and variant tasks where early repository search can anchor the answer. It is advisory for narrow bugfix work and strict for new policy design.
""")
    text = replace_section(text, "02. Независимый ответ агента", """
The agent must first write its own model from general to specific: concept, assumptions, expected artifacts, risks, and what would count as a useful result. Similar existing work is not checked until this answer exists.
""")
    text = replace_section(text, "03. Потенциал, который нужно раскрыть до синтеза", """
Algorithm:
1. classify the user request;
2. create a stream without search;
3. write own model;
4. write pseudocode;
5. run independent_first check;
6. only then run repo-search and comparison.

Pseudocode:
if task.kind in {architecture, methodology, variant}:
    stream = create_stream(no_search=True)
    fill_own_sections(stream)
    assert independent_first_check(stream).ok
    repo_search_after_independent_answer()
""")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    ok = json.loads(run_cmd(["check", rel, "--json"]).stdout)
    assert ok["status"] == "ok" and ok["ready_for_repo_search"] is True, ok
    assert ok["has_algorithm_marker"] and ok["has_pseudocode_marker"], ok

    by_id = json.loads(run_cmd(["check", ok["front_matter"]["id"], "--root", STREAM_ROOT_REL, "--json"]).stdout)
    assert by_id["status"] == "ok", by_id

    outside = subprocess.run(
        [sys.executable, TOOL, "check", "x", "--root", ".."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert outside.returncode == 2 and "outside repo" in outside.stderr, outside.stderr

    shutil.rmtree(STREAM_ROOT, ignore_errors=True)
    print("TESTS OK independent_first: template-fails/full-passes/id-lookup/path-safety")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)