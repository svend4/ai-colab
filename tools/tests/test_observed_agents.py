#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_observed_agents
# TYPE: active-script
# DOMAIN: core.parsing
# DEPTH_LEVEL: 2
# SUMMARY: Тест observed_agents (Q-W2-9b): наблюдение агентов в claim/heartbeat/streams + advisory-WARN validate.
# ==========================================
"""Тест динамической сверки ростера агентов (Q-W2-9b, C36-a) — «самопроверено».

Контракты:
  1. `_canon.observed_agents(root)` собирает имена агентов из рабочих артефактов:
     queues/claimed/*.md (front-matter agent/claimed_by), logs/heartbeat/*.json
     (имя файла), streams/<topic>/<id>/STREAM.md и streams/<topic>/*-divergence.md
     (front-matter agent). README.md пропускаются, имена нормализуются к lower-case,
     пустой/чужой корень → {} (без исключений).
  2. `validate.check_agents_roster` — advisory: агент вне AGENTS_ROSTER даёт WARN
     (НЕ ERROR: состав ростера ратифицируется человеком, C32/Q-W2-9); агенты из
     ростера не флажатся.
  3. Градация вне ростера (решение Stefan 2026-07-06, A4-1): SERVICE_AGENTS
     (служебные исполнители роёв) — тихо, без WARN; EXCLUDED_AGENTS — WARN
     с текстом причины из словаря (провенанс решения).

Пишется pytest-collectable (конвенция tools/tests/ по Q-W2-3/C13-c).
"""
# --- бутстрап путей (C14): тест живёт в tools/tests/, инструменты — в tools/.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys

from _canon import AGENTS_ROSTER, SERVICE_AGENTS, EXCLUDED_AGENTS, observed_agents
import validate


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path) or root, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _build(root):
    """Рабочие артефакты фикстуры: 2 агента вне ростера (ghost, phantom) + 3 из ростера."""
    # claim в формате pipeline.py (agent:) + legacy-формат (claimed_by:, регистр смешан)
    _write(root, "queues/claimed/T-100.claim.md",
           "---\ntask: T-100\nagent: ghost\nclaim_id: abc123\nlease_epoch: 99\n---\n")
    _write(root, "queues/claimed/legacy.md", "---\nclaimed_by: Mavis\n---\n# старый claim\n")
    _write(root, "queues/claimed/README.md", "# Claimed\n\n- Агент: agent-id (пример)\n")
    # heartbeat: имя файла = имя агента
    _write(root, "logs/heartbeat/claude.json", "{}\n")
    # streams: манифест варианта + divergence-файл; README пропускается
    _write(root, "streams/topic-a/20260101-0000-codex/STREAM.md",
           "---\nid: 20260101-0000-codex\ntopic: topic-a\nagent: codex\nstatus: proposed\n---\n")
    _write(root, "streams/topic-a/phantom-divergence.md",
           "---\ntopic: topic-a\nagent: phantom\ntype: divergence-stream\n---\n")
    _write(root, "streams/topic-a/README.md", "# topic-a\n")
    _write(root, "streams/README.md", "# streams\n")


def test_observed_agents_sources(tmp_path):
    root = str(tmp_path)
    _build(root)
    found = observed_agents(root)
    assert set(found) == {"ghost", "mavis", "claude", "codex", "phantom"}, found
    # каждое имя привязано к месту-свидетельству (для текста WARN валидатора)
    assert found["ghost"] == ["queues/claimed/T-100.claim.md"], found["ghost"]
    assert found["mavis"] == ["queues/claimed/legacy.md"], found["mavis"]  # claimed_by + lower-case
    assert found["claude"] == ["logs/heartbeat/claude.json"], found["claude"]
    assert found["codex"] == ["streams/topic-a/20260101-0000-codex/STREAM.md"], found["codex"]
    assert found["phantom"] == ["streams/topic-a/phantom-divergence.md"], found["phantom"]


def test_observed_agents_empty_root(tmp_path):
    # корень без рабочих слоёв — пустой словарь, не исключение
    assert observed_agents(str(tmp_path)) == {}


def _reset_validate():
    del validate.ERRORS[:]
    del validate.WARNS[:]
    del validate.OKS[:]


def test_validate_warns_unknown_agent(tmp_path):
    root = str(tmp_path)
    _build(root)
    old_root = validate.ROOT
    try:
        validate.ROOT = root
        _reset_validate()
        validate.check_agents_roster()
        joined = "\n".join(validate.WARNS)
        # неизвестные ростеру — WARN с местом и отсылкой к ратификации человеком
        assert "«ghost»" in joined and "queues/claimed/T-100.claim.md" in joined, joined
        assert "«phantom»" in joined and "streams/topic-a/phantom-divergence.md" in joined, joined
        assert "AGENTS_ROSTER" in joined and "C32/Q-W2-9" in joined, joined
        # агенты из ростера не флажатся; advisory — ни одного ERROR
        for known in AGENTS_ROSTER:
            assert ("«%s»" % known) not in joined, joined
        assert validate.ERRORS == [], "advisory-проверка не должна давать ERROR: %r" % validate.ERRORS
    finally:
        validate.ROOT = old_root
        _reset_validate()


def test_validate_ok_when_all_known(tmp_path):
    root = str(tmp_path)
    _write(root, "logs/heartbeat/claude.json", "{}\n")
    _write(root, "queues/claimed/T-1.claim.md",
           "---\ntask: T-1\nagent: codex\nclaim_id: x\nlease_epoch: 1\n---\n")
    old_root = validate.ROOT
    try:
        validate.ROOT = root
        _reset_validate()
        validate.check_agents_roster()
        assert validate.WARNS == [], validate.WARNS
        assert any("AGENTS_ROSTER" in m for m in validate.OKS), validate.OKS
    finally:
        validate.ROOT = old_root
        _reset_validate()


def test_validate_service_agent_silent(tmp_path):
    # SERVICE_AGENTS: служебные исполнители роёв — это норма, тихо (решение Stefan 2026-07-06)
    root = str(tmp_path)
    assert "subagent-worker" in SERVICE_AGENTS  # состав по решению A4-1
    _write(root, "logs/heartbeat/subagent-worker.json", "{}\n")
    _write(root, "queues/claimed/T-200.claim.md",
           "---\ntask: T-200\nagent: subagent-worker\nclaim_id: s1\nlease_epoch: 7\n---\n")
    old_root = validate.ROOT
    try:
        validate.ROOT = root
        _reset_validate()
        validate.check_agents_roster()
        assert validate.WARNS == [], "service-агент не должен давать WARN: %r" % validate.WARNS
        assert validate.ERRORS == [], validate.ERRORS
        assert any("AGENTS_ROSTER" in m for m in validate.OKS), validate.OKS
    finally:
        validate.ROOT = old_root
        _reset_validate()


def test_validate_excluded_agent_warn_reason(tmp_path):
    # EXCLUDED_AGENTS: WARN с текстом причины из словаря (провенанс решения Stefan 2026-07-06)
    root = str(tmp_path)
    assert "antigravity" in EXCLUDED_AGENTS  # состав по решению A4-1
    _write(root, "logs/heartbeat/antigravity.json", "{}\n")
    old_root = validate.ROOT
    try:
        validate.ROOT = root
        _reset_validate()
        validate.check_agents_roster()
        joined = "\n".join(validate.WARNS)
        assert "«antigravity»" in joined, joined
        assert "logs/heartbeat/antigravity.json" in joined, joined
        # причина берётся ИЗ словаря EXCLUDED_AGENTS, а не хардкодится в validate
        assert EXCLUDED_AGENTS["antigravity"] in joined, joined
        assert "outbox-mass-strip" in joined, joined
        assert validate.ERRORS == [], "advisory-проверка не должна давать ERROR: %r" % validate.ERRORS
    finally:
        validate.ROOT = old_root
        _reset_validate()


if __name__ == "__main__":
    # standalone-запуск (двухступенчатый канон: файл гоняет и test_all.py)
    import tempfile
    import shutil
    failed = 0
    for fn in (test_observed_agents_sources, test_observed_agents_empty_root,
               test_validate_warns_unknown_agent, test_validate_ok_when_all_known,
               test_validate_service_agent_silent, test_validate_excluded_agent_warn_reason):
        tmp = tempfile.mkdtemp(prefix="observed_agents_")
        try:
            fn(tmp)
        except AssertionError as e:
            failed += 1
            print("TEST FAIL (%s): %s" % (fn.__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if failed:
        sys.exit(1)
    print("TESTS OK observed_agents: claim(agent/claimed_by)+heartbeat+streams источники, "
          "lower-case нормализация, пустой корень → {}, validate WARN для чужих / OK для ростера "
          "(advisory, без ERROR) + service тихо / excluded WARN с причиной (A4-1)")
    sys.exit(0)
