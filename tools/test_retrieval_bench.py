"""Тест retrieval_bench.py — граф решает JOIN, FTS проваливает (воспроизводит вывод статьи на наших инструментах)."""
import os
import sys
import time
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import retrieval_bench as rb

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []

    # graph_walk: 1-hop direct, 2-hop join, 0-hop lookup
    edges = rb.build_edges()
    if rb.graph_walk(edges, "T-A", 1, "depends") != {"T-B"}:
        fails.append("1-hop depends T-A → {T-B}")
    if rb.graph_walk(edges, "T-A", 2, "depends") != {"T-C"}:
        fails.append("2-hop (JOIN) depends T-A → {T-C}")
    if rb.graph_walk(edges, "T-C", 0, None) != {"T-C"}:
        fails.append("0-hop lookup → {T-C}")

    # полный прогон на временном корне
    tmp = os.path.join(REPO_ROOT, "tmp-work", "rbench_test_%d_%d" % (os.getpid(), time.time_ns()))
    os.makedirs(tmp, exist_ok=True)
    try:
        rows = rb.run(tmp, os.path.join(tmp, "idx.db"))
        s = rb.summarize(rows)

        # ГЛАВНОЕ (вывод статьи на наших инструментах): граф решает JOIN, FTS — нет
        if s["join"]["graph"] != 1.0:
            fails.append("граф должен решать JOIN 100%%: %s" % s["join"]["graph"])
        if s["join"]["fts"] != 0.0:
            fails.append("FTS должен проваливать JOIN (0%%): %s" % s["join"]["fts"])
        if not (s["overall"]["graph"] > s["overall"]["fts"]):
            fails.append("граф overall > FTS overall: %s vs %s" % (s["overall"]["graph"], s["overall"]["fts"]))
        # FTS силён на distant (контент), это его зона
        if s["distant"]["fts"] < 0.5:
            fails.append("FTS должен ловить distant по контенту: %s" % s["distant"]["fts"])
        # токены графа меньше (ответ = id, не сниппет)
        if not (s["overall"]["graph_tok"] <= s["overall"]["fts_tok"]):
            fails.append("граф токенов ≤ FTS: %s vs %s" % (s["overall"]["graph_tok"], s["overall"]["fts_tok"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("FAIL test_retrieval_bench:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_retrieval_bench: graph_walk(1/2/0-hop) · граф JOIN=100%% · FTS JOIN=0%% · граф>FTS overall · FTS силён на distant · токены")


if __name__ == "__main__":
    main()
