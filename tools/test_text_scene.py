"""Тест text_scene.py — abstraction-view: build_cells(depth/type) · L0/L1/L2 раскрытие · diffuse-порядок · clamp · HTML-escape."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import text_scene as ts

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _canon():
    return {
        "seed": {"id": "seed", "path": "topics/seed.md",
                 "body": "# Seed\nкорневая общая тема узла\nГЛУБ-seed только-в-теле деталь", "links": {"a", "b"}},
        "a": {"id": "a", "path": "tasks/a.md",
              "body": "# A title\nсуть задачи а кратко\nГЛУБ-a только-в-теле деталь", "links": {"c"}},
        "b": {"id": "b", "path": "decisions/b.md",
              "body": "# B title\nсуть решения бэ кратко\nГЛУБ-b только-в-теле деталь", "links": set()},
        "c": {"id": "c", "path": "topics/c.md",
              "body": "# C title\nсуть листа це кратко\nГЛУБ-c только-в-теле деталь", "links": set()},
    }


def main():
    fails = []
    canon = _canon()

    # 1) build_cells: порядок BFS+sorted, глубина, тип из пути
    cells = ts.build_cells(canon, "seed", 2)
    ids = [c["id"] for c in cells]
    if ids != ["seed", "a", "b", "c"]:
        fails.append("порядок должен быть детерм. BFS [seed,a,b,c]: %s" % ids)
    depths = {c["id"]: c["depth"] for c in cells}
    if (depths.get("seed"), depths.get("a"), depths.get("b"), depths.get("c")) != (0, 1, 1, 2):
        fails.append("глубины: seed0 a1 b1 c2, получено %s" % depths)
    types = {c["id"]: c["type"] for c in cells}
    if types != {"seed": "topic", "a": "task", "b": "decision", "c": "topic"}:
        fails.append("тип из пути: %s" % types)

    # 2) L0 — только шапка (нет тела/гиста); L1 — +gist; L2 — +тело
    l0 = ts.render_ansi(cells, 0, 3)
    l1 = ts.render_ansi(cells, 1, 3)
    l2 = ts.render_ansi(cells, 2, 3)
    if "суть задачи а" in l0:
        fails.append("L0 не должен показывать gist")
    if "суть задачи а" not in l1:
        fails.append("L1 должен показывать gist")
    if "ГЛУБ-a" in l1:
        fails.append("L1 не должен показывать тело (ГЛУБ-a)")
    if "ГЛУБ-a" not in l2:
        fails.append("L2 должен показывать тело (ГЛУБ-a)")

    # 3) diffuse: первый кадр без тел, последний — все тела; порядок раскрытия = глубина (seed раньше c)
    frames = ts.diffuse(cells, 3, 3)  # steps=3: alpha 0, .5, 1
    if "ГЛУБ-seed" in frames[0] or "ГЛУБ-c" in frames[0]:
        fails.append("первый кадр (alpha=0) не должен раскрывать тела")
    if "ГЛУБ-seed" not in frames[-1] or "ГЛУБ-c" not in frames[-1]:
        fails.append("последний кадр (alpha=1) должен раскрыть все тела")
    mid = frames[1]  # k=round(.5*4)=2 → seed,a раскрыты, c нет
    if "ГЛУБ-seed" not in mid or "ГЛУБ-c" in mid:
        fails.append("раскрытие идёт от общего(seed) к частному(c): mid должен иметь seed, не c")

    # 4) clamp: все строки карточки РОВНО ширины CARD_W даже на огромных полях
    big = {"id": "x" * 80, "type": "task", "path": "tasks/x.md", "depth": 0, "title": "t",
           "gist": "g" * 200, "body": ("b" * 200 + "\n") * 3, "links": ["y" * 40, "z" * 40]}
    widths = {len(ln) for ln in ts.render_card(big, 2)}
    if widths != {ts.CARD_W}:
        fails.append("R-clamp: все строки карточки == CARD_W, получено ширины %s" % widths)

    # 5) HTML: <details>-сетка + XSS-escaping тела
    canon2 = dict(canon)
    canon2["a"] = dict(canon["a"]); canon2["a"]["body"] = "# A\nопасное <script>alert(1)</script> тело"
    htm = ts.render_html(ts.build_cells(canon2, "seed", 2), 3)
    if "<details>" not in htm or "grid-template-columns" not in htm:
        fails.append("HTML должен быть CSS-grid из <details>")
    if "&lt;script&gt;" not in htm or "<script>alert" in htm:
        fails.append("HTML должен экранировать тело (XSS)")

    # 6) детерминизм рендера: два вызова идентичны
    if ts.render_ansi(cells, 1, 3) != ts.render_ansi(cells, 1, 3):
        fails.append("render_ansi должен быть детерминирован")

    # 7) seed не найден → пусто
    if ts.build_cells(canon, "НЕТ", 2) != []:
        fails.append("несуществующий seed → []")

    if fails:
        print("FAIL test_text_scene:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_text_scene: build_cells(BFS+depth+type) · L0/L1/L2 раскрытие · diffuse(общее→частное) · clamp · HTML-escape · детерм.")


if __name__ == "__main__":
    main()
