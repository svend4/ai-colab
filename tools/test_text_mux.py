"""Тест text_mux.py — cell-store: валидация · консенсус/конфликт · merge_cells(R7/R9) · кадры-diff · lane/10s · провод."""
import os
import sys
import json
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import text_mux as tm

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def cell(cid, owner, kind="claim", row="r1", body="", status="proposed", lamport=0, links=None):
    return {"id": cid, "kind": kind, "owner": owner, "topic": "t", "position": {"row": row},
            "status": status, "body": body, "lamport": lamport, "links": links or []}


def main():
    fails = []

    # 1) валидация
    ok, _ = tm.validate_cell(cell("c1", "a"))
    if not ok:
        fails.append("валидная ячейка должна пройти")
    if tm.validate_cell({"id": "x", "owner": "a"})[0]:
        fails.append("без kind — невалидна")
    if tm.validate_cell(cell("c", "a", kind="zzz"))[0]:
        fails.append("kind вне словаря — невалидна")

    # 2) консенсус: 2 РАЗНЫХ владельца одинаковое тело → consensus; разные → variants
    cells = [cell("c1", "alice", row="risks", body="P2P поздний этап"),
             cell("c2", "bob", row="risks", body="p2p  поздний  этап"),   # тот же смысл (норм. тела)
             cell("c3", "carol", row="proposal", body="вариант A"),
             cell("c4", "dave", row="proposal", body="вариант B")]
    cons = {g["row"]: g for g in tm.consensus(cells)}
    if not cons["risks"]["consensus"] or sorted(cons["risks"]["consensus"][0]["owners"]) != ["alice", "bob"]:
        fails.append("risks: alice+bob одинаковое тело → consensus: %s" % cons["risks"]["consensus"])
    if cons["proposal"]["consensus"] or len(cons["proposal"]["variants"]) != 2:
        fails.append("proposal: разные тела → 2 варианта, не consensus: %s" % cons["proposal"])

    # 3) конфликт виден (status=conflict ИЛИ contradicts-link)
    cc = [cell("c5", "a", row="rx", status="conflict", body="x"),
          cell("c6", "b", row="ry", body="y", links=[{"rel": "contradicts", "target": "c5"}])]
    rows = {g["row"]: g for g in tm.consensus(cc)}
    if "c5" not in rows["rx"]["conflicts"] or "c6" not in rows["ry"]["conflicts"]:
        fails.append("конфликт должен детектиться (status/contradicts): %s" % rows)

    # 4) R7: удаление durable — конкурентная правка НЕ воскрешает
    base = {"X": cell("X", "a", body="b0"), "Y": cell("Y", "a", body="b0")}
    ours = {"X": cell("X", "a", status="deleted", body="b0"), "Y": cell("Y", "a", body="b0")}  # удалил X
    theirs = {"X": cell("X", "b", body="b0-edited"), "Y": cell("Y", "a", body="b0")}            # правил X
    merged, _conf = tm.merge_cells(base, ours, theirs)
    if "X" in merged:
        fails.append("R7: удалённый X не должен воскреснуть конкурентной правкой: %s" % list(merged))
    if "Y" not in merged:
        fails.append("R7: неудалённый Y должен остаться")

    # 4b) R7: новая ячейка (не в base) выживает
    m2, _ = tm.merge_cells({}, {"N": cell("N", "a", body="new")}, {})
    if "N" not in m2:
        fails.append("R7: новая ячейка add-wins")

    # 5) R9: расхождение тела → conflict + КОММУТАТИВНЫЙ tie-break
    b = {"Z": cell("Z", "a", body="base")}
    o = {"Z": cell("Z", "a", body="версия ours", lamport=1)}
    t = {"Z": cell("Z", "b", body="версия theirs", lamport=2)}
    m_ot, conf_ot = tm.merge_cells(b, o, t)
    m_to, _ = tm.merge_cells(b, t, o)
    if "Z" not in conf_ot or m_ot["Z"]["status"] != "conflict":
        fails.append("R9: расхождение тела → conflict")
    if m_ot["Z"]["body"] != m_to["Z"]["body"]:
        fails.append("R9: tie-break НЕ коммутативен: %s vs %s" % (m_ot["Z"]["body"], m_to["Z"]["body"]))
    if "conflict_bodies" not in m_ot["Z"] or len(m_ot["Z"]["conflict_bodies"]) != 2:
        fails.append("R9: оба тела должны быть видимы (не молча)")

    # 6) кадры: changed_cells = дифф к прошлому хэшу
    f1, h1 = tm.frame(cells, {}, "cv", 1)
    if set(f1["changed_cells"]) != {"c1", "c2", "c3", "c4"}:
        fails.append("первый кадр: все ячейки изменены: %s" % f1["changed_cells"])
    cells2 = [dict(c) for c in cells]
    cells2[0]["body"] = "изменено"; cells2[0]["lamport"] = 5
    f2, _ = tm.frame(cells2, h1, "cv", 2)
    if f2["changed_cells"] != ["c1"]:
        fails.append("второй кадр: изменена только c1: %s" % f2["changed_cells"])

    # 7) lane_view + 10s: не падают, несут матрицу/поля
    if "ROW \\ OWNER" not in tm.lane_view(cells):
        fails.append("lane_view должен дать заголовок матрицы")
    s10 = tm.summary_10s(cells)
    if "1. Кто работает" not in s10 or "alice" not in s10:
        fails.append("10s должен перечислить владельцев")

    # 8) load_cells + провод events (файл-нативный, офлайн)
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "cells"))
        json.dump(cell("c1", "a", body="ok"), open(os.path.join(d, "cells", "c1.json"), "w", encoding="utf-8"))
        open(os.path.join(d, "cells", "bad.json"), "w", encoding="utf-8").write("{не json")
        loaded, warn = tm.load_cells(d)
        if len(loaded) != 1 or not warn:
            fails.append("load_cells: 1 валидная + 1 предупреждение, получено %d/%d" % (len(loaded), len(warn)))
        ob = os.path.join(d, "outbox")
        tm.emit_event(ob, {"kind": "cell_seed", "id": "c1"})
        tm.emit_event(ob, {"kind": "status", "id": "c1", "status": "accepted"})
        ev = tm.read_events(ob)
        if len(ev) != 2 or ev[1]["status"] != "accepted":
            fails.append("провод events.jsonl: 2 события, последнее accepted: %s" % ev)

    if fails:
        print("FAIL test_text_mux:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_text_mux: валидация · консенсус/варианты/конфликт · merge_cells(R7 durable-delete · R9 коммут.) · кадры-diff · lane/10s · провод")


if __name__ == "__main__":
    main()
