"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_reflect_ingest
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_reflect_ingest.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест reflect_ingest.py — нормализация находок + severity + дедуп-ledger + рецидив + resolve."""
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
import reflect_ingest as ri

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

BLOCK_R1 = {"block": "reflect", "gates_passed": False, "advisory_flags": 1, "steps": [
    {"tool": "edges.py", "kind": "gate", "rc": 1, "skipped": False, "tail": "Активные циклы: 1\n  T-1 -> T-2 -> T-1"},
    {"tool": "decay.py", "kind": "advisory", "rc": 1, "skipped": False, "tail": "stale-активные: 3 (todo)"},
    {"tool": "maturity.py", "kind": "advisory", "rc": 0, "skipped": False, "tail": "ok"},
    {"tool": "skipped.py", "kind": "advisory", "rc": 1, "skipped": True, "tail": "x"},
]}
# второй заход: цикл остался (рецидив), decay ушёл (resolved), появился новый
BLOCK_R2 = {"block": "reflect", "gates_passed": False, "advisory_flags": 1, "steps": [
    {"tool": "edges.py", "kind": "gate", "rc": 1, "skipped": False, "tail": "Активные циклы: 1\n  T-9 -> T-8 -> T-9"},
    {"tool": "header.py", "kind": "advisory", "rc": 1, "skipped": False, "tail": "без визитки: foo.md"},
]}


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        ri.LEDGER = os.path.join(d, "ledger.json")

        # заход 1
        f1 = ri.findings_from_blocks(BLOCK_R1)
        # пропущенный шаг и rc==0 не дают находок → 2 находки (edges high, decay medium)
        if len(f1) != 2:
            fails.append("заход1 ожидал 2 находки, факт %d: %s" % (len(f1), [x["tool"] for x in f1]))
        sev = {x["tool"]: x["severity"] for x in f1}
        if sev.get("edges.py") != "high" or sev.get("decay.py") != "medium":
            fails.append("severity неверна: %s" % sev)
        # симптом стабилизирует числа (цикл T-1->T-2 и T-9->T-8 дают ОДИН хэш)
        ri.ingest(f1, "sha1", now=1000)

        f2 = ri.findings_from_blocks(BLOCK_R2)
        ri.ingest(f2, "sha2", now=2000)
        led = ri.load_ledger()

        # edges-цикл: рецидив (count=2), несмотря на разные T-id (числа нормализованы)
        edges_e = [e for e in led["findings"].values() if e["tool"] == "edges.py"]
        if len(edges_e) != 1 or edges_e[0]["count"] != 2:
            fails.append("edges цикл не распознан как рецидив (числа не нормализованы?): %s" % edges_e)
        # decay ушёл во 2-м заходе того же блока → resolved
        decay_e = [e for e in led["findings"].values() if e["tool"] == "decay.py"]
        if not decay_e or decay_e[0]["status"] != "resolved":
            fails.append("decay не помечен resolved при исчезновении: %s" % decay_e)
        # header новый → open
        header_e = [e for e in led["findings"].values() if e["tool"] == "header.py"]
        if not header_e or header_e[0]["status"] != "open":
            fails.append("header (новый) не open")

        s = ri.summarize(led)
        if s["open_high"] != 1:
            fails.append("summary open_high != 1: %s" % s["open_high"])
        if s["resolved_total"] != 1:
            fails.append("summary resolved_total != 1: %s" % s["resolved_total"])

        # третий заход с тем же edges-циклом → count=3 → полый цикл
        ri.ingest(ri.findings_from_blocks(BLOCK_R2), "sha3", now=3000)
        led3 = ri.load_ledger()
        s3 = ri.summarize(led3)
        if not any(e["tool"] == "edges.py" for e in s3["recurring"]):
            fails.append("edges count=3 не попал в recurring (полый цикл)")

        # to_menu: рецидив edges → опция меню, recommended=True, схема decision_menu
        menu = ri.to_menu(led3)
        if "options" not in menu or not menu["options"]:
            fails.append("to_menu пустое меню при рецидиве")
        edges_opt = next((o for o in menu["options"] if "edges.py" in o["title"]), None)
        if not edges_opt or not edges_opt.get("recommended"):
            fails.append("to_menu: рецидив edges не recommended/отсутствует")
        if not all(k in menu for k in ("title", "options", "recommendation", "how_to_choose")):
            fails.append("to_menu: нарушена схема decision_menu")

        # accept: принять edges-находку (wontfix) → уходит из recurring + НЕ ре-открывается рецидивом
        hit = ri.accept(led3, "edges.py", "легитимно — пример")
        if not hit:
            fails.append("accept не пометил edges-находку")
        led_a = ri.load_ledger()
        if any(e["tool"] == "edges.py" for e in ri.summarize(led_a)["recurring"]):
            fails.append("accepted edges всё ещё в recurring (полых циклах)")
        if ri.summarize(led_a)["accepted_total"] < 1:
            fails.append("accepted_total не вырос")
        # рецидив accepted → НЕ ре-открывает (остаётся accepted)
        ri.ingest(ri.findings_from_blocks(BLOCK_R2), "sha4", now=4000)
        led_b = ri.load_ledger()
        edges_b = [e for e in led_b["findings"].values() if e["tool"] == "edges.py"]
        if edges_b and edges_b[0]["status"] != "accepted":
            fails.append("accepted edges ре-открылся при рецидиве (status=%s)" % edges_b[0]["status"])

    if fails:
        print("FAIL test_reflect_ingest:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_reflect_ingest: находки+severity + нормализация-чисел + рецидив + resolve + полый-цикл")


if __name__ == "__main__":
    main()
