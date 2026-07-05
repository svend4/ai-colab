"""
# ==========================================
# [FILE ID CARD]
# ID: tools.folder_index
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт folder_index.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""folder_index.py — папка-индекс (навигация-через-метаданные, НЕ шардинг).

Из topics/navigation-vs-sharding-2026-06-24: вместо разрезания плоской папки — собрать ОДИН индекс
из визиток файлов (header.py) в отдельную папку `indexes/`. Машина и человек читают одно оглавление
(id/type/status/суть всех файлов + подпапки) вместо листинга сотен файлов. Плоская структура НЕ
трогается, читатели НЕ переписываются. Генерируется как index.json (--write) и верифицируется (--check).

CLI:
    python tools/folder_index.py write <dir>     # собрать indexes/<dir>.md из визиток
    python tools/folder_index.py check <dir>     # indexes/<dir>.md актуален? (exit 1 если устарел)
    python tools/folder_index.py write-all        # индексы для крупных папок (tasks/decisions/…)
"""
import os
import sys
import glob

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
from _cli import help_guard
import header

configure_output()

INDEXES = os.path.join(ROOT, "indexes")
BIG = ("tasks", "decisions", "questions", "docs", "topics", "drivers")


def _index_path(name):
    return os.path.join(INDEXES, name + ".md")


def build(dirpath):
    rel = os.path.relpath(dirpath, ROOT).replace("\\", "/")
    name = os.path.basename(rel.rstrip("/"))
    files = sorted(f for f in os.listdir(dirpath)
                   if os.path.isfile(os.path.join(dirpath, f))
                   and f.endswith(".md") and f not in ("INDEX.md", "README.md"))
    subs = sorted(d for d in os.listdir(dirpath)
                  if os.path.isdir(os.path.join(dirpath, d))
                  and not d.startswith((".", "_")) and d != "__pycache__")
    L = ["<!-- GENERATED folder_index.py — НЕ редактировать руками; навигация-через-метаданные -->",
         "# Индекс папки `%s/` — %d файлов%s" % (rel, len(files), (", %d подпапок" % len(subs)) if subs else ""),
         "",
         "> Машино- и человекочитаемое оглавление визиток (вместо шардинга плоской папки)."]
    if subs:
        L += ["", "## Подпапки", ""]
        for s in subs:
            L.append("- `%s/%s/`" % (rel, s))
    L += ["", "## Файлы (визитки)", "", "| файл | type | status | суть |", "|---|---|---|---|"]
    for f in files:
        c = header.card_of(os.path.join(dirpath, f))
        gist = (c.get("gist", "") or "").replace("|", "/").replace("\n", " ")[:90]
        L.append("| [%s](../%s/%s) | %s | %s | %s |"
                 % (f, rel, f, c.get("type", "") or "—", c.get("status", "") or "—", gist or "—"))
    return "\n".join(L) + "\n"


def write(name):
    # direct-write-ok: генерат indexes/<name>.md — переписывается целиком по определению;
    # канон-каталоги здесь только ЧИТАЮТСЯ для оглавления (C33)
    dirpath = os.path.join(ROOT, name)
    if not os.path.isdir(dirpath):
        print("нет папки %s" % name)
        return 2
    os.makedirs(INDEXES, exist_ok=True)
    content = build(dirpath)
    with open(_index_path(name), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("Записан indexes/%s.md (%d строк)" % (name, content.count("\n")))
    return 0


def check(name):
    dirpath = os.path.join(ROOT, name)
    ip = _index_path(name)
    if not os.path.isfile(ip):
        print("STALE: нет indexes/%s.md" % name)
        return 1
    cur = open(ip, encoding="utf-8").read()
    if cur != build(dirpath):
        print("STALE: indexes/%s.md устарел — `folder_index.py write %s`" % (name, name))
        return 1
    print("OK: indexes/%s.md актуален" % name)
    return 0


def main(argv):
    help_guard(__doc__, argv)
    a = list(argv)
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    if cmd in ("write-all", "check-all"):
        rc = 0
        for n in BIG:
            if os.path.isdir(os.path.join(ROOT, n)):
                rc |= (write(n) if cmd == "write-all" else check(n))
        return rc
    if cmd in ("write", "check") and len(a) >= 2:
        name = os.path.basename(a[1].rstrip("/\\"))
        return write(name) if cmd == "write" else check(name)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
