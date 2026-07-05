"""Тест oracle_quorum.py — кворум независимых судей + детекция рассогласия/гомогенности."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import oracle_quorum as oq

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DOC = """# Кворум по теме X

## Минор сохраняется без порога
- judge: gpt/analyst | verdict: refuted | reason: спам засоряет
- judge: claude/lawyer | verdict: refuted | reason: нужен порог осмысленности
- judge: gemini/critic | verdict: survived | reason: резерв low-prior ок

## Спорный инвариант с расколом
- judge: gpt/analyst | verdict: survived | reason: a
- judge: claude/lawyer | verdict: refuted | reason: b
- judge: gemini/critic | verdict: open | reason: c

## Все судьи одной модели (не независимы)
- judge: gpt/analyst | verdict: refuted | reason: a
- judge: gpt/lawyer | verdict: refuted | reason: b
"""


def main():
    fails = []

    # quorum: 2 refuted vs 1 survived → decisive refuted (>=2 и большинство)
    q = oq.quorum(["refuted", "refuted", "survived"])
    if not q["decisive"] or q["verdict"] != "refuted":
        fails.append("2 из 3 refuted должно быть decisive refuted: %s" % q)
    # раскол 1/1/1 → contested (захват/неоднозначность видимы)
    q2 = oq.quorum(["survived", "refuted", "open"])
    if q2["decisive"] or q2["verdict"] != "contested":
        fails.append("раскол 1/1/1 → contested: %s" % q2)
    # 1 судья → не decisive (нельзя решать одним судьёй, OQ-1)
    if oq.quorum(["refuted"])["decisive"]:
        fails.append("один судья не может быть decisive (OQ-1)")

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.md")
        open(p, "w", encoding="utf-8", newline="\n").write(DOC)
        recs = oq.parse_judges(p)
        if len(recs) != 3:
            fails.append("ожидалось 3 claim, получено %d" % len(recs))
        if len(recs[0]["judges"]) != 3 or recs[0]["judges"][0]["model"] != "gpt":
            fails.append("судьи claim 1 разобраны неверно: %s" % recs[0]["judges"])

        a0 = oq._assess(recs[0])
        if a0["quorum"]["verdict"] != "refuted":
            fails.append("claim 1: кворум должен дать refuted (2/3)")
        a1 = oq._assess(recs[1])
        if a1["quorum"]["decisive"]:
            fails.append("claim 2 (раскол) должен быть contested")

        # claim 3: все судьи одной модели (gpt) → флаг не-независимости
        a2 = oq._assess(recs[2])
        if not any("одной модели" in f.lower() for f in a2["independence"]["flags"]):
            fails.append("гомогенные судьи (одна модель) должны быть помечены (рекурсия оракула): %s" % a2["independence"]["flags"])

    if fails:
        print("FAIL test_oracle_quorum:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_oracle_quorum: кворум(2/3→decisive) · раскол→contested · 1-судья не decisive · гомогенность судей помечена")


if __name__ == "__main__":
    main()
