#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_l2_inventory
# TYPE: active-script
# DOMAIN: core.testing
# DEPTH_LEVEL: 2
# SUMMARY: Тест l2_inventory.py — build → stats → query на fixture-папке (пилот T-273).
# ==========================================
"""
"""Тест l2_inventory.py — read-only L2-inventory → SQLite/FTS5 (build/stats/query).

Двухступенчатый (конвенция conftest.py):
  - pytest-collectable: module-level test_* функции;
  - standalone __main__: run() с ненулевым exit при провале.
Прогон:
  py -3 tools/tests/test_l2_inventory.py
  py -3 -m pytest tools/tests/test_l2_inventory.py -q
"""
# --- бутстрап путей (C14): тест живёт в tools/tests/, инструменты — в tools/. ---
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import shutil
import sys
import uuid

os.environ.setdefault("PYTHONUTF8", "1")
sys.path.insert(0, _TOOLS_DIR)
import l2_inventory as li

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(base, rel, data, binary=False):
    """Записать фикстуру внутри base (это НЕ источник read-only — это временный корень теста)."""
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if binary else "w"
    if binary:
        open(path, mode).write(data)
    else:
        open(path, mode, encoding="utf-8", newline="\n").write(data)


def _make_fixture(src):
    """Создать разнородный источник: .md/.py/.txt (текст) + .png (бинарь) + вложенность."""
    _w(src, "docs/readme.md", "# Заголовок\nкворум независимых судей против захвата оракула\n")
    _w(src, "docs/notes.txt", "простые заметки: крдт мёрж канона field-level\n")
    _w(src, "code/app.py", "def butterfly():\n    return 'прогрессивное раскрытие меню'\n")
    _w(src, "secrets.md", "api_key=SUPERSECRETXYZ должно быть замаскировано\n")
    # бинарный файл — только метаданные, содержимое НЕ индексируется
    _w(src, "img/pixel.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00binary-not-indexed", binary=True)


def _make_project_tmp(prefix):
    """Создать temp-каталог в repo/tmp-work без stdlib TemporaryDirectory.

    На текущем Windows runtime stdlib tempfile может создать каталог, но затем
    запретить запись внутрь него. Прямой os.makedirs в tmp-work проверенно работает.
    """
    root = os.path.dirname(_TOOLS_DIR)
    base = os.path.join(root, "tmp-work")
    os.makedirs(base, exist_ok=True)
    for _ in range(100):
        path = os.path.join(base, prefix + uuid.uuid4().hex[:12])
        try:
            os.makedirs(path, exist_ok=False)
            return path
        except FileExistsError:
            pass
    raise RuntimeError("cannot create project temp dir")


def _run_cycle():
    """Полный цикл build → stats → query в изолированной tmp-папке. Возвращает список провалов."""
    fails = []
    base = _make_project_tmp("l2inv_src_")
    try:
        src = os.path.join(base, "source")
        os.makedirs(src, exist_ok=True)
        _make_fixture(src)
        db = os.path.join(base, "out", "l2_inventory.db")

        # --- build ---
        rep = li.build(src, db_path=db, max_text_bytes=200 * 1024)
        if not os.path.exists(db):
            fails.append("build: файл БД не создан")
        # 5 файлов: readme.md, notes.txt, app.py, secrets.md, pixel.png
        if rep["total_files"] != 5:
            fails.append("build: ожидалось 5 файлов, получено %d" % rep["total_files"])
        # 4 текстовых проиндексированы (png — только метаданные)
        if rep["text_indexed"] != 4:
            fails.append("build: ожидалось 4 текстовых в ФТС, получено %d" % rep["text_indexed"])
        if rep["by_extension"].get(".md") != 2:
            fails.append("build: ожидалось 2 файла .md, получено %s" % rep["by_extension"].get(".md"))
        if rep["by_extension"].get(".png") != 1:
            fails.append("build: ожидался 1 файл .png, получено %s" % rep["by_extension"].get(".png"))
        # источник в отчёте замаскирован (личный путь не утёк) — redact заменил $HOME/$WORKSPACE
        # (проверяем косвенно: отчёт содержит строку, а не падает)
        if not rep["source"]:
            fails.append("build: пустой source в отчёте")

        # --- stats ---
        st = li.stats(db)
        if st is None:
            fails.append("stats: вернул None при существующей БД")
        else:
            if st["total_files"] != 5:
                fails.append("stats: total_files=%d, ожидалось 5" % st["total_files"])
            if st["total_size_bytes"] <= 0:
                fails.append("stats: total_size_bytes должен быть > 0")
            if st["text_indexed"] != 4:
                fails.append("stats: text_indexed=%d, ожидалось 4" % st["text_indexed"])
            if st["by_extension"].get(".py") != 1:
                fails.append("stats: .py=%s, ожидалось 1" % st["by_extension"].get(".py"))

        # --- query: попадание по уникальному термину из содержимого ---
        r1 = li.query(db, "оракула", limit=10)
        if r1 is None:
            fails.append("query 'оракула': вернул None")
        elif not any(x["rel"] == "docs/readme.md" for x in r1):
            fails.append("query 'оракула' → docs/readme.md: %s" % r1)

        r2 = li.query(db, "butterfly", limit=10)
        if not r2 or not any(x["rel"] == "code/app.py" for x in r2):
            fails.append("query 'butterfly' → code/app.py: %s" % r2)

        # секрет замаскирован: SUPERSECRETXYZ не должен всплыть в сниппете
        r3 = li.query(db, "замаскировано", limit=10)
        if not r3 or not any(x["rel"] == "secrets.md" for x in r3):
            fails.append("query 'замаскировано' → secrets.md: %s" % r3)
        if any("SUPERSECRETXYZ" in (x.get("snippet") or "") for x in (r3 or [])):
            fails.append("query: секрет SUPERSECRETXYZ НЕ замаскирован в сниппете: %s" % r3)

        # бинарь не индексируется по содержимому: поиск по «binary-not-indexed» не даёт png-контент
        r4 = li.query(db, "notindexedbinary", limit=10)
        # (термин не встречается — ожидаем пусто, но точно не падение)
        if r4 is None:
            fails.append("query бинарного термина вернул None вместо []")

        # несуществующий термин → пусто, без краха
        r5 = li.query(db, "zzzнетничеготакого", limit=10)
        if r5 is None or r5 != []:
            fails.append("query несуществующего → []: %s" % r5)

        # --- негатив: отсутствующая БД → None (а не краш) ---
        if li.stats(os.path.join(base, "missing.db")) is not None:
            fails.append("stats(missing) → None")
        if li.query(os.path.join(base, "missing.db"), "x") is not None:
            fails.append("query(missing) → None")
    finally:
        shutil.rmtree(base, ignore_errors=True)

    return fails


# --- pytest-collectable точки ---

def test_build_stats_query_cycle():
    fails = _run_cycle()
    assert not fails, "l2_inventory провалы:\n  - " + "\n  - ".join(fails)


def test_missing_source_raises():
    d = _make_project_tmp("l2inv_missing_")
    try:
        missing = os.path.join(d, "no-such-source")
        db = os.path.join(d, "x.db")
        raised = False
        try:
            li.build(missing, db_path=db)
        except FileNotFoundError:
            raised = True
        assert raised, "build по несуществующему источнику должен бросать FileNotFoundError"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_db_inside_source_rejected():
    d = _make_project_tmp("l2inv_db_guard_")
    try:
        src = os.path.join(d, "source")
        os.makedirs(src, exist_ok=True)
        _make_fixture(src)
        raised = False
        try:
            li.build(src, db_path=os.path.join(src, "inside-source.db"))
        except li.PathAccessError:
            raised = True
        assert raised, "build должен запрещать --db внутри --source"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_max_files_bounds_scan():
    d = _make_project_tmp("l2inv_max_files_")
    try:
        src = os.path.join(d, "source")
        os.makedirs(src, exist_ok=True)
        _make_fixture(src)
        db = os.path.join(d, "out", "bounded.db")
        rep = li.build(src, db_path=db, max_files=2)
        assert rep["total_files"] == 2, "max_files=2 должен ограничить scan двумя файлами"
        assert rep["max_files"] == 2
        assert rep["truncated_by_max_files"] is True
        st = li.stats(db)
        assert st is not None
        assert st["total_files"] == 2
        assert st["max_files"] == 2
        assert st["truncated_by_max_files"] is True
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- standalone __main__ ---

def run():
    fails = _run_cycle()
    # добавим негатив по источнику
    d = _make_project_tmp("l2inv_missing_")
    try:
        missing = os.path.join(d, "no-such-source")
        try:
            li.build(missing, db_path=os.path.join(d, "x.db"))
            fails.append("build(missing source): ожидался FileNotFoundError")
        except FileNotFoundError:
            pass
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # негатив по safety-contract: БД нельзя создавать внутри read-only source
    d = _make_project_tmp("l2inv_db_guard_")
    try:
        src = os.path.join(d, "source")
        os.makedirs(src, exist_ok=True)
        _make_fixture(src)
        try:
            li.build(src, db_path=os.path.join(src, "inside-source.db"))
            fails.append("build(db inside source): ожидался PathAccessError")
        except li.PathAccessError:
            pass
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # bounded scan: реальный W_run должен иметь верхнюю границу по числу файлов
    d = _make_project_tmp("l2inv_max_files_")
    try:
        src = os.path.join(d, "source")
        os.makedirs(src, exist_ok=True)
        _make_fixture(src)
        db = os.path.join(d, "out", "bounded.db")
        rep = li.build(src, db_path=db, max_files=2)
        st = li.stats(db)
        if rep.get("total_files") != 2:
            fails.append("build(max_files=2): total_files=%s" % rep.get("total_files"))
        if rep.get("max_files") != 2 or not rep.get("truncated_by_max_files"):
            fails.append("build(max_files=2): нет признака bounded/truncated")
        if not st or st.get("total_files") != 2 or st.get("max_files") != 2 or not st.get("truncated_by_max_files"):
            fails.append("stats(max_files=2): неверная meta %s" % st)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if fails:
        print("FAIL test_l2_inventory:")
        for f in fails:
            print("  -", f)
        return 1
    print("OK test_l2_inventory: build(5 файлов, 4 текст в ФТС) · stats · query(термины/redact/бинарь) · missing→None")
    return 0


if __name__ == "__main__":
    sys.exit(run())

