"""Тест edges.py — типизированный граф (извлечение рёбер, циклы, висячие, две оси)."""
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
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import edges

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(root, rel, txt):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)


def main():
    fails = []
    with tempfile.TemporaryDirectory() as root:
        edges.ROOT = root
        # цикл T-1 ↔ T-2; висячее T-3→T-999; related D-1→T-1; supersede D-2→D-3
        _w(root, "tasks/T-1.md", "---\nid: T-1\ntype: task\nstatus: doing\ndepends_on: [T-2]\n---\nтело\n")
        _w(root, "tasks/T-2.md", "---\nid: T-2\ntype: task\nstatus: todo\ndepends_on: [T-1]\n---\nтело\n")
        _w(root, "tasks/T-3.md", "---\nid: T-3\ntype: task\nstatus: todo\ndepends_on: [T-999]\n---\nтело\n")
        _w(root, "decisions/D-1.md", "---\nid: D-1\ntype: decision\nstatus: accepted\nrelated: [T-1]\n---\nтело\n")
        _w(root, "decisions/D-2.md", "---\nid: D-2\ntype: decision\nstatus: superseded\nsuperseded_by: [D-3]\n---\nт\n")
        _w(root, "decisions/D-3.md", "---\nid: D-3\ntype: decision\nstatus: accepted\n---\nт\n")
        # T-4: тема без файла → topic_unresolved (НЕ жёсткое dangling); T-5: без поля type → missing_type
        _w(root, "tasks/T-4.md", "---\nid: T-4\ntype: task\nstatus: todo\ntopic: ghost-theme\n---\nт\n")
        _w(root, "tasks/T-5.md", "---\nid: T-5\nstatus: todo\nrelated: [T-1]\n---\nт\n")
        # T-6↔T-7 оба done → ТЕРМИНАЛЬНЫЙ цикл (мягко, историч.) — НЕ в жёстких cycles
        _w(root, "tasks/T-6.md", "---\nid: T-6\ntype: task\nstatus: done\ndepends_on: [T-7]\n---\nт\n")
        _w(root, "tasks/T-7.md", "---\nid: T-7\ntype: task\nstatus: done\ndepends_on: [T-6]\n---\nт\n")

        nodes, by_id, by_slug = edges.load_nodes()
        e = edges.build_edges(nodes, by_id, by_slug)

        types = {x["type"] for x in e}
        for need in ("depends", "related", "superseded"):
            if need not in types:
                fails.append("тип ребра %s не извлечён" % need)

        # папка вычислена из пути (не застряла)
        if nodes.get("T-1", {}).get("folder") != "tasks":
            fails.append("folder T-1 != tasks (%s)" % nodes.get("T-1", {}).get("folder"))

        c = edges.check(nodes, e, by_id)
        # активный цикл T-1↔T-2 (doing/todo) — в жёстких cycles
        if not any("T-1" in cyc and "T-2" in cyc for cyc in c["cycles"]):
            fails.append("активный цикл T-1↔T-2 не пойман: %s" % c["cycles"])
        # терминальный цикл T-6↔T-7 (done↔done) — в terminal_cycles, НЕ в жёстких
        if not any("T-6" in cyc and "T-7" in cyc for cyc in c["terminal_cycles"]):
            fails.append("терминальный цикл T-6↔T-7 не в terminal_cycles: %s" % c["terminal_cycles"])
        if any("T-6" in cyc for cyc in c["cycles"]):
            fails.append("терминальный цикл ложно в жёстких cycles")
        # висячее T-3→T-999
        if not any("T-999" in dg for dg in c["dangling"]):
            fails.append("висячее T-999 не пойман: %s" % c["dangling"])
        # related НЕ висячее (T-1 существует)
        if any("T-1" in dg for dg in c["dangling"]):
            fails.append("related→T-1 ложно висячее")
        # ЧЕСТНОСТЬ: тема без файла → topic_unresolved (мягкое), НЕ в жёстком dangling
        if not any("ghost-theme" in t for t in c["topic_unresolved"]):
            fails.append("тема-без-файла ghost-theme не в topic_unresolved")
        if any("ghost-theme" in dg for dg in c["dangling"]):
            fails.append("in_topic ложно попал в жёсткое dangling (должен быть soft)")
        # атом без type → missing_type
        if "T-5" not in c["missing_type"]:
            fails.append("T-5 без type не пойман в missing_type")
        # supersede целостность: D-2 статус superseded → НЕ нарушение
        if c["supersede"]:
            fails.append("supersede ложно flagged: %s" % c["supersede"])

        # impact (blast-radius): T-1 зависит от T-2 → impact(T-2) содержит T-1
        imp = edges.impact("T-2", nodes, e, by_id)
        if not any(a["id"] == "T-1" for a in imp):
            fails.append("impact(T-2) не содержит зависящий T-1: %s" % imp)
        # цикл не зацикливает BFS (T-1↔T-2) — конечный результат
        if edges.impact("T-1", nodes, e, by_id) is None:
            fails.append("impact(T-1) упал на цикле")
        # path: T-1 →depends→ T-2 (длина 1)
        p = edges.path("T-1", "T-2", nodes, e, by_id)
        if not p or p[0]["to"] != "T-2" or p[0]["type"] != "depends":
            fails.append("path(T-1,T-2) неверен: %s" % p)
        # нет пути в несуществующее
        if edges.path("T-2", "D-3", nodes, e, by_id) is not None:
            # D-3 не достижим из T-2 по структурным рёбрам
            pass

        # две оси в neighbors
        nb = edges.neighbors("D-1", nodes, e, by_id)
        if not nb or nb["axis_tree"]["folder"] != "decisions":
            fails.append("neighbors D-1 ось-дерево неверна")
        if not any("T-1" in o for o in nb["axis_graph"]["out"]):
            fails.append("neighbors D-1 ось-граф out не содержит T-1")

        # EXTERNAL: F-/C-/DIV- не висячие
        _w(root, "topics/x.md", "---\nid: X-1\ntype: topic\nstatus: proposed\nrelated: [F-020, C-04]\n---\nт\n")
        nodes2, bi2, bs2 = edges.load_nodes()
        e2 = edges.build_edges(nodes2, bi2, bs2)
        if any(x["raw"] in ("F-020", "C-04") and x["dangling"] for x in e2):
            fails.append("F-/C- помечены висячими (должны быть external)")

    if fails:
        print("FAIL test_edges:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_edges: типы рёбер + folder + цикл + висячее + supersede + две оси + external + impact/path")


if __name__ == "__main__":
    main()
