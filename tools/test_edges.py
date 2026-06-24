"""Тест edges.py — типизированный граф (извлечение рёбер, циклы, висячие, две оси)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
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
        # цикл T-1↔T-2 найден
        if not any("T-1" in cyc and "T-2" in cyc for cyc in c["cycles"]):
            fails.append("цикл T-1↔T-2 не пойман: %s" % c["cycles"])
        # висячее T-3→T-999
        if not any("T-999" in dg for dg in c["dangling"]):
            fails.append("висячее T-999 не пойман: %s" % c["dangling"])
        # related НЕ висячее (T-1 существует)
        if any("T-1" in dg for dg in c["dangling"]):
            fails.append("related→T-1 ложно висячее")
        # supersede целостность: D-2 статус superseded → НЕ нарушение
        if c["supersede"]:
            fails.append("supersede ложно flagged: %s" % c["supersede"])

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
    print("OK test_edges: типы рёбер + folder + цикл + висячее + supersede + две оси + external")


if __name__ == "__main__":
    main()
