"""Тест view.py — срез канона обходом рёбер (related/[[links]]) + frozen/live + budget."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view as v

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(d, sub, name, txt):
    os.makedirs(os.path.join(d, sub), exist_ok=True)
    open(os.path.join(d, sub, name), "w", encoding="utf-8", newline="\n").write(txt)


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        _w(d, "tasks", "a.md", "---\nid: a\nrelated: [b]\n---\n# A\nтело альфа первая строка\nвторая строка деталь глубже\n")
        _w(d, "tasks", "b.md", "---\nid: b\n---\n# B\nсм [[c]] подробнее тело бета содержание\n")
        _w(d, "tasks", "c.md", "---\nid: c\n---\n# C\nлист тело гамма содержание блока\n")
        _w(d, "decisions", "z.md", "---\nid: z\n---\n# Z\nнесвязанный блок дзета содержание\n")

        canon = v.load_canon(root=d)
        if set(canon) != {"a", "b", "c", "z"}:
            fails.append("load_canon: ожидалось {a,b,c,z}, получено %s" % set(canon))
        if canon["a"]["links"] != {"b"}:
            fails.append("a.related должно дать {b}: %s" % canon["a"]["links"])
        if "c" not in canon["b"]["links"]:
            fails.append("b body [[c]] должно дать ссылку c: %s" % canon["b"]["links"])

        # depth 1: a→b ; depth 2: +c ; z никогда
        s1 = set(v.slice_ids(canon, "a", 1))
        if s1 != {"a", "b"}:
            fails.append("slice depth1 должно быть {a,b}: %s" % s1)
        s2 = set(v.slice_ids(canon, "a", 2))
        if s2 != {"a", "b", "c"}:
            fails.append("slice depth2 должно быть {a,b,c}: %s" % s2)
        if "z" in s2:
            fails.append("несвязанный z не должен попасть в срез")

        # live = путь + GIST (первая строка); frozen = всё тело
        live, _ = v.assemble(canon, ["a", "b"], "live")
        if "tasks/a.md" not in live or "вторая строка деталь" in live:
            fails.append("live: путь+gist без глубоких строк тела: %s" % live[:90])
        frozen, _ = v.assemble(canon, ["a", "b"], "frozen")
        if "вторая строка деталь" not in frozen:
            fails.append("frozen: всё тело должно быть инлайн")

        # budget: крошечный → усечение
        ftxt, used = v.assemble(canon, ["a", "b", "c"], "frozen", budget=10)
        if "усечён по бюджету" not in ftxt:
            fails.append("budget=10 должен усечь срез: %s" % ftxt[:60])

    if fails:
        print("FAIL test_view:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_view: load_canon(related+[[links]]) · slice depth1/2 · z-исключён · live/frozen · budget-усечение")


if __name__ == "__main__":
    main()
