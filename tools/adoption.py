"""
# ==========================================
# [FILE ID CARD]
# ID: tools.adoption
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт adoption.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""adoption.py — статические метрики ПРИМЕНЕНИЯ (повторяемый блок само-мониторинга).

Операционализирует один-разовый adoption-аудит (`topics/adoption-statistics-2026-06-23.md`,
30 агентов) в дешёвый детерминированный детектор: dormant-инструменты, декларативные решения,
orphan-доки. Рекурсивное само-улучшение — «применяется ли накопленное» мерится автоматически
одной командой, а не воркфлоу. Встроен нюанс FINDER: manual-CLI (есть main + doc-ссылки, но
0 code-вызывателей) ≠ dead.

CLI:
    python tools/adoption.py            # человекочитаемая сводка
    python tools/adoption.py --json     # машинно
    python tools/adoption.py --list dormant   # списком: dormant|declarative|orphan
    python tools/adoption.py --save-baseline  # зафиксировать снимок метрик (RSI re-measure)
    python tools/adoption.py --delta [--json] # дельта vs baseline: сдвинулась ли игла применения
"""
import os
from _ioutil import configure_output
import re
import sys
import json
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _tool_stems():
    """tools/*.py кроме тестов и приватных _*.py-хелперов? — нет, _canon считается. Только не test_."""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        b = os.path.basename(p)
        if b.startswith("test_"):
            continue
        out.append((b[:-3], p))  # (stem, path)
    return out


def _concat(paths):
    return "\n".join(_read(p) for p in paths)


def _all_md():
    md = []
    for dirpath, _dirs, files in os.walk(ROOT):
        if any(seg in dirpath for seg in (os.sep + ".git", os.sep + "data", "tmp-work")):
            continue
        for f in files:
            if f.endswith(".md"):
                md.append(os.path.join(dirpath, f))
    return md


def classify_tools():
    stems = _tool_stems()
    code_paths = [p for _s, p in stems]
    code_text = _concat(code_paths)
    md_text = _concat(_all_md())
    rows = []
    for stem, path in stems:
        src = _read(path)
        others = code_text.replace(src, "", 1)  # исключить self из code-грепа
        importers = len(re.findall(r"(?:^|\n)\s*(?:from\s+%s\s+import|import\s+%s)\b" % (re.escape(stem), re.escape(stem)), others))
        callers = len(re.findall(r"%s\.py\b" % re.escape(stem), others))
        # doc_refs: ТОЛЬКО «stem.py» (не голое слово stem — иначе «metrics» в прозе = ложный refs)
        doc_refs = len(re.findall(r"%s\.py\b" % re.escape(stem), md_text))
        has_main = ("__main__" in src) or ("def main(" in src)
        if importers + callers > 0:
            status = "active"
        elif has_main and doc_refs > 0:
            status = "manual-cli"
        elif doc_refs > 0:
            status = "referenced-only"
        else:
            status = "dormant"
        rows.append({"name": stem + ".py", "status": status,
                     "importers": importers, "callers": callers, "doc_refs": doc_refs})
    return rows


def classify_decisions():
    code_text = _concat([p for _s, p in _tool_stems()])
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "decisions", "D-*.md"))):
        did = os.path.basename(path)[:-3]
        # ЧЕСТНО: static не отличает enforcement от цитаты в docstring → ярлык «code-linked» (упомянут
        # в неком не-test инструменте) vs «doc-only» (ни в одном .py). Прокси нижней границы; точное
        # «enforced» — судит FINDER (topics/adoption-statistics-2026-06-23.md, там 5/23).
        code_refs = len(re.findall(re.escape(did) + r"\b", code_text))
        rows.append({"name": did, "status": "code-linked" if code_refs > 0 else "doc-only",
                     "code_refs": code_refs})
    return rows


def classify_docs():
    md_paths = _all_md()
    big_text = _concat(md_paths) + _concat([p for _s, p in _tool_stems()])
    rows = []
    for path in md_paths:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        if not (rel.startswith("docs/") or rel.startswith("topics/")):
            continue
        fname = os.path.basename(path)
        slug = fname[:-3]
        self_src = _read(path)
        hay = big_text.replace(self_src, "", 1)
        # inbound: ТОЛЬКО полное имя файла (с .md) — slug-как-слово давал ложные cited
        inbound = len(re.findall(re.escape(fname), hay))
        _ = slug
        rows.append({"name": rel, "status": "cited" if inbound > 0 else "orphan", "inbound": inbound})
    return rows


def collect():
    tools = classify_tools()
    decisions = classify_decisions()
    docs = classify_docs()

    def pct(rows, good):
        n = len(rows)
        g = sum(1 for r in rows if r["status"] in good)
        return g, n, (round(100 * g / n) if n else 0)

    t_g, t_n, t_p = pct(tools, ("active", "manual-cli"))
    d_g, d_n, d_p = pct(decisions, ("code-linked",))
    o_g, o_n, o_p = pct(docs, ("cited",))
    return {
        "tools": tools, "decisions": decisions, "docs": docs,
        "summary": {
            "tools_applied": [t_g, t_n, t_p],
            "tools_dormant": sum(1 for r in tools if r["status"] == "dormant"),
            "decisions_enforced": [d_g, d_n, d_p],
            "docs_cited": [o_g, o_n, o_p],
            "docs_orphan": sum(1 for r in docs if r["status"] == "orphan"),
        },
    }


BASELINE = os.path.join(ROOT, "logs", "adoption-baseline.json")


def _flatten(summary):
    """Сводку → плоские числа для дельты."""
    return {
        "tools_applied_pct": summary["tools_applied"][2],
        "tools_dormant": summary["tools_dormant"],
        "decisions_pct": summary["decisions_enforced"][2],
        "docs_cited_pct": summary["docs_cited"][2],
        "docs_orphan": summary["docs_orphan"],
    }


def save_baseline():
    summary = collect()["summary"]
    os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
    with open(BASELINE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("baseline сохранён: logs/adoption-baseline.json")
    return 0


def cmd_delta(as_json=False):
    """RE-MEASURE (P15): дельта текущих метрик против baseline — сдвинулась ли игла применения."""
    if not os.path.exists(BASELINE):
        print("нет baseline — сначала `python tools/adoption.py --save-baseline`")
        return 2
    with open(BASELINE, encoding="utf-8") as f:
        old = _flatten(json.load(f))
    cur = _flatten(collect()["summary"])
    # знак «лучше»: pct/cited вверх — хорошо; dormant/orphan вниз — хорошо
    better_up = {"tools_applied_pct", "decisions_pct", "docs_cited_pct"}
    delta = {}
    for k in cur:
        d = cur[k] - old.get(k, cur[k])
        good = (d > 0) if k in better_up else (d < 0)
        delta[k] = {"old": old.get(k), "new": cur[k], "delta": d,
                    "dir": "↑" if d > 0 else ("↓" if d < 0 else "="),
                    "good": bool(d == 0 or good)}
    if as_json:
        print(json.dumps(delta, ensure_ascii=False, indent=2))
        return 0
    print("=== ADOPTION ДЕЛЬТА (vs baseline) ===")
    label = {"tools_applied_pct": "Инструменты применяются %", "tools_dormant": "dormant-инструменты",
             "decisions_pct": "Решения code-linked %", "docs_cited_pct": "Доки cited %",
             "docs_orphan": "orphan-доки"}
    for k, v in delta.items():
        mark = "" if v["delta"] == 0 else ("  ✓" if v["good"] else "  ⚠")
        print("  %-26s %s → %s  (%s%d)%s" % (label[k], v["old"], v["new"], v["dir"], v["delta"], mark))
    moved = sum(1 for v in delta.values() if v["delta"] != 0)
    print("\nИгла сдвинулась по %d метрикам%s" % (moved, "" if moved else " (нет изменений vs baseline)"))
    return 0


def cmd_report(as_json=False, list_kind=None):
    data = collect()
    if list_kind:
        key = {"dormant": ("tools", "dormant"), "declarative": ("decisions", "doc-only"),
               "orphan": ("docs", "orphan")}.get(list_kind)
        if not key:
            print("--list: dormant|declarative|orphan")
            return 2
        coll, st = key
        for r in data[coll]:
            if r["status"] == st:
                print(r["name"])
        return 0
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    s = data["summary"]
    print("=== ADOPTION (статическое применение накопленного) ===")
    print("  Инструменты применяются: %d/%d (%d%%)   dormant: %d" % (
        s["tools_applied"][0], s["tools_applied"][1], s["tools_applied"][2], s["tools_dormant"]))
    print("  Решения code-linked:     %d/%d (%d%%)   doc-only: %d  (прокси; точное enforced=5/23 у FINDER)" % (
        s["decisions_enforced"][0], s["decisions_enforced"][1], s["decisions_enforced"][2],
        s["decisions_enforced"][1] - s["decisions_enforced"][0]))
    print("  Доки cited:              %d/%d (%d%%)   orphan: %d" % (
        s["docs_cited"][0], s["docs_cited"][1], s["docs_cited"][2], s["docs_orphan"]))
    dormant = [r["name"] for r in data["tools"] if r["status"] == "dormant"]
    orphan = [r["name"] for r in data["docs"] if r["status"] == "orphan"]
    if dormant:
        print("\n  dormant-инструменты (0 вызывателей, 0 doc-ссылок):", ", ".join(dormant))
    if orphan:
        print("  orphan-доки (0 inbound):", ", ".join(orphan[:10]) + (" …" if len(orphan) > 10 else ""))
    return 0


def main(argv):
    args = list(argv)
    as_json = "--json" in args
    if "--save-baseline" in args:
        return save_baseline()
    if "--delta" in args:
        return cmd_delta(as_json=as_json)
    list_kind = None
    if "--list" in args:
        i = args.index("--list")
        if i + 1 < len(args):
            list_kind = args[i + 1]
    return cmd_report(as_json=as_json, list_kind=list_kind)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
