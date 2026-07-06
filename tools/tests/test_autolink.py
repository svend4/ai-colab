"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_autolink
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_autolink.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест autolink.py — advisory-предложения дозреть (type/gist/topic)."""
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
import autolink

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
        # T-1: без type (→type:task по префиксу), без gist но с прозой (→gist)
        _w(root, "tasks/T-1.md", "---\nid: T-1\ntitle: Без типа\nstatus: todo\n---\nПервая проза тут.\n")
        # D-1: изолят (нет структурных рёбер), активный, цитируется атомом T-2 → topic-предложение related:[T-2]
        _w(root, "decisions/D-1.md", "---\nid: D-1\ntype: decision\ntitle: Изолят\ngist: суть\nstatus: proposed\n---\nт\n")
        # T-2: цитирует D-1 в теле (cites), сам с type
        _w(root, "tasks/T-2.md", "---\nid: T-2\ntype: task\ntitle: Цитирующий\nstatus: open\n---\nсм D-1 для контекста\n")

        data = autolink.collect()

        # type-backfill: T-1 → task (детерминированно по префиксу)
        t1 = next((x for x in data["type"] if x["id"] == "T-1"), None)
        if not t1 or t1["suggest"] != "task":
            fails.append("T-1 type-backfill != task: %s" % t1)
        # D-1 уже имеет type → НЕ в type-предложениях
        if any(x["id"] == "D-1" for x in data["type"]):
            fails.append("D-1 (есть type) ложно в type-backfill")

        # gist-suggest: T-1 (title, без gist, проза) → есть
        g1 = next((x for x in data["gist"] if x["id"] == "T-1"), None)
        if not g1 or "проза" not in g1["suggest"].lower():
            fails.append("T-1 gist-suggest неверен: %s" % g1)
        # D-1 уже имеет gist → НЕ в gist
        if any(x["id"] == "D-1" for x in data["gist"]):
            fails.append("D-1 (есть gist) ложно в gist-suggest")

        # topic-suggest: D-1 изолят цитируется T-2 → related:[T-2] (семантический атом, не агрегат)
        tp = next((x for x in data["topic"] if x["id"] == "D-1"), None)
        if not tp or "T-2" not in tp["suggest"]:
            fails.append("D-1 topic-suggest не содержит T-2: %s" % tp)

    if fails:
        print("FAIL test_autolink:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_autolink: type-backfill(префикс) + gist(проза) + topic(семантич. цитирующие) + не-дубль")


if __name__ == "__main__":
    main()
