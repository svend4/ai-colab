#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG-поиск v1 над workbench.db — ранжирование документов по релевантности запросу.

TF-IDF на чистой stdlib (без зависимостей): ранжирует `documents` по совпадению
терминов запроса с `path`+`summary`. Это **keyword-rank**, не семантический вектор —
настоящие embeddings/векторный поиск добавляются отдельным слоем (нужна модель).

ВНИМАНИЕ: написано без прогона. Прогнать `python drivers/workbench/test_search.py`.

CLI:
    python search.py <db.db> "<query>" [--limit N]
"""
import os
import re
import sys
import math
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import workbench as wb


def _tokens(s):
    return re.findall(r"\w+", (s or "").lower())


def rank(db, query, limit=10, base_dir=None, pool=1000):
    conn = wb.init(db, base_dir=base_dir)
    try:
        docs = wb.query_documents(conn, limit=pool)
    finally:
        conn.close()

    doctoks = [_tokens(d.get("path", "") + " " + (d.get("summary") or "")) for d in docs]
    df = collections.Counter()
    for toks in doctoks:
        for t in set(toks):
            df[t] += 1
    n = max(1, len(docs))
    qt = set(_tokens(query))

    scored = []
    for d, toks in zip(docs, doctoks):
        tf = collections.Counter(toks)
        score = sum(tf[t] * math.log(1 + n / (1 + df[t])) for t in qt if t in tf)
        if score > 0:
            scored.append((score, d))
    scored.sort(key=lambda x: -x[0])
    return [dict(d, score=round(s, 3)) for s, d in scored[:limit]]


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    db, query = a[0], a[1]
    limit = int(a[a.index("--limit") + 1]) if "--limit" in a else 10
    try:
        print(json.dumps(rank(db, query, limit=limit), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
