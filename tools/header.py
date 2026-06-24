"""
# ==========================================
# [FILE ID CARD]
# ID: tools.header
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт header.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""header.py — визитка-шапка файла (C-07: консенсус 2+ агентов) — извлечь/линтить/покрытие.

Архитектурный консенсус (topics/architecture-fundamentals §2 + razbor-consensus C-07): КАЖДЫЙ
значимый файл несёт визитку card→middle→base вверху — машино-парсимая карточка (что это / для чего
/ суть), общее→частное. Для .md — YAML front-matter; для .py — module docstring (1-я строка = суть).
header.py поднимает визитку с уровня сообщения (card.py) на уровень ФАЙЛА: извлекает card, линтит
наличие, считает покрытие. Минимальная визитка = title + gist (что это).

CLI:
    python tools/header.py card <file>          # показать визитку файла (card-уровень)
    python tools/header.py lint <file> [file…]  # файлы без валидной визитки (exit 1 если есть)
    python tools/header.py board [--json]        # покрытие визитками по docs/ + tools/
"""
import os
import re
import sys
import json
import glob

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
from _canon import parse_front_matter

configure_output()

# минимальные поля визитки (card-уровень): чем файл представляется машине/человеку
REQUIRED = ("title", "gist")


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _md_card(text):
    """Визитка .md: front-matter ИЛИ первый # заголовок + первая строка прозы."""
    fm = parse_front_matter(text) if text.startswith("---") else {}
    title = fm.get("title", "")
    gist = fm.get("gist") or fm.get("description") or fm.get("summary") or ""
    if not title:
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else ""
    if not gist:
        # первая непустая, не-heading, не-front-matter строка
        body = text.split("\n---", 2)[-1] if text.startswith("---") else text
        for line in body.splitlines():
            s = line.strip()
            if s and not s.startswith(("#", "-", "|", ">", "`", "<!--")):
                gist = s[:200]
                break
    return {"title": title, "gist": gist, "id": fm.get("id", ""),
            "type": fm.get("type", ""), "status": fm.get("status", ""), "has_fm": bool(fm)}


def _py_card(text):
    """Визитка .py: module docstring (1-я строка = суть)."""
    m = re.search(r'^\s*(?:#![^\n]*\n)?(?:#[^\n]*\n)*\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', text, re.S)
    doc = (m.group(1).strip() if m else "")
    first = doc.splitlines()[0].strip() if doc else ""
    # «name — суть» → title=name, gist=суть; иначе вся строка как gist
    if " — " in first:
        title, gist = first.split(" — ", 1)
    else:
        title, gist = first.split(":", 1) if ":" in first else (first, first)
    return {"title": title.strip(), "gist": gist.strip(), "id": "", "type": "script",
            "status": "", "has_fm": bool(doc)}


def card_of(path):
    text = _read(path)
    c = _py_card(text) if path.endswith(".py") else _md_card(text)
    c["path"] = os.path.relpath(path, ROOT).replace("\\", "/")
    c["missing"] = [k for k in REQUIRED if not c.get(k)]
    c["ok"] = not c["missing"]
    return c


def lint(paths):
    return [card_of(p) for p in paths if not card_of(p)["ok"]]


def _scan_targets():
    out = []
    for pat in ("docs/*.md", "topics/*.md", "tools/*.py"):
        for p in glob.glob(os.path.join(ROOT, pat)):
            b = os.path.basename(p)
            if b.startswith("test_") or b.startswith("_"):
                continue
            out.append(p)
    return out


def board(as_json=False):
    cards = [card_of(p) for p in _scan_targets()]
    n = len(cards) or 1
    ok = [c for c in cards if c["ok"]]
    miss = [c for c in cards if not c["ok"]]
    data = {"total": len(cards), "with_card": len(ok), "missing": len(miss),
            "coverage_pct": round(100 * len(ok) / n),
            "missing_files": [{"path": c["path"], "lacks": c["missing"]} for c in miss[:40]]}
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print("=== ВИЗИТКИ ФАЙЛОВ (C-07 покрытие) ===")
    print("  с визиткой: %d/%d (%d%%)   без: %d" % (len(ok), len(cards), data["coverage_pct"], len(miss)))
    if miss:
        print("\n  без валидной визитки (нет title/gist):")
        for c in miss[:40]:
            print("    %-52s нет: %s" % (c["path"], ",".join(c["missing"])))
        if len(miss) > 40:
            print("    … ещё %d" % (len(miss) - 40))
    return 0


def cmd_card(path):
    c = card_of(path if os.path.isabs(path) else os.path.join(ROOT, path))
    print("=== Визитка: %s ===" % c["path"])
    print("  title:  %s" % (c["title"] or "(нет)"))
    print("  gist:   %s" % (c["gist"] or "(нет)"))
    for k in ("id", "type", "status"):
        if c.get(k):
            print("  %-6s  %s" % (k + ":", c[k]))
    print("  визитка: %s" % ("OK" if c["ok"] else "НЕПОЛНАЯ (нет %s)" % ",".join(c["missing"])))
    return 0 if c["ok"] else 1


def main(argv):
    a = list(argv)
    as_json = "--json" in a
    pos = [x for x in a if not x.startswith("--")]
    if not pos or pos[0] == "board":
        return board(as_json=as_json)
    cmd = pos[0]
    if cmd == "card" and len(pos) >= 2:
        return cmd_card(pos[1])
    if cmd == "lint":
        files = [x if os.path.isabs(x) else os.path.join(ROOT, x) for x in pos[1:]]
        bad = lint(files)
        for c in bad:
            print("НЕПОЛНАЯ визитка: %s — нет %s" % (c["path"], ",".join(c["missing"])))
        if not bad:
            print("OK: все файлы несут визитку (title+gist)")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
