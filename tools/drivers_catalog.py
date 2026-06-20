#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор каталога драйверов (T-030).

Собирает `drivers/index.json` (машинный срез) и `drivers/CATALOG.md` (человеческая
таблица) из front-matter всех `drivers/*.md`, кроме служебных (README/_template/SCHEMA/CATALOG).

    python tools/drivers_catalog.py          # переписать index.json + CATALOG.md
    python tools/drivers_catalog.py --check   # ничего не писать; exit 1, если каталог устарел
"""
import os
import sys
import glob
import json


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS = os.path.join(ROOT, "drivers")
SKIP = {"README.md", "_template.md", "SCHEMA.md", "CATALOG.md"}
FIELDS = ["id", "title", "level", "mode", "risk", "status", "sandbox", "secrets", "activation"]


def parse_fm(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def collect():
    items = []
    for path in sorted(glob.glob(os.path.join(DRIVERS, "*.md"))):
        if os.path.basename(path) in SKIP:
            continue
        with open(path, encoding="utf-8") as f:
            fm = parse_fm(f.read())
        if not fm.get("id"):
            continue
        items.append({k: fm.get(k, "") for k in FIELDS})
    items.sort(key=lambda d: d["id"])
    return items


def render_catalog(items):
    out = [
        "# Каталог драйверов (Treiber)",
        "",
        "Генерируется `tools/drivers_catalog.py` из `drivers/*.md` — не править вручную.",
        "",
        "| ID | Драйвер | Уровень | Режим | Риск | Статус |",
        "|---|---|---|---|---|---|",
    ]
    for d in items:
        out.append("| %s | %s | %s | %s | %s | %s |"
                   % (d["id"], d["title"], d["level"], d["mode"], d["risk"], d["status"]))
    return "\n".join(out) + "\n"


def main():
    check = "--check" in sys.argv[1:]
    items = collect()
    index_text = json.dumps({"drivers": items}, ensure_ascii=False, indent=2) + "\n"
    catalog_text = render_catalog(items)

    targets = [("index.json", index_text), ("CATALOG.md", catalog_text)]
    stale = False
    for fname, new in targets:
        path = os.path.join(DRIVERS, fname)
        old = ""
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = f.read()
        if old != new:
            stale = True
            if check:
                print("STALE: drivers/%s" % fname)
            else:
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new)
                print("OK: обновлён drivers/%s" % fname)
        else:
            print("OK: drivers/%s актуален" % fname)

    if check and stale:
        print("Каталог драйверов устарел — запусти: python tools/drivers_catalog.py")
        return 1
    print("Драйверов в каталоге: %d" % len(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
