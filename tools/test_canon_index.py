"""Тест canon_index.py — SQLite/FTS5 индекс канона (build + search)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import canon_index as ci

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
        _w(d, "tasks", "a.md", "---\nid: T-1\ntype: task\n---\n# A\nкворум независимых судей против захвата оракула\n")
        _w(d, "decisions", "b.md", "---\nid: D-1\ntype: decision\n---\n# B\nкрдт мёрж канона field-level вместо строчных конфликтов\n")
        _w(d, "topics", "c.md", "---\nid: TOP-1\ntype: topic\n---\n# C\nпрогрессивное раскрытие меню заголовки детали\n")
        db = os.path.join(d, "idx.db")

        n, fts = ci.build(root=d, db_path=db, dirs=("tasks", "decisions", "topics"))
        if n != 3:
            fails.append("build: ожидалось 3 блока, проиндексировано %d" % n)
        if not os.path.exists(db):
            fails.append("build: файл индекса не создан")

        # поиск по уникальному термину → ровно тот блок
        r1 = ci.search("оракула", db_path=db)
        if not r1 or r1[0]["id"] != "T-1":
            fails.append("search 'оракула' → T-1 первым: %s" % r1)
        r2 = ci.search("мёрж", db_path=db)
        if not any(x["id"] == "D-1" for x in r2):
            fails.append("search 'мёрж' → D-1: %s" % r2)
        r3 = ci.search("раскрытие меню", db_path=db)
        if not any(x["id"] == "TOP-1" for x in r3):
            fails.append("search 'раскрытие меню' → TOP-1: %s" % r3)
        # тип сохранён
        if r1 and r1[0]["type"] != "task":
            fails.append("type должен индексироваться: %s" % r1[0])
        # несуществующее → пусто, не падает
        if ci.search("zzzнетничего", db_path=db) != []:
            fails.append("несуществующий запрос → пустой список")
        # индекс не построен → None (а не краш)
        if ci.search("x", db_path=os.path.join(d, "missing.db")) is not None:
            fails.append("нет индекса → None")

    print("FTS5 доступен: %s" % fts)
    if fails:
        print("FAIL test_canon_index:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_canon_index: build(3) · search уникальных терминов→верные блоки · type · пусто · нет-индекса→None")


if __name__ == "__main__":
    main()
