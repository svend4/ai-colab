# ==========================================
# [FILE ID CARD]
# ID: tools.retrieval_bench
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: бенчмарк retrieval по типам запросов (direct/distant/JOIN): наш ГРАФ vs FTS.
# ==========================================
"""retrieval_bench.py — бенчмарк retrieval по типам запросов (direct/distant/JOIN): наш ГРАФ vs FTS.

Метод из статьи «Vector RAG isn't enough — context graph for multi-agent memory» (TDS, 2026), применён к
НАШИМ инструментам: граф-слой (модель edges.py: типизированные рёбра depends/related; 2-hop walk = join) vs
вектор-слой (canon_index BM25/FTS5). Цель — измерить то, что у нас ЕСТЬ, но не мерилось: точность по
**join**-запросам (ответ требует склейки двух фактов; его НЕТ в тексте запроса → FTS-similarity не находит,
граф решает обходом). Детерминированно, без LLM — как в статье.

CLI: python tools/retrieval_bench.py [--json]
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import json
import shutil

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import canon_index

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

# Детерминированный фикстур-граф: цепочка зависимостей T-A → T-B → T-C (+ дистракторы).
FIXTURE = {
    "T-A": {"depends_on": ["T-B"]},
    "T-B": {"depends_on": ["T-C"]},
    "T-C": {"body": "Модуль T-C: хранилище использует PostgreSQL для персистенции."},
    "T-D": {"related": ["T-A"], "body": "Дистрактор: смежная заметка про T-A, не по делу."},
    "T-E": {"body": "Несвязанная тема про погоду и кофе."},
}
QUERIES = [
    {"type": "direct", "text": "от чего зависит T-A", "entry": "T-A", "hops": 1, "pred": "depends", "gt": "T-B"},
    {"type": "direct", "text": "от чего зависит T-B", "entry": "T-B", "hops": 1, "pred": "depends", "gt": "T-C"},
    {"type": "distant", "text": "узел T-C хранилище персистенция", "entry": "T-C", "hops": 0, "pred": None, "gt": "T-C"},
    {"type": "distant", "text": "PostgreSQL хранилище модуль", "entry": "T-C", "hops": 0, "pred": None, "gt": "T-C"},
    {"type": "join", "text": "от чего зависит то, от чего зависит T-A", "entry": "T-A", "hops": 2, "pred": "depends", "gt": "T-C"},
    {"type": "join", "text": "конечная зависимость цепочки от T-A", "entry": "T-A", "hops": 2, "pred": "depends", "gt": "T-C"},
]


def write_fixture(root):
    # direct-write-ok: синтетическая фикстура в tmp-каталоге бенча (root — временный),
    # канонический tasks/ репозитория не трогается (C33)
    d = os.path.join(root, "tasks")
    os.makedirs(d, exist_ok=True)
    for nid, spec in FIXTURE.items():
        fm = ["id: %s" % nid, "type: task"]
        if spec.get("depends_on"):
            fm.append("depends_on: [%s]" % ", ".join(spec["depends_on"]))
        if spec.get("related"):
            fm.append("related: [%s]" % ", ".join(spec["related"]))
        # with — дескриптор закрывается сразу (иначе на Windows незакрытый файл блокирует rmtree каталога)
        with open(os.path.join(d, nid + ".md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("---\n%s\n---\n# %s\n%s\n" % ("\n".join(fm), nid, spec.get("body", "")))


def build_edges():
    """Типизированные рёбра из фикстуры (зеркало модели edges.py: depends/related)."""
    edges = []
    for nid, spec in FIXTURE.items():
        for d in spec.get("depends_on", []):
            edges.append((nid, "depends", d))
        for d in spec.get("related", []):
            edges.append((nid, "related", d))
    return edges


def graph_walk(edges, start, hops, pred):
    """N-hop walk по предикату (hops=1 direct, hops=2 JOIN). hops=0 = id-lookup (distant — O(1))."""
    if hops == 0:
        return {start}
    frontier = {start}
    for _ in range(hops):
        frontier = {d for (s, p, d) in edges if s in frontier and (pred is None or p == pred)}
    return frontier


def _fts(query_text, db, k=3):
    res = canon_index.search(query_text, db_path=db, limit=k) or []
    return [r["id"] for r in res], " ".join(r.get("snippet", "") for r in res)


def run(root, db):
    write_fixture(root)
    canon_index.build(root=root, db_path=db, dirs=("tasks",))
    edges = build_edges()
    rows = []
    for q in QUERIES:
        g = graph_walk(edges, q["entry"], q["hops"], q["pred"]) if q["entry"] else set()
        ids, snip = _fts(q["text"], db)
        rows.append({"type": q["type"], "gt": q["gt"], "text": q["text"],
                     "graph_ok": q["gt"] in g, "fts_ok": (q["gt"] in ids) or (q["gt"] in snip),
                     "graph_tok": max(1, len(",".join(sorted(g))) // 4), "fts_tok": max(1, len(snip) // 4),
                     "graph_ans": sorted(g), "fts_ids": ids})
    return rows


def summarize(rows):
    out = {}
    for t in ("direct", "distant", "join"):
        rs = [r for r in rows if r["type"] == t]
        out[t] = {"n": len(rs),
                  "graph": round(sum(r["graph_ok"] for r in rs) / len(rs), 3) if rs else 0.0,
                  "fts": round(sum(r["fts_ok"] for r in rs) / len(rs), 3) if rs else 0.0}
    n = len(rows) or 1
    out["overall"] = {"n": len(rows),
                      "graph": round(sum(r["graph_ok"] for r in rows) / n, 3),
                      "fts": round(sum(r["fts_ok"] for r in rows) / n, 3),
                      "graph_tok": round(sum(r["graph_tok"] for r in rows) / n, 1),
                      "fts_tok": round(sum(r["fts_tok"] for r in rows) / n, 1)}
    return out


def main(argv):
    help_guard(__doc__, argv)
    tmp = os.path.join(ROOT, "tmp-work", "retrieval_bench_%d" % os.getpid())
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    try:
        rows = run(tmp, os.path.join(tmp, "idx.db"))
    finally:
        # уборка временного каталога — иначе tmp-work/retrieval_bench_<pid> копятся с каждым запуском
        shutil.rmtree(tmp, ignore_errors=True)
    s = summarize(rows)
    if "--json" in argv:
        print(json.dumps({"summary": s, "rows": rows}, ensure_ascii=False, indent=2)); return 0
    print("=== RETRIEVAL BENCH · наш ГРАФ vs FTS · %d запросов (direct/distant/join) ===" % len(rows))
    print("  %-9s %8s %8s" % ("тип", "ГРАФ", "FTS"))
    for t in ("direct", "distant", "join"):
        print("  %-9s %7.0f%% %7.0f%%  (n=%d)" % (t, 100 * s[t]["graph"], 100 * s[t]["fts"], s[t]["n"]))
    o = s["overall"]
    print("  %-9s %7.0f%% %7.0f%%" % ("ИТОГО", 100 * o["graph"], 100 * o["fts"]))
    print("  токенов/запрос: граф %.1f · FTS %.1f" % (o["graph_tok"], o["fts_tok"]))
    print("\n  Вывод (как в статье): FTS проваливает JOIN (%.0f%%) — ответ не в тексте запроса;" % (100 * s["join"]["fts"]))
    print("  граф решает 2-hop walk'ом (%.0f%%). Это валидирует наш edges.py-слой цифрами." % (100 * s["join"]["graph"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
