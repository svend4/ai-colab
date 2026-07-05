# ==========================================
# [FILE ID CARD]
# ID: tools.consensus_by_meaning
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: консенсус ВЗВЕШЕН ПО СВИДЕТЕЛЯМ, не по счёту (замена doc_consensus-счётчика).
# ==========================================
"""consensus_by_meaning.py — консенсус ВЗВЕШЕН ПО СВИДЕТЕЛЯМ, не по счёту (замена doc_consensus-счётчика).

doc_consensus.py: консенсус = claim в >=2 ДОКУМЕНТАХ (счёт). Котёл-сверка потребовала отбор ПО СМЫСЛУ.
Здесь публичные `claims` (атомарные утверждения варианта) и `consensus` (3-слотный выход) считают силу
claim как ЭФФЕКТИВНОЕ ЧИСЛО СВИДЕТЕЛЕЙ (через independence_measure), а НЕ число вхождений:
  claim в 3 КЛОН-вариантах = 1 свидетель → минор;  claim в 2 НЕЗАВИСИМЫХ = 2 свидетеля → ядро.
Денежный кадр в выводе: «вхождений 3, но свидетель 1». Канонизация claim сейчас лексическая
(подключаема — настоящая смысловая = несущая стена №1, LLM). Детерминированно поверх independence_measure.

CLI:
  python tools/consensus_by_meaning.py <topic-dir>   # 3-слотный консенсус по вариантам темы
  python tools/consensus_by_meaning.py --board       # по всем variants/<topic>/
  python tools/consensus_by_meaning.py --json [--thr 0.4]
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import glob
import independence_measure as im

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
DEFAULT_THR = 0.4


def claims(path):
    """Атомарные claim варианта (буллеты / заголовки / строки таблиц) с токенами и тегом источника."""
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return []
    out = []
    in_fm = in_code = False
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if i == 1 and s == "---":
            in_fm = True; continue
        if in_fm:
            if s == "---":
                in_fm = False
            continue
        if s.startswith("```"):
            in_code = not in_code; continue
        if in_code or not s:
            continue
        m = (re.match(r"^[-*+]\s+(.*)", s) or re.match(r"^#{1,4}\s+(.*)", s)
             or re.match(r"^\|\s*(.+?)\s*\|", s))
        if m:
            txt = re.sub(r"\s+", " ", m.group(1)).strip()
            toks = im._tokens(txt)
            if len(toks) >= 2:
                out.append({"text": txt[:150], "toks": toks, "var": path})
    return out


def consensus(paths, thr=DEFAULT_THR):
    """3-слотный консенсус: ядро(свидетелей>=2) · минор(1, сохранён) · scope(нужна стена №1)."""
    items = []
    for p in paths:
        items.extend(claims(p))
    if not items:
        return None
    clusters = _cluster_claims(items, thr)
    cache = {p: im._load(p) for p in paths}
    rows = []
    for cl in clusters:
        support = sorted({items[i]["var"] for i in cl})
        wit = im.effective_witnesses([cache[p] for p in support if cache[p]])
        rows.append({"text": items[cl[0]]["text"], "occurrences": len(cl),
                     "support": [os.path.basename(p) for p in support], "witnesses": wit})
    rows.sort(key=lambda r: (-r["witnesses"], -r["occurrences"]))
    return {
        "n_variants": len(paths), "n_claims": len(items), "n_clusters": len(clusters),
        "core": [r for r in rows if r["witnesses"] >= 2],
        "minor": [r for r in rows if r["witnesses"] <= 1],
    }


def _sim(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cluster_claims(items, thr):
    """Союз claim ПО РАЗНЫМ вариантам, близких по смыслу (лексически). Внутри варианта не сливаем."""
    n = len(items)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if items[i]["var"] != items[j]["var"] and _sim(items[i]["toks"], items[j]["toks"]) >= thr:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def _print_report(r, title):
    print("=== КОНСЕНСУС ПО СМЫСЛУ (вес = свидетели, не count): %s ===" % title)
    print("  вариантов %d · claim %d · кластеров %d" % (r["n_variants"], r["n_claims"], r["n_clusters"]))
    print("  --- ЯДРО (>=2 НЕЗАВИСИМЫХ свидетеля) ---")
    for c in r["core"][:20]:
        print("    [св %d / вхожд %d] %s  ⟵ %s" % (
            c["witnesses"], c["occurrences"], c["text"], ", ".join(c["support"])))
    if not r["core"]:
        print("    (нет: независимой конвергенции не обнаружено)")
    print("  --- МИНОР (1 свидетель — СОХРАНЁН, не отброшен) ---")
    for c in r["minor"][:20]:
        tail = "  ← клоны: %d вхождений = 1 свидетель" % c["occurrences"] if c["occurrences"] > 1 else ""
        print("    [св %d / вхожд %d] %s%s" % (c["witnesses"], c["occurrences"], c["text"], tail))
    print("  --- SCOPE-ВЕТВИ (противоречия) ---")
    print("    (детект противоречий требует смысловой канонизации — несущая стена №1, LLM)")


def main(argv):
    help_guard(__doc__, argv)
    import json
    as_json = "--json" in argv
    thr = DEFAULT_THR
    if "--thr" in argv:
        try:
            thr = float(argv[argv.index("--thr") + 1])
        except (ValueError, IndexError):
            pass
    args = [a for a in argv if not a.startswith("--")]
    if "--board" in argv or not args:
        topics = sorted({os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "variants", "*", "*.md"))})
        results = []
        for t in topics:
            r = consensus(sorted(glob.glob(os.path.join(t, "*.md"))), thr)
            if r:
                r["topic"] = os.path.basename(t)
                results.append(r)
        if as_json:
            print(json.dumps(results, ensure_ascii=False, indent=2)); return 0
        for r in results:
            _print_report(r, r["topic"])
            print()
        return 0
    d = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    r = consensus(sorted(glob.glob(os.path.join(d, "*.md"))), thr)
    if r is None:
        print("consensus_by_meaning: нет вариантов в %s" % d); return 2
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
    _print_report(r, os.path.basename(d.rstrip("/\\")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
