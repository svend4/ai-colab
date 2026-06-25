"""Тест portals.py — средний слой: варианты → порталы по содержанию (тема)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import portals as pt

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(d, name, body):
    p = os.path.join(d, name)
    open(p, "w", encoding="utf-8", newline="\n").write(body)
    return p


def main():
    fails = []

    # content_sim: одинаковые → 1, дизъюнктные → 0
    ta = pt._tokens("консенсус независимость свидетели сверка")
    if pt.content_sim(ta, ta) != 1.0:
        fails.append("content_sim идентичных != 1")
    if pt.content_sim(ta, pt._tokens("драйвер песочница исполнение реестр")) != 0.0:
        fails.append("content_sim дизъюнктных != 0")

    with tempfile.TemporaryDirectory() as d:
        # 2 варианта темы-А (общая лексика) + 2 темы-Б (другая лексика, дизъюнктны)
        a1 = _w(d, "a1.md", "консенсус независимость свидетели сверка варианты слепота")
        a2 = _w(d, "a2.md", "консенсус независимость сверка варианты голоса меньшинство")
        b1 = _w(d, "b1.md", "драйвер песочница исполнение реестр манифест очередь")
        b2 = _w(d, "b2.md", "драйвер песочница реестр манифест конвейер диспетч")

        ps = pt.portals([a1, a2, b1, b2], thr=0.2)
        if len(ps) != 2:
            fails.append("ожидалось 2 портала (тема-А, тема-Б), получено %d" % len(ps))
        else:
            sets = [{v["name"] for v in p} for p in ps]
            if {"a1.md", "a2.md"} not in sets:
                fails.append("a1,a2 должны быть в одном портале (тема-А): %s" % sets)
            if {"b1.md", "b2.md"} not in sets:
                fails.append("b1,b2 должны быть в одном портале (тема-Б): %s" % sets)

        r = pt.analyze([a1, a2, b1, b2], thr=0.2)
        if r["n_portals"] != 2 or r["n_variants"] != 4:
            fails.append("analyze: 2 портала из 4 вариантов: %s" % r)

    if fails:
        print("FAIL test_portals:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_portals: content_sim · тема-А и тема-Б → 2 портала (родственное сводится локально)")


if __name__ == "__main__":
    main()
