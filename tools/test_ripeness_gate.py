"""Тест ripeness_gate.py — гейт зрелости(И-2) + печати(И-1) вариантов."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ripeness_gate as rg

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

RIPE = """---
id: x
status: ready-for-synthesis
sealed: blind
---
# Условия применимости
Применять к содержательным вопросам.
# Полный ответ / дизайн
Механизм и фазы.
# Уникальный вклад
Структурная слепота.
# Риски
Дублирование усилий.
# Открытые вопросы
Кто ратифицирует?
# Evidence
Анкоринг реален.
"""

THIN = """---
id: y
status: draft
---
# Идея
Что-то про варианты, без полей.
"""

RIPE_UNSEALED = """---
id: z
status: ready-for-synthesis
---
# Условия
applies to questions
# Дизайн
механизм
# Уникальное
unique вклад
# Риски
risk
# Вопросы
question?
"""


def _w(d, name, txt):
    p = os.path.join(d, name)
    open(p, "w", encoding="utf-8", newline="\n").write(txt)
    return p


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        ripe = _w(d, "ripe.md", RIPE)
        thin = _w(d, "thin.md", THIN)
        unsealed = _w(d, "unsealed.md", RIPE_UNSEALED)

        r = rg.ripeness(ripe)
        if not r["ripe"] or not r["sealed"] or len(r["present"]) != 5 or not r["has_evidence"]:
            fails.append("ripe: должен быть зрел+запечатан 5/5+evidence: %s" % r)
        if r["flags"]:
            fails.append("ripe: лишние флаги: %s" % r["flags"])

        t = rg.ripeness(thin)
        if t["ripe"] or t["sealed"] or t["status_ok"]:
            fails.append("thin: должен быть отклонён/незапечатан: %s" % t)
        if "условия" not in t["missing"]:
            fails.append("thin: «условия» должны быть в missing")

        u = rg.ripeness(unsealed)
        if not u["ripe"]:
            fails.append("unsealed: 5 полей+статус → ripe")
        if u["sealed"]:
            fails.append("unsealed: НЕ должен числиться запечатанным")
        if not any("не запечатан" in f for f in u["flags"]):
            fails.append("unsealed: флаг «не запечатан» (И-1) обязателен: %s" % u["flags"])

        # gate(): ripe проходит, thin — назад
        passed, rejected = rg.gate([ripe, thin, unsealed])
        if {os.path.basename(x["file"]) for x in passed} != {"ripe.md", "unsealed.md"}:
            fails.append("gate: в котёл должны пройти ripe+unsealed: %s" % [x["file"] for x in passed])
        if [x for x in rejected if "thin" in x["file"]] == []:
            fails.append("gate: thin должен быть отклонён")

        # seal_hash детерминирован и меняется с телом
        h1 = rg.seal_hash(ripe)
        ripe2 = _w(d, "ripe2.md", RIPE + "\n# Ещё\nдобавка")
        if not h1 or h1 == rg.seal_hash(ripe2):
            fails.append("seal_hash: должен быть детерминирован и меняться с телом")
        if rg.seal_hash(ripe) != h1:
            fails.append("seal_hash: недетерминирован при повторе")

    if fails:
        print("FAIL test_ripeness_gate:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_ripeness_gate: ripe→котёл · thin→назад · unsealed→флаг-И1 · gate-роутинг · seal_hash-детерминизм")


if __name__ == "__main__":
    main()
