# ==========================================
# [FILE ID CARD]
# ID: tools.oracle_quorum
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: кворум независимых судей вместо ОДНОГО (смягчение проблемы оракула, OQ-1/OQ-2).
# ==========================================
"""oracle_quorum.py — кворум независимых судей вместо ОДНОГО (смягчение проблемы оракула, OQ-1/OQ-2).

Self-repair (kotel §10) вскрыл корень 7 still-refuted: семантический вердикт исходит от ОДНОГО LLM →
judge-capture. Оракула не устранить, но: (1) поднять цену захвата 1→кворум независимых судей (разные
model/lens); (2) сделать захват ВИДИМЫМ — рассогласие судей → contested, не молчаливое решение. Это та
же защита, что метод даёт СВИДЕТЕЛЯМ (симметрия судья↔свидетель), но на УРОВНЕ КОДА, не прозы.

Формат quorum/<тема>.md: `## <claim>` + строки `- judge: model/lens | verdict: V | reason: R`.

CLI:
  python tools/oracle_quorum.py quorum/<тема>.md   # кворум-вердикт + рассогласие + независимость судей
  python tools/oracle_quorum.py --board
  python tools/oracle_quorum.py --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import glob
from collections import Counter

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
MIN_AGREE = 2  # decisive только если >=2 судьи согласны И строгое большинство


def parse_judges(path):
    """claim → список суждений {judge:(model,lens), verdict, reason}. Формат `## claim` + `- judge: ...`."""
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return []
    out = []
    cur = None
    for ln in lines:
        h = re.match(r"^##\s+(.*)", ln)
        if h:
            cur = {"claim": h.group(1).strip(), "judges": []}
            out.append(cur)
            continue
        if cur:
            m = re.match(r"^\s*-\s*judge\s*:\s*(.*)", ln, re.I)
            if m:
                cur["judges"].append(_parse_judge(m.group(1)))
    return out


def quorum(verdicts, min_agree=MIN_AGREE):
    """Кворум-вердикт: decisive только при >=min_agree согласных И строгом большинстве; иначе contested."""
    c = Counter(v for v in verdicts if v)
    n = len([v for v in verdicts if v])
    if not n:
        return {"verdict": "contested", "decisive": False, "agreement": 0.0, "breakdown": {}, "n_judges": 0}
    top, topn = c.most_common(1)[0]
    decisive = topn >= min_agree and topn * 2 > n
    return {
        "verdict": top if decisive else "contested",
        "decisive": decisive, "agreement": round(topn / n, 2),
        "breakdown": dict(c), "n_judges": n,
    }


def judge_independence(judges):
    """Насколько судьи НЕЗАВИСИМЫ: распознать гомогенность (рекурсия проблемы — честно флажим)."""
    models = {j["model"] for j in judges if j["model"] != "?"}
    lenses = {j["lens"] for j in judges if j["lens"] != "?"}
    flags = []
    if len(judges) < MIN_AGREE + 1:
        flags.append("мало судей (<%d) — кворум хрупок" % (MIN_AGREE + 1))
    if len(models) <= 1:
        flags.append("⚠ все судьи ОДНОЙ модели — кворум НЕ независим (та же проблема оракула, рекурсия)")
    return {"models": sorted(models), "lenses": sorted(lenses), "flags": flags}


def _parse_judge(s):
    parts = [p.strip() for p in s.split("|")]
    j = {"model": "?", "lens": "?", "verdict": "", "reason": ""}
    head = parts[0] if parts else ""
    if "/" in head:
        m, _, l = head.partition("/")
        j["model"], j["lens"] = m.strip(), l.strip()
    else:
        j["lens"] = head
    for p in parts[1:]:
        k, _, v = p.partition(":")
        k = k.strip().lower()
        if k in ("verdict", "reason"):
            j[k] = v.strip()
    return j


def _assess(rec):
    verds = [j["verdict"] for j in rec["judges"]]
    q = quorum(verds)
    ind = judge_independence(rec["judges"])
    return {"claim": rec["claim"], "quorum": q, "independence": ind}


def _report(recs, title):
    print("=== ОРАКУЛ-КВОРУМ (N судей, не 1): %s ===" % title)
    for rec in recs:
        a = _assess(rec)
        q = a["quorum"]
        mark = "◐ CONTESTED (рассогласие → захват/неоднозначность ВИДИМЫ)" if not q["decisive"] else (
            "✅ %s" % q["verdict"])
        print("  %s  [%d судей, согласие %.0f%%, %s]" % (
            mark, q["n_judges"], q["agreement"] * 100, q["breakdown"]))
        print("     claim: %s" % rec["claim"][:80])
        for fl in a["independence"]["flags"]:
            print("     %s" % fl)


def main(argv):
    help_guard(__doc__, argv)
    import json
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    if "--board" in argv or not args:
        files = sorted(glob.glob(os.path.join(ROOT, "quorum", "*.md")))
        if as_json:
            print(json.dumps([{"file": os.path.relpath(f, ROOT).replace("\\", "/"),
                               "claims": [_assess(r) for r in parse_judges(f)]} for f in files],
                             ensure_ascii=False, indent=2)); return 0
        if not files:
            print("oracle_quorum: нет quorum/*.md (мульти-судейских прогонов ещё не было)"); return 0
        for f in files:
            _report(parse_judges(f), os.path.basename(f)); print()
        return 0
    p = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    recs = parse_judges(p)
    if as_json:
        print(json.dumps([_assess(r) for r in recs], ensure_ascii=False, indent=2)); return 0
    if not recs:
        print("oracle_quorum: claim не найдено в %s" % p); return 2
    _report(recs, os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
