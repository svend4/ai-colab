"""Тест red_team_gate.py — выходной гейт (survived→канон / refuted→negative-set / open→pending)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import red_team_gate as rg

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DOC = """# Red-team записи темы X

## Независимость взвешивает совпадение, не число
- attack: а если все клоны сговорились?
- verdict: survived
- reason: атака не прошла — клоны схлопываются мерой независимости

## Минор всегда сохраняется без исключений
- attack: контрпример — спам-claim кратности 1 засоряет резерв
- verdict: refuted
- severity: high,medium
- reason: нужен порог осмысленности перед сохранением; абсолютная формулировка опровергнута

## Канонизация всегда детерминирована
- attack: границы кластеров дрейфуют между прогонами
- verdict: open

## Слепота достаточна для независимости
- attack: один опровергатель нашёл дыру (клоны в карантине)
- verdict: refuted
- severity: high
- reason: один tombstone — независимо не подтверждено
"""


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.md")
        open(p, "w", encoding="utf-8", newline="\n").write(DOC)

        recs = rg.parse_records(p)
        if len(recs) != 4:
            fails.append("ожидалось 4 записи, получено %d" % len(recs))

        g = rg.gate(recs)
        if len(g["cleared"]) != 1 or "Независимость" not in g["cleared"][0]["claim"]:
            fails.append("cleared должен содержать survived-claim: %s" % g["cleared"])
        # refuted с >=2 опровергателями (high,medium) → rejected (negative-set)
        if len(g["rejected"]) != 1 or "Минор" not in g["rejected"][0]["claim"]:
            fails.append("rejected должен содержать 2-опровергательский refuted: %s" % g["rejected"])
        elif not g["rejected"][0]["reason"]:
            fails.append("refuted обязан нести reason (антиген, RT-2): %s" % g["rejected"][0])
        # СИММЕТРИЯ ADD↔REMOVE: refuted с 1 опровергателем → contested, НЕ убит
        if len(g["contested"]) != 1 or "Слепота" not in g["contested"][0]["claim"]:
            fails.append("1-опровергательский refuted должен быть contested (симметрия), а не rejected: %s" % g["contested"])
        if any("Слепота" in r["claim"] for r in g["rejected"]):
            fails.append("одиночный tombstone НЕ должен убивать claim (no-silent-delete фикс)")
        if len(g["pending"]) != 1:
            fails.append("pending должен содержать 1 open")

        # promotable: claim, совпадающий с survived-записью → можно; чужой → нет
        pr = rg.promotable(
            ["Независимость взвешивает совпадение источников, не число",
             "земля плоская и зелёная"], recs)
        prmap = {x["claim"]: x["promotable"] for x in pr}
        if not prmap["Независимость взвешивает совпадение источников, не число"]:
            fails.append("claim, совпавший с survived, должен быть promotable")
        if prmap["земля плоская и зелёная"]:
            fails.append("несвязанный claim НЕ должен быть promotable без записи survived (RT-1)")

    if fails:
        print("FAIL test_red_team_gate:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_red_team_gate: survived→cleared · refuted→reason(антиген) · open→pending · promotable(RT-1)")


if __name__ == "__main__":
    main()
