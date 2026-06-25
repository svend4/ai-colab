"""portals.py — средний слой охвата (И-8, золотая середина): варианты → кластеры/порталы по ТЕМЕ.

Триада охвата требует среднего слоя: не прыгать «агент → сразу глобал», а сводить родственные варианты
в ПОРТАЛ сначала. Тула строит граф похожести вариантов ПО СОДЕРЖАНИЮ (Jaccard токенов тела — тематическая
ось, ОТЛИЧНАЯ от клон-оси independence_measure: генотип+поверхность) и режет на связные компоненты =
порталы. Как ньюс-группы: варианты сами оседают по темам. Публичные: content_sim, portals, analyze.

CLI:
  python tools/portals.py --board            # порталы по всем variants/*/*.md
  python tools/portals.py --thr 0.25 --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
DEFAULT_THR = 0.12  # фазовый переход узкий (0.10→1 портал, 0.15→много); порог чувствителен (откр. вопрос №1)
_STOP = set("the a an and or of to in is are на по для что как это не из то же или и в с не до от".split())


def content_sim(a_tokens, b_tokens):
    """Тематическая близость = Jaccard токенов тела (содержание), не генотип."""
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def portals(paths, thr=DEFAULT_THR):
    """Связные компоненты графа content-похожести = порталы (средняя единица сверки)."""
    vs = [v for v in (_load(p) for p in paths) if v]
    comps = _components(vs, thr)
    return [[vs[i] for i in c] for c in comps]


def analyze(paths, thr=DEFAULT_THR):
    """Сводка: сколько порталов из скольких вариантов, состав и охваченные темы."""
    pts = portals(paths, thr)
    if not pts:
        return None
    return {
        "n_variants": sum(len(p) for p in pts), "n_portals": len(pts),
        "portals": sorted(([{
            "size": len(p), "members": [v["name"] for v in p],
            "topics": sorted({v["topic"] for v in p}),
        } for p in pts]), key=lambda x: -x["size"]),
    }


def _load(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    return {"name": os.path.basename(path), "topic": os.path.basename(os.path.dirname(path)),
            "tokens": _tokens(text)}


def _tokens(body):
    out = set()
    cur = []
    for ch in body.lower():
        if ch.isalnum() or ch in "_-":
            cur.append(ch)
        else:
            if len(cur) > 3:
                w = "".join(cur)
                if w not in _STOP:
                    out.add(w)
            cur = []
    return out


def _components(vs, thr):
    n = len(vs)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if content_sim(vs[i]["tokens"], vs[j]["tokens"]) >= thr:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


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
    paths = sorted(glob.glob(os.path.join(ROOT, "variants", "*", "*.md")))
    r = analyze(paths, thr)
    if r is None:
        print("portals: нет вариантов в variants/*/"); return 0
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
    print("=== ПОРТАЛЫ (средний слой охвата, И-8), thr=%.2f ===" % thr)
    print("  вариантов: %d · порталов: %d (родственное сводится локально ДО глобала)" % (
        r["n_variants"], r["n_portals"]))
    for i, p in enumerate(r["portals"], 1):
        print("  • портал %d (%d): %s" % (i, p["size"], ", ".join(p["members"])))
        if len(p["topics"]) > 1:
            print("      связал темы: %s" % ", ".join(p["topics"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
