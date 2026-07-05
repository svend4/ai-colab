# ==========================================
# [FILE ID CARD]
# ID: tools.canon_index
# TYPE: active-script
# DOMAIN: core.indexing
# DEPTH_LEVEL: 1
# SUMMARY: SQLite/FTS5 индекс канона (workbench-компонент 5: быстрая память/retrieval).
# ==========================================
"""canon_index.py — SQLite/FTS5 индекс канона (workbench-компонент 5: быстрая память/retrieval).

Этап 1 roadmap offline/headless workbench (topics/offline-headless-workbench-mvp-2026-06-26). Индексирует
канон в SQLite FTS5 → агент/runner тянет релевантные блоки запросом, а не весь репо (питает view.py).
Дополняет граф-оси (portals/edges) полнотекстовой осью. Stdlib (sqlite3); FTS5 с деградацией к LIKE.

CLI:
  python tools/canon_index.py build                 # (пере)собрать индекс indexes/canon.db
  python tools/canon_index.py search "<запрос>"      # FTS-поиск, ранжированный
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import glob
import sqlite3

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
DB = os.path.join(ROOT, "indexes", "canon.db")
# Единый реестр каталогов канона — из _canon (P9-a, волна 2); локальная копия запрещена.
from _canon import CANON_DIRS, require_canon_dirs


def build(root=ROOT, db_path=DB, dirs=CANON_DIRS):
    """(Пере)собрать индекс: канон-файлы → FTS5 (или обычная таблица при отсутствии FTS5). Возвращает счёт."""
    items = _collect(root, dirs)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    fts = _has_fts5(conn)
    conn.execute("DROP TABLE IF EXISTS canon")
    if fts:
        conn.execute("CREATE VIRTUAL TABLE canon USING fts5(id, path, type, body)")
    else:
        conn.execute("CREATE TABLE canon(id TEXT, path TEXT, type TEXT, body TEXT)")
    conn.executemany("INSERT INTO canon(id, path, type, body) VALUES(?,?,?,?)",
                     [(it["id"], it["path"], it["type"], it["body"]) for it in items])
    conn.commit()
    conn.close()
    return len(items), fts


def search(query, db_path=DB, limit=10):
    """FTS-поиск по индексу → [{id, path, type, snippet}] ранжированный (bm25 при FTS5, иначе LIKE)."""
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    try:
        fts = _table_is_fts(conn)
        if fts:
            rows = conn.execute(
                "SELECT id, path, type, snippet(canon, 3, '[', ']', '…', 8) FROM canon "
                "WHERE canon MATCH ? ORDER BY bm25(canon) LIMIT ?",
                (_fts_query(query), limit)).fetchall()
        else:
            like = "%" + query.replace("%", "") + "%"
            rows = conn.execute(
                "SELECT id, path, type, substr(body,1,80) FROM canon WHERE body LIKE ? OR id LIKE ? LIMIT ?",
                (like, like, limit)).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        conn.close()
    return [{"id": r[0], "path": r[1], "type": r[2], "snippet": (r[3] or "").replace("\n", " ")} for r in rows]


def _collect(root, dirs):
    # Контракт P9: несуществующий канон-каталог → FileNotFoundError, а не тихий пустой индекс.
    require_canon_dirs(root, dirs)
    out = []
    for d in dirs:
        for p in glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True):
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            fm = text[:800]
            fid = (re.search(r"^id:\s*(.+)$", fm, re.M) or [None, os.path.splitext(os.path.basename(p))[0]])[1].strip() \
                if re.search(r"^id:\s*(.+)$", fm, re.M) else os.path.splitext(os.path.basename(p))[0]
            ftype = (re.search(r"^type:\s*(.+)$", fm, re.M) or [None, ""])
            ftype = ftype.group(1).strip() if hasattr(ftype, "group") else ""
            out.append({"id": fid, "path": os.path.relpath(p, root).replace("\\", "/"),
                        "type": ftype, "body": _body(text)})
    return out


def _body(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            nl = text.find("\n", end + 1)
            return text[nl + 1:] if nl >= 0 else ""
    return text


def _has_fts5(conn):
    try:
        conn.execute("CREATE VIRTUAL TABLE _fts5probe USING fts5(x)")
        conn.execute("DROP TABLE _fts5probe")
        return True
    except sqlite3.OperationalError:
        return False


def _table_is_fts(conn):
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name='canon'").fetchone()
    return bool(row) and "fts5" in (row[0] or "").lower()


def _fts_query(q):
    terms = [t for t in re.findall(r"[0-9A-Za-zА-Яа-яёЁ_]{2,}", q)]
    return " OR ".join('"%s"' % t for t in terms) if terms else '""'


def main(argv):
    help_guard(__doc__, argv)
    import json
    args = [a for a in argv if not a.startswith("--")]
    cmd = args[0] if args else "build"
    if cmd == "build":
        n, fts = build()
        print("=== ИНДЕКС КАНОНА: %d блоков → %s (%s) ===" % (
            n, os.path.relpath(DB, ROOT).replace("\\", "/"), "FTS5" if fts else "LIKE-fallback"))
        return 0
    if cmd == "search":
        if len(args) < 2:
            print("canon_index: search требует запрос"); return 2
        res = search(" ".join(args[1:]))
        if res is None:
            print("canon_index: индекс не построен — сначала `canon_index.py build`"); return 2
        if "--json" in argv:
            print(json.dumps(res, ensure_ascii=False, indent=2)); return 0
        print("=== ПОИСК «%s» — %d попаданий ===" % (" ".join(args[1:]), len(res)))
        for r in res:
            print("  %-30s [%s] %s" % (r["id"][:30], r["type"] or "—", r["path"]))
            if r["snippet"]:
                print("       %s" % r["snippet"][:90])
        return 0
    print("canon_index: команда build | search"); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
