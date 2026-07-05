# ==========================================
# [FILE ID CARD]
# ID: tools.independence_measure
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: несущая стена №2: измерить независимость вариантов, а не объявить.
# ==========================================
"""independence_measure.py — несущая стена №2: измерить независимость вариантов, а не объявить.

Котёл-сверка (kotel/independent-first-reconcile-2026-06-25) показала: «по смыслу, не количеству»
реально лишь настолько, насколько мы ИЗМЕРЯЕМ независимость. seal_hash (ripeness_gate) доказывает
ПОРЯДОК (писал до чтения), но не то, что два варианта — не клоны одной модели/линзы.

Эта тула считает ЭФФЕКТИВНОЕ ЧИСЛО СВИДЕТЕЛЕЙ (как effective sample size): 5 вариантов, но если 3 —
почти-клоны (тот же генотип + похожий текст), эффективно ~3. «N клонов = 1 свидетель». Сила совпадения
= число РАЗНЫХ кластеров-свидетелей, НЕ сырой count. Детерминированно, без LLM (работает на генотипе
из front-matter + поверхностной дивергенции тел). Это машинная форма правила «вес = разнообразие, не число».

CLI:
  python tools/independence_measure.py <topic-dir>   # эфф. свидетели по вариантам темы
  python tools/independence_measure.py --board       # по всем variants/<topic>/
  python tools/independence_measure.py --json [--thr 0.5]
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
DEFAULT_THR = 0.5
_STOP = set("the a an and or of to in is are for with на по для что как это не из то же или и в".split())


def genotype(fm):
    """Генотип-вектор варианта из front-matter: (model, lens|author). '?' = отсутствует (не клон)."""
    model = (fm.get("model") or "?").strip()
    lens = (fm.get("lens") or fm.get("author") or "?").strip()
    return (model, lens)


def surface_div(a_tokens, b_tokens):
    """1 − Jaccard: ВЫСОКАЯ = тексты разные (хорошо для независимости); 0 = идентичны."""
    if not a_tokens or not b_tokens:
        return 1.0
    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return 1.0 - (inter / union if union else 0.0)


def effective_witnesses(variants, thr=DEFAULT_THR):
    """Число кластеров-свидетелей: почти-клоны схлопываются в один. <= сырого числа вариантов."""
    return len(_cluster(variants, thr))


def analyze(paths, thr=DEFAULT_THR):
    """Сводка по набору вариантов: сырое vs эффективное число, кластеры-клоны, флаги генотипа."""
    vs = [v for v in (_load(p) for p in paths) if v]
    if not vs:
        return None
    clusters = _cluster(vs, thr)
    models = {v["geno"][0] for v in vs if v["geno"][0] != "?"}
    lenses = {v["geno"][1] for v in vs if v["geno"][1] != "?"}
    clone_groups = [[vs[i]["name"] for i in g] for g in clusters if len(g) > 1]
    return {
        "n_raw": len(vs), "n_effective": len(clusters),
        "models": sorted(models), "lenses": sorted(lenses),
        "clone_groups": clone_groups,
        "flags": _flags(vs, models, len(clusters)),
    }


def _load(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    fm = _front_matter(text)
    return {
        "name": os.path.basename(path), "file": os.path.relpath(path, ROOT).replace("\\", "/"),
        "geno": genotype(fm), "tokens": _tokens(_body(text)), "sealed": "sealed" in fm,
    }


def _tokens(body):
    out = set()
    cur = []
    for ch in body.lower():
        if ch.isalnum() or ch in "_-":
            cur.append(ch)
        else:
            if len(cur) > 2:
                w = "".join(cur)
                if w not in _STOP:
                    out.add(w)
            cur = []
    return out


COPY_THR = 0.85  # near-identical поверхность = копирование (не convergence-on-truth)


def _pair_sim(a, b):
    """Клон-похожесть (1 = клоны). Клон = ТОТ ЖЕ генотип (model AND lens) ИЛИ near-copy поверхности.

    Red-team-находка (independence-weight): разный генотип + умеренно-высокий overlap — это вероятно
    convergence-on-TRUTH (два верных лаконичных ответа пишутся похоже), а НЕ клоны. Старая формула
    0.5*геноип+0.5*surf схлопывала таких в 1 свидетеля. Теперь поверхность сливает, только если
    near-verbatim (>=COPY_THR = копирование); иначе при разном генотипе — НЕ клон.
    """
    ma, la = a["geno"]; mb, lb = b["geno"]
    same_geno = (ma != "?" and ma == mb) and (la != "?" and la == lb)
    surf_overlap = 1.0 - surface_div(a["tokens"], b["tokens"])
    # Две ОРТОГОНАЛЬНЫЕ оси (урок атаки blindness, kotel §10): генотип-декорреляция И seal-провенанс.
    if same_geno:
        return 1.0                      # тот же генотип = клоны (эхо весов), seal НЕ спасает
    # разный генотип: seal-провенанс перебивает поверхность (фикс терсной-истины, остаток independence-weight)
    if a.get("sealed") and b.get("sealed"):
        return 0.0                      # оба писали ВСЛЕПУЮ → не копия даже при surf=1.0 (провенанс, не суждение)
    if surf_overlap >= COPY_THR:
        return 1.0                      # near-verbatim БЕЗ blind-провенанса = вероятно копия
    return surf_overlap * 0.5           # разный генотип, не копия → convergence, не дотягивает до слияния


def _cluster(vs, thr):
    n = len(vs)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if _pair_sim(vs[i], vs[j]) >= thr:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def _front_matter(text):
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end < 0:
        return fm
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def _body(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            nl = text.find("\n", end + 1)
            return text[nl + 1:] if nl >= 0 else ""
    return text


def _flags(vs, models, n_eff):
    f = []
    if len(models) <= 1:
        f.append("⚠ все варианты одной модели — независимость ЧАСТИЧНА (генотип-гомогенность)")
    if any(v["geno"] == ("?", "?") for v in vs):
        f.append("часть вариантов без генотип-метаданных (model/lens) — мера деградирует к поверхностной")
    if n_eff < len(vs):
        f.append("эффективных свидетелей МЕНЬШЕ числа вариантов (есть клоны)")
    return f


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
        rows = []
        for t in topics:
            r = analyze(sorted(glob.glob(os.path.join(t, "*.md"))), thr)
            if r:
                r["topic"] = os.path.basename(t)
                rows.append(r)
        if as_json:
            print(json.dumps(rows, ensure_ascii=False, indent=2)); return 0
        print("=== ЭФФЕКТИВНОЕ ЧИСЛО СВИДЕТЕЛЕЙ (несущая стена №2), thr=%.2f ===" % thr)
        for r in rows:
            print("  %-42s свидетелей %d из %d вариантов · моделей %d · линз %d" % (
                r["topic"][:42], r["n_effective"], r["n_raw"], len(r["models"]), len(r["lenses"])))
            for cg in r["clone_groups"]:
                print("      клоны→1: %s" % ", ".join(cg))
            for fl in r["flags"]:
                print("      %s" % fl)
        return 0
    d = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    r = analyze(sorted(glob.glob(os.path.join(d, "*.md"))), thr)
    if r is None:
        print("independence_measure: нет вариантов в %s" % d); return 2
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
    print("=== %s ===" % os.path.basename(d.rstrip("/\\")))
    print("  эффективных свидетелей: %d из %d вариантов" % (r["n_effective"], r["n_raw"]))
    print("  модели: %s · линзы: %s" % (", ".join(r["models"]) or "—", ", ".join(r["lenses"]) or "—"))
    for cg in r["clone_groups"]:
        print("  клоны→1 свидетель: %s" % ", ".join(cg))
    for fl in r["flags"]:
        print("  %s" % fl)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
