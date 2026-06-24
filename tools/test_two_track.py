"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_two_track
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_two_track.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест two_track.py — двухтрековая классификация (консенсус ratify / разногласие detail)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import two_track as tt

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

CONS = """# consensus
## §1. ОБЩЕЕ
### C-01. Первый консенсус
### C-02. Второй консенсус
## §2. СЕРЕДИНА
### M-01. Золотой голос (не трек-1)
"""
DIV = """# divergence
## A. КОНФЛИКТЫ ФАКТОВ
### DIV-01. Конфликт статуса
## B. STANDALONE
### DIV-02. Один голос
### DIV-03. Ещё один
"""


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        cp = os.path.join(d, "cons.md"); dp = os.path.join(d, "div.md")
        open(cp, "w", encoding="utf-8").write(CONS)
        open(dp, "w", encoding="utf-8").write(DIV)
        data = tt.collect(consensus=cp, divergence=dp)
        t1, t2 = data["track1_ratify"], data["track2_detail"]
        # трек-1 = только C- (не M-)
        ids1 = {i["id"] for i in t1}
        if ids1 != {"C-01", "C-02"}:
            fails.append("track1 ожид {C-01,C-02}, факт %s" % sorted(ids1))
        if t1 and t1[0]["mark"] != "READY-RATIFY-BUILD":
            fails.append("track1 mark != READY-RATIFY-BUILD")
        # трек-2 = DIV- с под-категориями
        ids2 = {i["id"] for i in t2}
        if ids2 != {"DIV-01", "DIV-02", "DIV-03"}:
            fails.append("track2 ожид 3 DIV, факт %s" % sorted(ids2))
        if t2 and t2[0]["mark"] != "PENDING-DETAIL":
            fails.append("track2 mark != PENDING-DETAIL")
        # под-категория conflict подхвачена
        div01 = next((i for i in t2 if i["id"] == "DIV-01"), {})
        if "КОНФЛИКТ" not in div01.get("subcat", "").upper():
            fails.append("DIV-01 не получил под-категорию конфликта")
        # render содержит обе части + пропорцию
        r = tt.render(data)
        for n in ("ТРЕК-1", "ТРЕК-2", "пропорция", "READY-RATIFY-BUILD", "PENDING-DETAIL"):
            if n not in r:
                fails.append("render без %r" % n)
        # --track фильтр
        ronly = tt.render(data, only="ratify")
        if "DIV-02" in ronly:
            fails.append("--track ratify протёк divergence")

    if fails:
        print("FAIL test_two_track:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_two_track: 2 трека (ratify/detail) + марки + под-категории + фильтр")


if __name__ == "__main__":
    main()
