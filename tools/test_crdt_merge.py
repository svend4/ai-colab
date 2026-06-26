"""Тест crdt_merge.py — 3-way field-level мёрж канона (union списков, конфликт-флаги, нет потерь)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
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

    # 2) конфликт-скаляр: оба сменили status по-разному
    m2 = cm.merge3(base, item(["a"], "accepted", "базовое тело"), item(["a"], "rejected", "базовое тело"))
    if not any("status" in c for c in m2["conflicts"]):
        fails.append("оба сменили status по-разному → конфликт: %s" % m2["conflicts"])
    if m2["fm"]["status"] != "accepted":
        fails.append("при конфликте берётся ours (accepted): %s" % m2["fm"]["status"])

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

    if fails:
        print("FAIL test_crdt_merge:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_crdt_merge: union-списков · status 3-way · конфликт-скаляр · конфликт-тело(без потерь+маркеры) · round-trip")


if __name__ == "__main__":
    main()
