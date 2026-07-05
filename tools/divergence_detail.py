# ==========================================
# [FILE ID CARD]
# ID: tools.divergence_detail
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: «детализация ПЕРЕД консенсусом» как тула (P-3, инвариант 4/5 линз).
# ==========================================
"""divergence_detail.py — «детализация ПЕРЕД консенсусом» как тула (P-3, инвариант 4/5 линз).

Сошедшийся инвариант: расхождение НЕЛЬЗЯ сводить к консенсусу, пока не проверено «разные условия —
оба правы?». Тула даёт 4-фасетный скаффолд (`facets`) на пару расходящихся claim и ГЕЙТ (`gate`):
конфликт не идёт на разрешение без записи-детализации. Мнимый конфликт (разные условия) → оба claim
в котёл как scoped-ветви (не теряем правых); подлинный → на разрешение (red_team_gate). Заполнение
фасетов — агент (подключаемо), скаффолд+гейт ДЕТЕРМИНИРОВАНЫ.

Формат divergence/<тема>.md: `## <claim A> -vs- <claim B>` + буллеты `- условия:`/`- evidence:`/
`- риск:`/`- охват:` + `- verdict: мнимый|подлинный|open`.

CLI:
  python tools/divergence_detail.py --pair "claim A" "claim B"   # печать 4-фасетного скаффолда
  python tools/divergence_detail.py divergence/<тема>.md         # маршрут записей
  python tools/divergence_detail.py --board
  python tools/divergence_detail.py --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
VERDICTS = ("мнимый", "подлинный", "open")


def facets(a, b):
    """4 подвопроса детализации на пару расходящихся claim (детерминированный скаффолд)."""
    return [
        "условия: при каких входах/условиях верен «%s», при каких «%s»? разные ниши → оба правы?" % (a[:40], b[:40]),
        "evidence: на каких данных/доказательствах стоит каждый? сравнимы ли они вообще?",
        "риск: какую толерантность к риску принимает каждый? расхождение из-за разного риск-аппетита?",
        "охват: claim про ОДНО и то же или про разный охват/уровень/область применения?",
    ]


def parse_records(path):
    """Записи детализации: на каждый `## A -vs- B` — 4 фасета + verdict."""
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return []
    recs = []
    cur = None
    for ln in lines:
        h = re.match(r"^##\s+(.*)", ln)
        if h:
            title = h.group(1).strip()
            a, _, b = title.partition(" -vs- ")
            cur = {"a": a.strip(), "b": b.strip(), "verdict": "open",
                   "условия": "", "evidence": "", "риск": "", "охват": ""}
            recs.append(cur)
            continue
        if cur:
            m = re.match(r"^\s*-\s*(условия|evidence|риск|охват|verdict)\s*:\s*(.*)", ln, re.I)
            if m:
                key, val = m.group(1).lower(), m.group(2).strip()
                if key == "verdict":
                    v = val.lower().split()[0] if val else "open"
                    cur["verdict"] = v if v in VERDICTS else "open"
                else:
                    cur[key] = val
    return recs


def gate(records):
    """Маршрут: resolved(verdict задан) · pending(open/нет). Мнимый → scoped оба; подлинный → разрешение."""
    return {
        "scoped": [r for r in records if r["verdict"] == "мнимый"],     # оба claim в котёл как ветви
        "to_resolve": [r for r in records if r["verdict"] == "подлинный"],  # → red_team_gate / decision
        "pending": [r for r in records if r["verdict"] == "open"],      # detail не завершён → не разрешать
    }


def _filled(rec):
    return sum(1 for f in ("условия", "evidence", "риск", "охват") if rec[f])


def _report(g, title):
    print("=== ДЕТАЛИЗАЦИЯ РАСХОЖДЕНИЙ (перед консенсусом): %s ===" % title)
    print("  мнимый→scoped: %d · подлинный→разрешение: %d · pending(detail не завершён): %d" % (
        len(g["scoped"]), len(g["to_resolve"]), len(g["pending"])))
    for r in g["scoped"]:
        print("  ◑ МНИМЫЙ (оба правы, scoped): %s -vs- %s" % (r["a"][:40], r["b"][:40]))
        if r["условия"]:
            print("       условия: %s" % r["условия"][:90])
    for r in g["to_resolve"]:
        print("  ⚔ ПОДЛИННЫЙ → на разрешение: %s -vs- %s" % (r["a"][:40], r["b"][:40]))
    for r in g["pending"]:
        print("  ⏳ PENDING (%d/4 фасета) — не разрешать без детализации (DD-1): %s -vs- %s" % (
            _filled(r), r["a"][:35], r["b"][:35]))


def main(argv):
    help_guard(__doc__, argv)
    import json
    as_json = "--json" in argv
    if "--pair" in argv:
        i = argv.index("--pair")
        rest = [a for a in argv[i + 1:] if not a.startswith("--")]
        if len(rest) >= 2:
            print("=== 4-ФАСЕТНЫЙ СКАФФОЛД ДЕТАЛИЗАЦИИ ===")
            for q in facets(rest[0], rest[1]):
                print("  - " + q)
            print("  - verdict: мнимый | подлинный | open")
            return 0
        print("divergence_detail: --pair требует 2 claim"); return 2
    args = [a for a in argv if not a.startswith("--")]
    if "--board" in argv or not args:
        files = sorted(glob.glob(os.path.join(ROOT, "divergence", "*.md")))
        results = []
        for fp in files:
            g = gate(parse_records(fp))
            g["file"] = os.path.relpath(fp, ROOT).replace("\\", "/")
            results.append(g)
        if as_json:
            print(json.dumps(results, ensure_ascii=False, indent=2)); return 0
        if not results:
            print("divergence_detail: нет divergence/*.md (расхождений ещё не детализировали)"); return 0
        for g in results:
            _report(g, os.path.basename(g["file"]))
            print()
        return 0
    p = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    recs = parse_records(p)
    g = gate(recs)
    if as_json:
        print(json.dumps(g, ensure_ascii=False, indent=2)); return 0
    if not recs:
        print("divergence_detail: записей не найдено в %s" % p); return 2
    _report(g, os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
