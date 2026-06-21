#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты variants.py — READ-ONLY дискавери форк-вариантов по реальному репо.

Все проверки read-only против известных файлов репо; временные каталоги не нужны
(инструмент ничего не пишет). Subprocess-проверка CLI — по конвенции drift_check/onboard.
"""
import os
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import variants  # noqa: E402


def test_discover_finds_known_sources():
    index = variants.build_index()
    files = [v["file"] for vs in index.values() for v in vs]

    # >=1 stream-пакет
    streams = [f for f in files if f.startswith("streams/") and f.endswith("STREAM.md")]
    assert streams, "ожидался хотя бы один stream-пакет, нашли: %r" % files

    # пара онбординг ↔ operating-manual (форк-варианты Claude/Codex одной темы)
    assert "docs/agent-onboarding.md" in files, "нет docs/agent-onboarding.md"
    assert "docs/top-agent-operating-manual.md" in files, "нет operating-manual"
    onboard_key = [k for k, vs in index.items()
                   if any(v["file"] == "docs/agent-onboarding.md" for v in vs)][0]
    pair_agents = {v["agent"] for v in index[onboard_key]
                   if v["file"].startswith("docs/")}
    assert {"claude", "codex"} <= pair_agents, \
        "пара должна различать claude/codex, agents=%r" % pair_agents

    # хотя бы один форк из темы/
    topic_notes = [f for f in files if f.startswith("темы/")]
    assert topic_notes, "ожидался хотя бы один форк из темы/, нашли: %r" % files


def test_status_and_agent_inference():
    index = variants.build_index()
    # commit-policy stream имеет status: adopted, author: codex во front-matter
    found = None
    for vs in index.values():
        for v in vs:
            if v["file"].endswith("2026-06-21-codex-streams-policy/STREAM.md"):
                found = v
    assert found is not None, "не найден codex-streams-policy STREAM.md"
    assert found["status"] == "adopted", "status из front-matter: %r" % found["status"]
    assert found["agent"] == "codex", "agent из front-matter: %r" % found["agent"]


def test_index_emits_valid_json():
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, "variants.py"), "index"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL,
    )
    assert p.returncode == 0, "index rc=%s err=%s" % (p.returncode, p.stderr)
    data = json.loads(p.stdout)
    assert isinstance(data, dict) and data, "JSON должен быть непустым объектом"
    for variants_list in data.values():
        assert isinstance(variants_list, list)
        for v in variants_list:
            assert set(v) == {"agent", "file", "status", "kind"}, "форма записи: %r" % v


def test_topic_filter_narrows():
    full = variants.build_index()
    narrowed = variants._filter_topic(full, "commit-policy")
    assert narrowed, "фильтр commit-policy не должен быть пустым"
    assert len(narrowed) < len(full), "--topic должен сужать набор"
    for key in narrowed:
        assert "commit-policy" in key

    # тот же фильтр через CLI list --topic
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, "variants.py"),
         "list", "--topic", "commit-policy", "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL,
    )
    assert p.returncode == 0, "list rc=%s err=%s" % (p.returncode, p.stderr)
    data = json.loads(p.stdout)
    assert data and all("commit-policy" in k for k in data)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print("PASS %s" % fn.__name__)
        except AssertionError as exc:
            failed += 1
            print("FAIL %s: %s" % (fn.__name__, exc))
    print("\n%d/%d passed" % (len(fns) - failed, len(fns)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run_all())
