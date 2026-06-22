#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_consensus (Q-017, слияние документации агентов) — находит ОБЩИЕ пункты и РАЗНОГЛАСИЯ между доками.

Сканирует несколько markdown-документов (разных агентов/людей) по одной теме, выделяет «пункты»
(буллеты / заголовки / строки таблиц), кластеризует похожие по содержанию (Jaccard на токенах) и даёт:
- **Консенсус** — пункты, встречающиеся в >=2 документах, с cross-reference `file:line` где встречаются;
- **Разногласия** — пункты только из одного документа (сгруппированы по файлу).

Это автоматизация ручного синтеза (opinion-synthesis): консенсус → описание в mainline, разногласия →
детализировать/обосновать (модель D-017). READ-ONLY, чистая stdlib.

CLI:
    python tools/doc_consensus.py report --files a.md b.md [c.md ...] [--out reports/x.md] [--thr 0.4]
    python tools/doc_consensus.py report --topic <topic> [--out ...]   # доки темы через variants.py
"""
import os
import re
import sys
import json
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
# Шумовые слова (ru+en), чтобы Jaccard ловил суть, а не служебные.
STOP = set((
    "the a an and or of to in is are for with on at by as be it this that not from into "
    "и в на по для что как это не из то же был быть эти об от со про или нет так уже там где "
    "к у о а но если чтобы при над под между его её их мы вы они оно тот эта все весь"
).split())


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


# Лёгкий стемминг: чтобы «безопасность/безопасности», «коммит/коммиты» совпадали (cross-agent проза
# одни идеи пишет разными формами). Грубо, без морфологии — отсечь частые окончания.
_RU_SUF = sorted((
    "ость", "ения", "иями", "ями", "ами", "ого", "ому", "ыми", "ими", "ах", "ях", "ов", "ев",
    "ий", "ый", "ая", "ое", "ые", "ться", "ть", "ет", "ут", "ют", "ам", "ом", "ем", "ах", "и", "ы", "а", "у", "е",
), key=len, reverse=True)
_EN_SUF = ("ings", "ing", "ies", "ed", "es", "s")


def _stem(w):
    for suf in _RU_SUF:
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[:-len(suf)]
    for suf in _EN_SUF:
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[:-len(suf)]
    return w


def _norm_tokens(text):
    t = text.lower()
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[^0-9a-zа-яё_-]+", " ", t)
    return {_stem(w) for w in t.split() if len(w) > 2 and w not in STOP}


def units(path, root=ROOT):
    """Извлечь «пункты» дока: буллеты / заголовки ##-#### / строки таблиц (вне front-matter)."""
    rel = os.path.relpath(path, root).replace("\\", "/")
    out = []
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return out
    in_fm = False
    in_code = False
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if i == 1 and s == "---":
            in_fm = True
            continue
        if in_fm:
            if s == "---":
                in_fm = False
            continue
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = (re.match(r"^[-*+]\s+(.*)", s) or re.match(r"^#{2,4}\s+(.*)", s)
             or re.match(r"^\|\s*(.+?)\s*\|", s))
        if not m:
            continue
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        if len(text) < 8 or set(text) <= set("-|: "):
            continue
        toks = _norm_tokens(text)
        if len(toks) >= 2:
            out.append({"text": text[:160], "tokens": toks, "where": "%s:%d" % (rel, i), "doc": rel})
    return out


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def analyze(paths, root=ROOT, thr=0.4):
    """Кластеризовать пункты; вернуть {consensus, divergent, docs}."""
    all_units = []
    for p in paths:
        all_units.extend(units(p, root))
    clusters = []  # {rep: tokens(первого), members: [unit], docs: set}
    for u in all_units:
        best, best_sim = None, thr
        for c in clusters:
            sim = _jaccard(u["tokens"], c["rep"])
            if sim >= best_sim:
                best, best_sim = c, sim
        if best is not None:
            best["members"].append(u)
            best["docs"].add(u["doc"])
        else:
            clusters.append({"rep": u["tokens"], "members": [u], "docs": {u["doc"]}})
    consensus = sorted((c for c in clusters if len(c["docs"]) >= 2),
                       key=lambda c: -len(c["docs"]))
    divergent = [c for c in clusters if len(c["docs"]) == 1]
    docs = sorted({u["doc"] for u in all_units})
    return {"consensus": consensus, "divergent": divergent, "docs": docs, "n_units": len(all_units)}


def render(res):
    L = []
    L.append("# Doc-consensus отчёт")
    L.append("")
    L.append("Документы (%d): %s" % (len(res["docs"]), ", ".join("`%s`" % d for d in res["docs"])))
    L.append("Пунктов всего: %d · консенсус-кластеров: %d · одиночных: %d"
             % (res["n_units"], len(res["consensus"]), len(res["divergent"])))
    L.append("")
    L.append("## Консенсус (пункты в >=2 документах) — кандидаты в mainline-описание")
    L.append("")
    if not res["consensus"]:
        L.append("_(общих пунктов не найдено при текущем пороге)_")
    for c in res["consensus"]:
        rep = max(c["members"], key=lambda u: len(u["tokens"]))
        L.append("- **%s**" % rep["text"])
        L.append("  - встречается в %d док.: %s" % (len(c["docs"]),
                 ", ".join("`%s`" % w for w in sorted(u["where"] for u in c["members"]))))
    L.append("")
    L.append("## Разногласия (пункт только в одном документе) — детализировать/обосновать (D-017)")
    L.append("")
    by_doc = {}
    for c in res["divergent"]:
        u = c["members"][0]
        by_doc.setdefault(u["doc"], []).append(u)
    for doc in sorted(by_doc):
        L.append("### `%s` — уникальные пункты (%d)" % (doc, len(by_doc[doc])))
        for u in by_doc[doc][:30]:
            L.append("- %s  _(%s)_" % (u["text"], u["where"]))
        if len(by_doc[doc]) > 30:
            L.append("- … ещё %d" % (len(by_doc[doc]) - 30))
        L.append("")
    return "\n".join(L)


def _topic_files(topic):
    p = subprocess.run([sys.executable, os.path.join(TOOLS, "variants.py"), "index"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", stdin=subprocess.DEVNULL)
    try:
        idx = json.loads(p.stdout or "{}")
    except ValueError:
        return []
    return [v["file"] for v in idx.get(topic, []) if v.get("file", "").endswith(".md")]


def _arg(a, flag, default=None):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default


def main():
    a = sys.argv[1:]
    if not a or a[0] != "report":
        print(__doc__)
        return 2
    thr = float(_arg(a, "--thr", "0.4"))
    out_path = _arg(a, "--out")
    files = []
    if "--files" in a:
        i = a.index("--files") + 1
        while i < len(a) and not a[i].startswith("--"):
            files.append(a[i])
            i += 1
    elif "--topic" in a:
        files = _topic_files(_arg(a, "--topic"))
    if len(files) < 2:
        print("Нужно >=2 документа (--files a.md b.md или --topic <topic> с >=2 вариантами).")
        return 2
    res = analyze([os.path.join(ROOT, f) if not os.path.isabs(f) else f for f in files], thr=thr)
    text = render(res)
    if out_path:
        dest = out_path if os.path.isabs(out_path) else os.path.join(ROOT, out_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        print("Записано: %s" % os.path.relpath(dest, ROOT))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
