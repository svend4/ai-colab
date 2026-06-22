#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тематические порталы (D-016) — лёгкая плагин-модель на файлах поверх универсального ядра.

Модель Википедии: ядро (универсальные движки files/workbench/knowledge) — одна большая
«энциклопедия»; **портал** — узкоспециализированная под-тема/подпапка/корпус (юр, соц, любая).
Домен живёт ВНУТРИ портала (его файлы + таксономия как данные в `portal.md`), а НЕ в коде ядра.
Универсальные движки работают на любом портале без изменений.

Портал = чистый L2 manifest `portals/<name>/portal.md` + операционный корпус `data/portals/<name>/`:
  - `portals/<name>/portal.md` — identity/config (corpus_ref, topics);
  - `data/portals/<name>/<corpus>/` — тематические файлы;
  - `data/portals/<name>/<name>.db` — генерируемая knowledge-память (runtime, в .gitignore).

Fallback: если `portals/<name>/portal.md` отсутствует, используется legacy `data/portals/<name>/portal.md`.

CLI:
    python tools/portal.py list
    python tools/portal.py new <name> [--desc "..."] [--corpus corpus]
    python tools/portal.py build <name>
    python tools/portal.py report <name> [--query ТЕКСТ] [--out reports/x.md]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _canon import parse_front_matter  # единый парсер front-matter
import knowledge as kn  # универсальный L6-движок ingest→query→report (ядро)

PORTALS = os.path.join(ROOT, "data", "portals")  # legacy/runtime data root
L2_PORTALS = os.path.join(ROOT, "portals")


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _list_field(value):
    s = (value or "").strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip() for x in s.split(",") if x.strip()]


def _manifest_path(name):
    l2 = os.path.join(L2_PORTALS, name, "portal.md")
    if os.path.exists(l2):
        return l2, "l2"
    legacy = os.path.join(PORTALS, name, "portal.md")
    if os.path.exists(legacy):
        return legacy, "legacy"
    raise FileNotFoundError("нет портала: %s" % name)


def _manifest(name):
    path, source = _manifest_path(name)
    with open(path, encoding="utf-8") as f:
        fm = parse_front_matter(f.read())
    fm["_manifest_path"] = path
    fm["_manifest_source"] = source
    fm["_corpus_subdir"] = fm.get("corpus") or "corpus"
    fm["_corpus_ref"] = fm.get("corpus_ref") or os.path.join("data", "portals", name, fm["_corpus_subdir"])
    fm["_topics"] = _list_field(fm.get("topics"))
    return fm


def _corpus_path(name, fm=None):
    fm = fm or _manifest(name)
    return fm["_corpus_ref"].replace("\\", "/")  # относительно ROOT


def _db_path(name):
    return os.path.join("data", "portals", name, "%s.db" % name)


def list_portals():
    names = set()
    for root in (PORTALS, L2_PORTALS):
        if os.path.isdir(root):
            for name in os.listdir(root):
                if os.path.isfile(os.path.join(root, name, "portal.md")):
                    names.add(name)
    out = []
    for name in sorted(names):
        fm = _manifest(name)
        out.append({"name": name, "title": fm.get("title", ""),
                    "topics": fm["_topics"], "corpus": _corpus_path(name, fm),
                    "source": fm["_manifest_source"]})
    return out


def new(name, desc="", corpus="corpus", topics=None):
    pdir = os.path.join(PORTALS, name)
    os.makedirs(os.path.join(pdir, corpus), exist_ok=True)
    topics_str = "[%s]" % ", ".join(topics) if topics else "[]"
    with open(os.path.join(pdir, "portal.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("---\nid: portal-%s\ntype: portal\ntitle: %s\ndescription: %s\ncorpus: %s\n"
                "topics: %s\n---\n\n# Портал: %s\n\n%s\n\nФайлы темы — в `%s/`. Сборка/отчёт:\n"
                "`python tools/portal.py report %s --query <термин>`.\n"
                % (name, name, desc, corpus, topics_str, name, desc, corpus, name))
    return pdir


def build(name):
    fm = _manifest(name)
    corpus = _corpus_path(name, fm)
    if not os.path.isdir(os.path.join(ROOT, corpus)):
        raise FileNotFoundError("нет корпуса портала: %s" % corpus)
    db = _db_path(name)
    n = kn.build(db, corpus)
    return n, db, fm


def report(name, query=None, out=None):
    n, db, fm = build(name)
    corpus = _corpus_path(name, fm)
    text = kn.report(corpus, db=db, query_text=query)
    # тематическое покрытие (таксономия портала — это ДАННЫЕ, не код ядра)
    topics = fm["_topics"]
    if topics:
        conn = kn.wb.init(db, base_dir=ROOT)
        try:
            lines = ["", "## Покрытие тем портала", "| Тема | Документов с совпадением |", "|---|---|"]
            for t in topics:
                hits = kn.fts_search(conn, t, limit=1000)
                lines.append("| %s | %d |" % (t, len(hits)))
        finally:
            conn.close()
        text = text + "\n" + "\n".join(lines)
    header = "> Портал **%s** (%s). Ядро универсально; тема — это контент портала (D-016).\n\n" % (
        name, fm.get("title", ""))
    text = header + text
    if out:
        kn.write_report(text, out)
    return text


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        if cmd == "list":
            for p in list_portals():
                print("%-16s topics=%s corpus=%s — %s"
                      % (p["name"], p["topics"], p["corpus"], p["title"]))
            return 0
        if cmd == "new" and len(a) > 1:
            desc = a[a.index("--desc") + 1] if "--desc" in a else ""
            corpus = a[a.index("--corpus") + 1] if "--corpus" in a else "corpus"
            pdir = new(a[1], desc=desc, corpus=corpus)
            print("создан портал: %s" % pdir)
            return 0
        if cmd == "build" and len(a) > 1:
            n, db, _ = build(a[1])
            print("портал %s: занесено %d документов → %s" % (a[1], n, db))
            return 0
        if cmd == "report" and len(a) > 1:
            query = a[a.index("--query") + 1] if "--query" in a else None
            out = a[a.index("--out") + 1] if "--out" in a else None
            print(report(a[1], query=query, out=out))
            return 0
    except Exception as exc:
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
