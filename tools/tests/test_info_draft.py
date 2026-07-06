# ast: allow-subprocess
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_info_draft
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: Tests for the no-canon info/document draft packet manager.
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
import tempfile

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
TMP_BASE = os.path.join(ROOT, "tmp-work")
TOOL = os.path.join(HERE, "info_draft.py")


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
    # Изоляция от параллельных прогонов: уникальный каталог через tempfile.mkdtemp,
    # уборка в finally. База обязана лежать внутри репо — info_draft.py отклоняет
    # --root вне репо ("refusing path outside repo").
    os.makedirs(TMP_BASE, exist_ok=True)
    draft_root = tempfile.mkdtemp(prefix="info-draft-test-", dir=TMP_BASE)
    draft_root_rel = os.path.relpath(draft_root, ROOT)
    try:
        return _run_checks(draft_root_rel)
    finally:
        shutil.rmtree(draft_root, ignore_errors=True)


def _run_checks(draft_root_rel):
    p = run_cmd([
        "create",
        "Doc Draft",
        "--owner",
        "codex",
        "--title",
        "Doc Draft",
        "--purpose",
        "exercise no-canon information draft manager",
        "--kind",
        "doc",
        "--task",
        "T-261",
        "--stream",
        "20260625-2013-codex",
        "--topic",
        "info-draft-manager",
        "--target",
        "docs/example.md",
        "--root",
        draft_root_rel,
        "--json",
    ])
    created = load_json(p.stdout)
    assert created["schema"] == "info_draft_create.v1", created
    assert created["mutates"] is True, created
    assert created["canon_status"] == "not-canonical-until-synthesized-and-promoted", created
    assert created["draft"]["id"] == "doc-draft", created
    draft_path = os.path.join(ROOT, created["draft"]["relpath"].replace("/", os.sep))
    for name in ["manifest.json", "README.md", "brief.md", "outline.md", "claims.md", "sources.md", "open_questions.md", "divergence.md", "notes.md"]:
        assert os.path.isfile(os.path.join(draft_path, name)), name

    duplicate = subprocess.run(
        [sys.executable, TOOL, "create", "doc-draft", "--owner", "codex", "--purpose", "duplicate", "--root", draft_root_rel],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    assert duplicate.returncode != 0 and "already exists" in duplicate.stderr, duplicate.stderr

    check = load_json(run_cmd(["check", "doc-draft", "--root", draft_root_rel, "--json"]).stdout)
    assert check["schema"] == "info_draft_check.v1" and check["status"] == "ok", check

    review = load_json(run_cmd(["review", "doc-draft", "--root", draft_root_rel, "--json"]).stdout)
    assert review["schema"] == "info_draft_review.v1", review
    assert review["source"]["canon_status"] == "not-canonical-until-synthesized-and-promoted", review
    assert review["recommendation"]["route"] in {"keep-quarantine", "ready-for-synthesis"}, review
    assert "synthesize-docs" in review["recommendation"]["synthesis_command"], review

    # Fill enough bullets to move from keep-quarantine to ready-for-synthesis.
    with open(os.path.join(draft_path, "claims.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write("- claim: first\n- claim: second\n")
    with open(os.path.join(draft_path, "sources.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write("- source: docs/example.md\n- source: streams/example/STREAM.md\n")
    with open(os.path.join(draft_path, "open_questions.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write("- question: one\n- question: two\n")
    ready = load_json(run_cmd(["review", "doc-draft", "--root", draft_root_rel, "--json"]).stdout)
    assert ready["recommendation"]["route"] == "ready-for-synthesis", ready

    list_payload = load_json(run_cmd(["list", "--root", draft_root_rel, "--json"]).stdout)
    assert list_payload["schema"] == "info_draft_list.v1", list_payload
    assert [d["id"] for d in list_payload["drafts"]] == ["doc-draft"], list_payload

    manifest_path = os.path.join(draft_path, "manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["canon_status"] = "accepted"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    bad = subprocess.run(
        [sys.executable, TOOL, "check", "doc-draft", "--root", draft_root_rel, "--json"],
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

    print("TESTS OK info_draft: create/check/review/list/no-canon/path-safety")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)