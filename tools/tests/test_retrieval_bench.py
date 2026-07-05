"""Тест retrieval_bench.py — граф решает JOIN, FTS проваливает (воспроизводит вывод статьи на наших инструментах)."""
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
import time
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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

    # уборка за собой (аудит C50): main() обязан удалить свой tmp-work/retrieval_bench_<pid> в finally,
    # а write_fixture — закрывать дескрипторы (на Windows незакрытый файл блокирует rmtree)
    cli_tmp = os.path.join(rb.ROOT, "tmp-work", "retrieval_bench_%d" % os.getpid())
    rc = rb.main([])
    if rc != 0:
        fails.append("main([]) должен вернуть 0: %s" % rc)
    if os.path.isdir(cli_tmp):
        fails.append("main() не убрал за собой временный каталог: %s" % cli_tmp)
        shutil.rmtree(cli_tmp, ignore_errors=True)

    if fails:
        print("FAIL test_retrieval_bench:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_retrieval_bench: graph_walk(1/2/0-hop) · граф JOIN=100%% · FTS JOIN=0%% · граф>FTS overall · FTS силён на distant · токены · main() убирает tmp")


if __name__ == "__main__":
    main()
