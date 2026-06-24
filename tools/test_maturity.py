"""Тест maturity.py — зрелость 0-1000‰ как синтез 5 осей (DIV-21)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edges
import decay
import maturity

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
        decay.ROOT = root
        # T-1: все 5 осей → 1000‰ (id+type+title+gist, ребро depends, done=fresh+resolved)
        _w(root, "tasks/T-1.md", "---\nid: T-1\ntype: task\ntitle: Полный\ngist: одна фраза\nstatus: done\ndepends_on: [T-2]\n---\nт\n")
        # T-2: без gist (card✗), но связан (цель ребра), done → 800‰
        _w(root, "tasks/T-2.md", "---\nid: T-2\ntype: task\ntitle: Без гиста\nstatus: done\n---\nт\n")
        # T-3: без type(identity✗) без gist(card✗) изолят(connected✗) todo(resolved✗), но свежий(fresh✓) → 200‰
        _w(root, "tasks/T-3.md", "---\nid: T-3\ntitle: Сырой\nstatus: todo\n---\nт\n")

        rows = maturity.collect()
        by = {r["id"]: r for r in rows}

        if by.get("T-1", {}).get("score") != 1000:
            fails.append("T-1 (все оси) != 1000: %s" % by.get("T-1", {}).get("score"))
        if by.get("T-2", {}).get("score") != 800:
            fails.append("T-2 (без gist) != 800: %s (axes %s)" % (by.get("T-2", {}).get("score"), by.get("T-2", {}).get("axes")))
        if by.get("T-3", {}).get("score") != 200:
            fails.append("T-3 (сырой) != 200: %s (axes %s)" % (by.get("T-3", {}).get("score"), by.get("T-3", {}).get("axes")))

        # T-3 в недозрелых (<600); отсортированы по возрастанию (T-3 первый)
        if rows and rows[0]["id"] != "T-3":
            fails.append("сортировка: самый сырой не первый: %s" % [r["id"] for r in rows])
        # ось connected: T-1 и T-2 связаны (depends), T-3 — нет
        if not by["T-1"]["axes"]["connected"] or by["T-3"]["axes"]["connected"]:
            fails.append("ось connected неверна")
        # ось identity: T-3 без type → False
        if by["T-3"]["axes"]["identity"]:
            fails.append("T-3 без type ложно identity=True")

    if fails:
        print("FAIL test_maturity:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_maturity: 5 осей (identity/card/connected/fresh/resolved) + балл + сортировка")


if __name__ == "__main__":
    main()
