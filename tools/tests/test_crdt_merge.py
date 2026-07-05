"""Тест crdt_merge.py — 3-way field-level мёрж канона (union списков, конфликт-флаги, нет потерь)."""
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

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import crdt_merge as cm

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def item(related, status, body):
    return cm.parse_item("---\nid: x\nstatus: %s\nrelated: [%s]\n---\n%s\n" % (status, ", ".join(related), body))


def main():
    fails = []

    # 1) чистое слияние: ours добавил c + сменил status; theirs добавил d + сменил body
    base = item(["a", "b"], "proposed", "базовое тело")
    ours = item(["a", "b", "c"], "accepted", "базовое тело")
    theirs = item(["a", "b", "d"], "proposed", "тело изменено theirs")
    m = cm.merge3(base, ours, theirs)
    if set(m["fm"]["related"]) != {"a", "b", "c", "d"}:
        fails.append("related должно быть union {a,b,c,d} (ничего не потеряно): %s" % m["fm"]["related"])
    if m["fm"]["status"] != "accepted":
        fails.append("status: ours сменил, theirs нет → accepted: %s" % m["fm"]["status"])
    if "тело изменено theirs" not in m["body"]:
        fails.append("body: theirs сменил, ours нет → тело theirs")
    if m["conflicts"]:
        fails.append("чистое слияние не должно дать конфликтов: %s" % m["conflicts"])

    # 2) конфликт-скаляр: оба сменили status по-разному → флаг + КОММУТАТИВНЫЙ детерм. выбор (R9)
    A = item(["a"], "accepted", "базовое тело")
    B = item(["a"], "rejected", "базовое тело")
    m2 = cm.merge3(base, A, B)
    if not any("status" in c for c in m2["conflicts"]):
        fails.append("оба сменили status по-разному → конфликт: %s" % m2["conflicts"])
    if m2["fm"]["status"] not in ("accepted", "rejected"):
        fails.append("при конфликте выбран один из значений: %s" % m2["fm"]["status"])
    m2r = cm.merge3(base, B, A)   # обратный порядок аргументов
    if m2["fm"]["status"] != m2r["fm"]["status"]:
        fails.append("R9: _merge_scalar НЕ коммутативен: %s vs %s" % (m2["fm"]["status"], m2r["fm"]["status"]))

    # 3) конфликт-тело: оба сменили тело по-разному → маркеры, НЕ потеря
    m3 = cm.merge3(base, item(["a"], "proposed", "версия ours"), item(["a"], "proposed", "версия theirs"))
    if not any("body" in c for c in m3["conflicts"]):
        fails.append("оба сменили тело → конфликт-флаг")
    if "версия ours" not in m3["body"] or "версия theirs" not in m3["body"]:
        fails.append("обе версии тела должны быть В выводе (не потеряны): %s" % m3["body"][:80])
    if "<<<<<<<" not in m3["body"]:
        fails.append("конфликт-тело должно нести маркеры слияния")

    # 4) round-trip: render слитого парсится обратно
    txt = cm.render_item(m)
    re_parsed = cm.parse_item(txt)
    if re_parsed["fm"].get("status") != "accepted":
        fails.append("render→parse round-trip потерял status")

    # 5) R7: удаление durable — конкурентная правка тела НЕ воскрешает удалённую карточку
    base5 = item(["a", "b"], "proposed", "тело")
    ours5 = item(["a", "c"], "proposed", "тело")          # убрал b, добавил c
    theirs5 = item(["a", "b"], "proposed", "тело иное")   # оставил b, тронул только тело
    m5 = cm.merge3(base5, ours5, theirs5)
    rel5 = set(m5["fm"]["related"])
    if "b" in rel5:
        fails.append("R7: удалённая ours карточка b НЕ должна воскреснуть конкурентной правкой: %s" % rel5)
    if rel5 != {"a", "c"}:
        fails.append("R7: ожидалось {a,c} (b удалён durable, c добавлен): %s" % rel5)

    # 6) R7: y убран ОБЕИМИ → durable; новое поле без base = чистый union
    m6 = cm.merge3(item(["x", "y"], "proposed", "т"), item(["x"], "proposed", "т"), item(["x"], "proposed", "т"))
    if "y" in set(m6["fm"]["related"]):
        fails.append("R7: y убран обеими сторонами → не должен остаться: %s" % m6["fm"]["related"])

    if fails:
        print("FAIL test_crdt_merge:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_crdt_merge: 3-way OR-Set(add-wins+remove-durable R7) · скаляр-коммутативность R9 · конфликт-тело(маркеры) · round-trip")


if __name__ == "__main__":
    main()
