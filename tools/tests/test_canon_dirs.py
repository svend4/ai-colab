#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_canon_dirs
# TYPE: active-script
# DOMAIN: core.parsing
# DEPTH_LEVEL: 1
# SUMMARY: Тест единого реестра CANON_DIRS в _canon (P9-a): единственность источника + missing-dir → ERROR.
# ==========================================
"""Тест консолидации CANON_DIRS (P9-a, волна 2) — «самопроверено».

Три контракта:
  1. ЕДИНСТВЕННОСТЬ ИСТОЧНИКА: в потребителях (view.py, canon_index.py, info_verify.py,
     gap_scan.py) нет СОБСТВЕННОГО присваивания CANON_DIRS = (...) — только импорт из _canon.
  2. Значения: ядро 5 каталогов; расширенный = ядро + drivers/streams/portals/core
     (фактическое поведение потребителей сохранено; канонический состав — эскалирован человеку).
  3. Контракт «несуществующий канон-путь → ERROR, не тихий 0»: require_canon_dirs поднимает
     FileNotFoundError; view.load_canon и canon_index._collect падают громко на неполном root.
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
import re
import sys
import tempfile
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import _canon
import view
import canon_index


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

# Присваивание собственной константы (не импорт): `CANON_DIRS = (`/`[`.
_OWN_CONST_RE = re.compile(r"^CANON_DIRS\s*=\s*[\(\[]", re.M)


def run():
    ok = True
    try:
        # 1. Единственность источника: локальных констант в потребителях больше нет
        for fn in ("view.py", "canon_index.py", "info_verify.py", "gap_scan.py"):
            with open(os.path.join(HERE, fn), encoding="utf-8", errors="replace") as f:
                src = f.read()
            assert not _OWN_CONST_RE.search(src), \
                "%s: собственная константа CANON_DIRS — источник должен быть _canon (P9)" % fn
        # _canon — единственное место с присваиванием
        with open(os.path.join(HERE, "_canon.py"), encoding="utf-8", errors="replace") as f:
            assert _OWN_CONST_RE.search(f.read()), "_canon.py должен определять CANON_DIRS"

        # 2. Значения и связь ядро ⊂ расширенный
        assert _canon.CANON_DIRS == ("tasks", "decisions", "questions", "topics", "docs")
        assert _canon.CANON_DIRS_EXTENDED[:5] == _canon.CANON_DIRS
        assert set(_canon.CANON_DIRS_EXTENDED) - set(_canon.CANON_DIRS) == \
            {"drivers", "streams", "portals", "core"}
        # потребители смотрят на те же объекты
        assert view.CANON_DIRS == _canon.CANON_DIRS
        assert canon_index.CANON_DIRS == _canon.CANON_DIRS

        # 3. missing → ERROR (не тихий 0)
        root = tempfile.mkdtemp(prefix="canon_dirs_test_")
        try:
            # только 2 каталога из 5
            for d in ("tasks", "decisions"):
                os.makedirs(os.path.join(root, d))
            missing = _canon.missing_canon_dirs(root)
            assert missing == ["questions", "topics", "docs"], missing
            try:
                _canon.require_canon_dirs(root)
                assert False, "require_canon_dirs обязан поднять FileNotFoundError"
            except FileNotFoundError as e:
                assert "questions" in str(e), e
            # view.load_canon: громкий отказ вместо пустого среза
            try:
                view.load_canon(root=root)
                assert False, "load_canon на неполном root обязан упасть (P9)"
            except FileNotFoundError:
                pass
            # canon_index._collect: тоже
            try:
                canon_index._collect(root, _canon.CANON_DIRS)
                assert False, "_collect на неполном root обязан упасть (P9)"
            except FileNotFoundError:
                pass
            # полный root → работает без ошибок
            for d in ("questions", "topics", "docs"):
                os.makedirs(os.path.join(root, d))
            assert _canon.missing_canon_dirs(root) == []
            _canon.require_canon_dirs(root)  # не поднимает
            assert view.load_canon(root=root) == {}  # пустой, но ЯВНО валидный (каталоги есть)
        finally:
            shutil.rmtree(root, ignore_errors=True)

        # бонус: ростер агентов (C36-a) — единый источник и regex-группа
        assert _canon.AGENTS_ROSTER == ("claude", "codex", "mavis", "novax")
        assert _canon.agents_regex_group() == "claude|codex|mavis|novax"

        print("TESTS OK canon_dirs: единственность источника (4 файла без своей константы) + "
              "ядро/расширенный составы + missing-dir → FileNotFoundError (view/canon_index) + ростер")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
