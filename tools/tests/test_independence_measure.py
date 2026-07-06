"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_independence_measure
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_independence_measure.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест independence_measure.py — эффективное число свидетелей (схлопывание клонов)."""
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
import independence_measure as im

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _v(model, lens, body):
    return "---\nmodel: %s\nlens: %s\nsealed: blind\n---\n%s\n" % (model, lens, body)


def _w(d, name, txt):
    p = os.path.join(d, name)
    open(p, "w", encoding="utf-8", newline="\n").write(txt)
    return p


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        # A и B — клоны (тот же генотип m1/L1 + почти тот же текст); C — другой генотип+текст
        A = _w(d, "a.md", _v("m1", "L1", "alpha beta gamma delta epsilon"))
        B = _w(d, "b.md", _v("m1", "L1", "alpha beta gamma delta epsilon zeta"))
        C = _w(d, "c.md", _v("m2", "L2", "omega psilon chiron phiton tauon"))

        r = im.analyze([A, B, C])
        if r["n_raw"] != 3:
            fails.append("n_raw != 3")
        if r["n_effective"] != 2:
            fails.append("эфф. свидетелей должно быть 2 (A,B клоны): %s" % r["n_effective"])
        cg = [set(g) for g in r["clone_groups"]]
        if {"a.md", "b.md"} not in cg:
            fails.append("A,B должны быть в одном клон-кластере: %s" % r["clone_groups"])
        if not any("клон" in f.lower() for f in r["flags"]):
            fails.append("флаг про клонов отсутствует")

        if im.effective_witnesses([im._load(A), im._load(B), im._load(C)]) != 2:
            fails.append("effective_witnesses != 2")

        # surface_div: идентичные → 0, дизъюнктные → 1
        ta = im._tokens("alpha beta gamma")
        if im.surface_div(ta, ta) != 0.0:
            fails.append("surface_div идентичных != 0")
        if im.surface_div(ta, im._tokens("omega psilon chiron")) != 1.0:
            fails.append("surface_div дизъюнктных != 1")

        # генотип-гомогенность: все одной модели, разные линзы, разный текст → 3 свидетеля, но ФЛАГ
        with tempfile.TemporaryDirectory() as d2:
            X = _w(d2, "x.md", _v("m1", "L1", "alpha beta gamma delta"))
            Y = _w(d2, "y.md", _v("m1", "L2", "omega psilon chiron phiton"))
            Z = _w(d2, "z.md", _v("m1", "L3", "kappa lambda mu nu xi"))
            r2 = im.analyze([X, Y, Z])
            if r2["n_effective"] != 3:
                fails.append("разные линзы+текст → 3 свидетеля: %s" % r2["n_effective"])
            if not any("одной модели" in f for f in r2["flags"]):
                fails.append("флаг генотип-гомогенности (одна модель) обязателен: %s" % r2["flags"])

        # SEAL-ПРОВЕНАНС (фикс терсной-истины, остаток independence-weight): два sealed-blind разного
        # генотипа на КОРОТКОЙ ИСТИНЕ (даже verbatim) → 2 свидетеля: провенанс доказывает «не копия»
        Tv = _w(d, "tv.md", _v("m2", "L2", "срок составляет тридцать календарных дней"))
        Tw = _w(d, "tw.md", _v("m3", "L3", "срок составляет тридцать календарных дней"))
        if im.effective_witnesses([im._load(Tv), im._load(Tw)]) != 2:
            fails.append("seal-провенанс: два sealed-blind на терсной истине = 2 свидетеля (не схлопывать)")
        # near-verbatim БЕЗ seal-провенанса (нет sealed:) → 1 свидетель (это копирование)
        C1 = _w(d, "c1.md", "---\nmodel: m9\nlens: L9\n---\nсрок составляет тридцать календарных дней ответ")
        C2 = _w(d, "c2.md", "---\nmodel: m8\nlens: L8\n---\nсрок составляет тридцать календарных дней ответ")
        if im.effective_witnesses([im._load(C1), im._load(C2)]) != 1:
            fails.append("near-verbatim БЕЗ seal-провенанса (>=COPY_THR) → 1 свидетель (копия)")
        # тот же генотип + sealed → всё равно клон (эхо весов, seal не спасает)
        S1 = _w(d, "s1.md", _v("m5", "L5", "альфа бета гамма дельta эпсилон уникальный один"))
        S2 = _w(d, "s2.md", _v("m5", "L5", "альфа бета гамма дельta эпсилон уникальный два"))
        if im.effective_witnesses([im._load(S1), im._load(S2)]) != 1:
            fails.append("тот же генотип + sealed → клон (1 свидетель): seal не делает клонов независимыми")

    if fails:
        print("FAIL test_independence_measure:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_independence_measure: клоны→1 свидетель · surface_div · флаг генотип-гомогенности")


if __name__ == "__main__":
    main()
