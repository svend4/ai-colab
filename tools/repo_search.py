#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.repo_search
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт repo_search.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
repo_search (продукт) — ранжированный полнотекстовый поиск по ДОКУМЕНТАЦИИ репозитория.

Репо вырос (десятки docs/decisions/questions/topics/tasks). Этот инструмент индексирует их содержимое
в FTS5-память (поверх L6-движка `tools/knowledge.py`: files-драйвер + workbench + bm25) и даёт
ранжированный поиск — чтобы агент или человек находил нужное (решение, политику, тему) одной командой,
а не grep'ом вслепую. READ-ONLY; БД в gitignored `logs/`.

CLI:
    python tools/repo_search.py index                      # (пере)собрать индекс по docs/decisions/...
    python tools/repo_search.py search "<запрос>" [--limit N] [--json]
    python tools/repo_search.py report                     # размер/состав индекса
"""
import os
import re
import sys
from _ioutil import configure_output
from _cli import help_guard
import json
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
import knowledge as kn  # переиспользуем L6-движок (build/_build_fts/fts_search/workbench)

# Зоны документации (содержательная проза/канон); код/драйверы намеренно не индексируем.
DOC_DIRS = ["docs", "decisions", "questions", "topics", "tasks"]
DEFAULT_DB = "logs/repo-knowledge.db"

configure_output()

def build_index(db=DEFAULT_DB, dirs=None):
    """Собрать свежий индекс по зонам документации. Возвращает число документов."""
    full = os.path.join(ROOT, db)
    if os.path.exists(full):
        os.remove(full)  # свежий индекс без дублей при пересборке
    os.makedirs(os.path.dirname(full), exist_ok=True)
    total = 0
    for d in (dirs or DOC_DIRS):
        if os.path.isdir(os.path.join(ROOT, d)):
            total += kn.build(db, d, agent="repo_search")
    return total

def _present(row):
    """Привести строку результата к продукт-виду: реальный кликабельный путь + компактный сниппет."""
    d = dict(row)
    p = d.get("path") or ""
    # id движка знаний `knowledge:<dir>:<file>` -> реальный путь `<dir>/<file>` (кликабельно)
    if ":" in p:
        parts = p.split(":")
        if parts[0] in ("knowledge", "repo_search"):
            parts = parts[1:]
        p = "/".join(parts)
    d["path"] = p
    s = re.sub(r"\s+", " ", (d.get("summary") or "")).strip()
    d["summary"] = s[:200]  # сниппет, а не всё тело дока (JSON не раздувается)
    return d

def search(query, db=DEFAULT_DB, limit=10):
    """Ранжированный FTS5+bm25 поиск (термы через OR — для recall); собирает индекс, если его нет."""
    full = os.path.join(ROOT, db)
    if not os.path.exists(full):
        build_index(db)
    conn = kn.wb.init(db, base_dir=ROOT)
    try:
        kn._build_fts(conn)
        terms = [t for t in re.split(r"[^0-9A-Za-zА-Яа-яЁё_]+", query) if len(t) > 1]
        expr = " OR ".join('"%s"' % t for t in terms) if terms else '"%s"' % query.replace('"', "")
        try:
            rows = conn.execute(
                "SELECT d.path AS path, d.type AS type, d.summary AS summary, bm25(kn_fts) AS rank "
                "FROM kn_fts f JOIN documents d ON d.id = f.doc_id "
                "WHERE kn_fts MATCH ? ORDER BY rank LIMIT ?", (expr, int(limit))).fetchall()
            return [_present(r) for r in rows]
        except sqlite3.OperationalError:
            return [_present(r) for r in kn.fts_search(conn, query, limit=limit)]  # fallback
    finally:
        conn.close()

def main():
    help_guard(__doc__)
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    as_json = "--json" in a
    limit = int(a[a.index("--limit") + 1]) if "--limit" in a and a.index("--limit") + 1 < len(a) else 10
    try:
        if cmd == "index":
            n = build_index()
            print("Индекс собран: %d документов (%s) -> %s" % (n, "/".join(DOC_DIRS), DEFAULT_DB))
            return 0
        if cmd == "search":
            words, i = [], 1
            while i < len(a):
                if a[i] == "--limit":
                    i += 2
                    continue
                if a[i].startswith("--"):
                    i += 1
                    continue
                words.append(a[i])
                i += 1
            if not words:
                print("Укажи запрос: repo_search.py search \"<текст>\"")
                return 2
            hits = search(" ".join(words), limit=limit)
            if as_json:
                print(json.dumps(hits, ensure_ascii=False, indent=2))
                return 0
            print("Поиск «%s» — %d совпадений (ранжировано, FTS5/bm25):" % (" ".join(words), len(hits)))
            for h in hits:
                print("  %-44s %s" % (h.get("path", ""), (h.get("summary") or "")[:70]))
            return 0
        if cmd == "report":
            n = build_index()
            conn = kn.wb.init(DEFAULT_DB, base_dir=ROOT)
            try:
                docs = kn.wb.query_documents(conn, limit=2000)
            finally:
                conn.close()
            by = {}
            for d in docs:
                by[d.get("type") or "?"] = by.get(d.get("type") or "?", 0) + 1
            print("Индекс репо: %d документов по зонам %s" % (n, "/".join(DOC_DIRS)))
            for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
                print("  %-8s %d" % (k, v))
            return 0
    except Exception as exc:  # noqa: BLE001
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main())
