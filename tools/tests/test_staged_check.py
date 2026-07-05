#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_staged_check
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: Тест staged_check.py — гейт частичного стейджинга навигации (C1-b): verdict-логика без git.
# ==========================================
"""Тест staged_check.py (C1-b, волна 2) — «самопроверено».

Чистая логика verdict(staged, unstaged) тестируется БЕЗ git (герметично, детерминированно):
классификация источник/генерат, все 5 сценариев блокировки. Реальный git-путь покрыт
smoke-прогоном check() на живом репо (структура ответа, без утверждений о содержимом —
рабочее дерево у агентов легитимно грязное).
"""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import staged_check as sc


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    try:
        # классификация путей
        assert sc._is_source("topics/x.md") and sc._is_source("tasks/T-001.md"), "source-префиксы"
        assert not sc._is_source("tools/x.py") and not sc._is_source("topics/x.txt"), "не-source"
        assert sc._is_generated("STATUS.md") and sc._is_generated("indexes/topics.md"), "генераты"
        assert not sc._is_generated("docs/x.md"), "docs — не генерат"
        # windows-слэши нормализуются
        assert sc._is_generated("indexes\\topics.md"), "обратный слэш должен нормализоваться"

        # (a) класс C1: источники staged, регенераты НЕ staged → блок
        v = sc.verdict(staged=["topics/new-topic.md"], unstaged=["STATUS.md", "index.json"])
        assert v["blocked"], v
        assert v["staged_sources"] == ["topics/new-topic.md"], v
        assert v["unstaged_generated"] == ["STATUS.md", "index.json"] or \
            set(v["unstaged_generated"]) == {"STATUS.md", "index.json"}, v

        # (b) источники И регенераты staged, незастейдженных генератов нет → ок
        v = sc.verdict(staged=["topics/new-topic.md", "STATUS.md", "index.json"], unstaged=[])
        assert not v["blocked"], v

        # (c) источник staged, генераты вообще не менялись (правка тела без front-matter) → ок
        v = sc.verdict(staged=["tasks/T-100.md"], unstaged=["tools/foo.py"])
        assert not v["blocked"], v

        # (d) ничего не staged → ок
        v = sc.verdict(staged=[], unstaged=["STATUS.md"])
        assert not v["blocked"], v

        # (e) генерат dirty, но staged нет источников → не наш класс, ок
        v = sc.verdict(staged=["tools/foo.py"], unstaged=["board.md"])
        assert not v["blocked"], v

        # (f) частично staged генераты + незастейдженный хвост генератов при staged-источнике → блок
        v = sc.verdict(staged=["decisions/D-050.md", "STATUS.md"], unstaged=["indexes/topics.md"])
        assert v["blocked"], v

        # smoke: реальный git-путь (структура; None допустим только при недоступном git)
        res = sc.check()
        assert res is None or set(res) >= {"blocked", "staged_sources", "unstaged_generated"}, res

        print("TESTS OK staged_check: классификация source/generated + verdict 6 сценариев "
              "(C1-класс блокируется, остальное нет) + smoke check()")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
