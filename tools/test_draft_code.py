# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_draft_code
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: Tests for the no-execute draft-code packet manager.
# ==========================================
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DRAFT_ROOT_REL = os.path.join("tmp-work", "draft-code-test")
DRAFT_ROOT = os.path.join(ROOT, DRAFT_ROOT_REL)
TOOL = os.path.join(HERE, "draft_code.py")


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


def load_json(stdout):
    return json.loads(stdout)


def run():
    shutil.rmtree(DRAFT_ROOT, ignore_errors=True)
    os.makedirs(DRAFT_ROOT, exist_ok=True)

    p = run_cmd([
        "create",
        "Demo Draft",
        "--owner",
        "codex",
        "--title",
        "Demo Draft",
        "--purpose",
        "exercise no-execute draft manager",
        "--task",
        "T-260",
        "--stream",
        "20260625-1942-codex",
        "--topic",
        "code-variant-draft-manager",
        "--target",
        "tools/example.py",
        "--root",
        DRAFT_ROOT_REL,
        "--json",
    ])
    created = load_json(p.stdout)
    assert created["schema"] == "draft_code_create.v1", created
    assert created["mutates"] is True and created["execution_allowed"] is False, created
    assert created["draft"]["id"] == "demo-draft", created
    draft_path = os.path.join(ROOT, created["draft"]["relpath"].replace("/", os.sep))
    assert os.path.isdir(os.path.join(draft_path, "src")), created
    assert os.path.isdir(os.path.join(draft_path, "tests")), created
    assert os.path.isfile(os.path.join(draft_path, "manifest.json")), created
    assert os.path.isfile(os.path.join(draft_path, "pseudocode.md")), created

    duplicate = subprocess.run(
        [sys.executable, TOOL, "create", "demo-draft", "--owner", "codex", "--purpose", "duplicate", "--root", DRAFT_ROOT_REL],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert duplicate.returncode != 0 and "already exists" in duplicate.stderr, duplicate.stderr

    check = load_json(run_cmd(["check", "demo-draft", "--root", DRAFT_ROOT_REL, "--json"]).stdout)
    assert check["schema"] == "draft_code_check.v1" and check["status"] == "ok", check
    assert check["execution_allowed"] is False, check
    assert check["manifest"]["data"]["execution"] == "forbidden-until-accepted-run-plan", check

    marker = os.path.join(DRAFT_ROOT, "EXECUTED_MARKER.txt")
    with open(os.path.join(draft_path, "src", "would_execute.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write("open(%r, 'w').write('bad')\n" % marker)
    review = load_json(run_cmd(["review", "demo-draft", "--root", DRAFT_ROOT_REL, "--json"]).stdout)
    assert review["schema"] == "draft_code_review.v1", review
    assert review["source"]["kind"] == "agent-draft", review
    assert review["source"]["execute_allowed"] is False, review
    assert review["draft_policy"]["execution_allowed"] is False, review
    assert not os.path.exists(marker), "review executed draft code"

    list_payload = load_json(run_cmd(["list", "--root", DRAFT_ROOT_REL, "--json"]).stdout)
    assert list_payload["schema"] == "draft_code_list.v1", list_payload
    assert [d["id"] for d in list_payload["drafts"]] == ["demo-draft"], list_payload

    manifest_path = os.path.join(draft_path, "manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["execution"] = "allowed"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    bad = subprocess.run(
        [sys.executable, TOOL, "check", "demo-draft", "--root", DRAFT_ROOT_REL, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert bad.returncode == 1, (bad.stdout, bad.stderr)
    bad_payload = load_json(bad.stdout)
    assert bad_payload["status"] == "error", bad_payload

    outside = subprocess.run(
        [sys.executable, TOOL, "list", "--root", ".."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert outside.returncode == 2 and "outside repo" in outside.stderr, outside.stderr

    shutil.rmtree(DRAFT_ROOT, ignore_errors=True)
    print("TESTS OK draft_code: create/check/review/list/no-execute/path-safety")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)