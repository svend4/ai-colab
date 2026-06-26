"""text_mux.py — lanes-view: многоагентный cell-store (text_cell.v1) + консенсус/конфликт + кадры + presence.

Реализует «lanes»-режим единого спека (topics/textscene-unified-spec-2026-06-26): много акторов (люди+агенты)
пишут типизированные ЯЧЕЙКИ (text_cell.v1) на общую канву; text_mux показывает их 2D-МАТРИЦЕЙ (строки = row/
тема×вид, столбцы = владелец), делает ВИДИМЫМ согласие и разногласие (а не топит в ленте), сводит кадры
(text_frame.v1 с changed_cells = «текст-диффузия» = прогрессивное уточнение поля) и отвечает на 10-секундный
критерий (кто·над чем·что изменилось·где конфликт·…).

CRDT-мёрж ячеек (merge_cells) переносит фиксы Step 0 на JSON-ячейки:
  • R7 — OR-Set по id + tombstone: статус 'deleted' durable, конкурентная правка НЕ воскрешает;
  • R9 — конкурентное расхождение тела → видимый 'conflict' + КОММУТАТИВНЫЙ tie-break (lamport, sha256), не молча.
Провод файл-нативный (queues/outbox events.jsonl) — «смысл не пиксели», офлайн, без сети.
Инвариант: canon ≠ view (читает ячейки/канву, истину-канон не мутирует; принятие — human/integrator).

CLI:
  python tools/text_mux.py report <canvas-dir>            # presence + матрица + консенсус + 10-сек
  python tools/text_mux.py report <canvas-dir> --json
  python tools/text_mux.py report <canvas-dir> --view lanes|consensus|10s
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import json
import glob
import hashlib

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

STATUS_GLYPH = {"draft": "~", "proposed": "?", "confirmed": "✓", "conflict": "!", "accepted": "★", "deleted": "✗"}
# Словарь видов = ОБЪЕДИНЕНИЕ схем из обоих сошедшихся доков (canvas: answer/claim; mmorpg: proposal) —
# нестыковку источников разрешаем союзом, а не выбором одной.
CELL_KINDS = {"question", "answer", "claim", "proposal", "risk", "evidence", "task", "decision",
              "status", "patch", "summary"}
REQUIRED = ("id", "kind", "owner")


def validate_cell(d):
    """(ok, reason) по text_cell.v1: обязательны id/kind/owner, kind из словаря."""
    if not isinstance(d, dict):
        return False, "не объект"
    for k in REQUIRED:
        if not d.get(k):
            return False, "нет поля %s" % k
    if d["kind"] not in CELL_KINDS:
        return False, "kind '%s' вне словаря" % d["kind"]
    return True, ""


def norm_cell(d):
    """Дефолты text_cell.v1 → полная ячейка."""
    return {"id": d["id"], "canvas_id": d.get("canvas_id", ""), "kind": d["kind"], "owner": d["owner"],
            "topic": d.get("topic", ""), "position": d.get("position") or {}, "depth": int(d.get("depth", 0) or 0),
            "status": d.get("status", "draft"), "links": d.get("links") or [], "body": d.get("body", "") or "",
            "lamport": int(d.get("lamport", 0) or 0)}


def load_cells(canvas_dir):
    """cells/*.json → (валидные ячейки, предупреждения). Невалидные пропускаются с пометкой (не падаем)."""
    cells, warn = [], []
    for p in sorted(glob.glob(os.path.join(canvas_dir, "cells", "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            warn.append("%s: битый json (%s)" % (os.path.basename(p), str(e)[:40])); continue
        ok, why = validate_cell(d)
        (cells.append(norm_cell(d)) if ok else warn.append("%s: %s" % (os.path.basename(p), why)))
    return cells, warn


def _row_key(c):
    pos = c.get("position") or {}
    return pos.get("row") or ("%s/%s" % (c["topic"], c["kind"]))


def _norm_body(b):
    return re.sub(r"\s+", " ", (b or "").strip().lower())[:120]


def _has_contradiction(c):
    return c["status"] == "conflict" or any(
        isinstance(l, dict) and l.get("rel") == "contradicts" for l in c["links"])


def consensus(cells):
    """Группы по row → consensus(≥2 РАЗНЫХ владельца, одинаковое тело) / variants / conflicts. Разногласие ВИДИМО."""
    groups = {}
    for c in cells:
        if c["status"] == "deleted":
            continue
        groups.setdefault(_row_key(c), []).append(c)
    out = []
    for key, cs in sorted(groups.items()):
        bodies = {}
        for c in cs:
            bodies.setdefault(_norm_body(c["body"]), []).append(c)
        cons, variants = [], []
        for _nb, grp in sorted(bodies.items()):
            owners = sorted({c["owner"] for c in grp})
            if len(owners) >= 2:
                cons.append({"body": grp[0]["body"][:80], "owners": owners, "ids": sorted(c["id"] for c in grp)})
            else:
                variants.append({"body": grp[0]["body"][:80], "owner": grp[0]["owner"], "id": grp[0]["id"]})
        conflicts = sorted(c["id"] for c in cs if _has_contradiction(c))
        out.append({"row": key, "owners": sorted({c["owner"] for c in cs}),
                    "consensus": cons, "variants": variants, "conflicts": conflicts})
    return out


def merge_cells(base, ours, theirs):
    """3-way OR-Set ячеек по id (base/ours/theirs: dict id→cell). Возвращает (merged dict, conflicts:[id]).

    R7: в base + удалена любой стороной (нет/deleted) → tombstone durable, НЕ воскресает.
    R9: обе изменили тело по-разному → видимый 'conflict' + коммутативный tie-break (lamport, sha256(body)).
    """
    def live(side, cid):
        c = side.get(cid)
        return c if (c and c.get("status") != "deleted") else None

    merged, conflicts = {}, []
    for cid in sorted(set(ours) | set(theirs) | set(base)):
        lo, lt = live(ours, cid), live(theirs, cid)
        in_base = cid in base
        survive = (lo is not None and lt is not None) if in_base else (lo is not None or lt is not None)
        if not survive:
            continue                                   # удаление durable / нет нигде
        if lo is not None and lt is not None and _norm_body(lo["body"]) != _norm_body(lt["body"]):
            winner = max([lo, lt], key=lambda c: (c.get("lamport", 0),
                         hashlib.sha256(c["body"].encode("utf-8")).hexdigest()))
            m = dict(winner); m["status"] = "conflict"
            m["conflict_bodies"] = sorted([lo["body"][:80], lt["body"][:80]])
            merged[cid] = m; conflicts.append(cid)
        else:
            merged[cid] = dict(lo or lt)
    return merged, conflicts


def _cell_hash(c):
    return hashlib.sha256(("%s|%s|%s" % (c["status"], c["body"], c.get("lamport", 0))).encode("utf-8")).hexdigest()[:12]


def frame(cells, prev_hashes, canvas_id="canvas", frame_no=0):
    """text_frame.v1: снимок + changed_cells (diff к prev_hashes). Возвращает (frame, cur_hashes)."""
    cur = {c["id"]: _cell_hash(c) for c in cells if c["status"] != "deleted"}
    changed = sorted(set(cid for cid, h in cur.items() if prev_hashes.get(cid) != h)
                     | set(cid for cid in prev_hashes if cid not in cur))   # +исчезнувшие
    return ({"schema": "text_frame.v1", "canvas_id": canvas_id, "frame_no": frame_no,
             "cells": sorted(cur), "changed_cells": changed,
             "summary": "%d ячеек, %d изменено" % (len(cur), len(changed))}, cur)


def lane_view(cells):
    """ANSI-матрица: строки = row (тема×вид), столбцы = владелец; ячейка = id+глиф-статус, · если пусто."""
    live = [c for c in cells if c["status"] != "deleted"]
    if not live:
        return "(пусто)"
    rows = sorted({_row_key(c) for c in live})
    owners = sorted({c["owner"] for c in live})
    w = 13
    out = ["ROW \\ OWNER".ljust(18) + "".join(o[:w - 1].ljust(w) for o in owners)]
    for r in rows:
        line = r[:17].ljust(18)
        for o in owners:
            cell = next((c for c in live if _row_key(c) == r and c["owner"] == o), None)
            line += (("%s%s" % (cell["id"][:w - 3], STATUS_GLYPH.get(cell["status"], "?"))) if cell else "·").ljust(w)
        out.append(line)
    return "\n".join(out)


def summary_10s(cells):
    """10-секундный критерий (codex §12) — выводимые поля для report."""
    live = [c for c in cells if c["status"] != "deleted"]
    owners = sorted({c["owner"] for c in live})
    cons = consensus(cells)
    conflict_rows = [g["row"] for g in cons if g["conflicts"] or (len(g["variants"]) >= 2 and not g["consensus"])]
    verified = sorted(c["id"] for c in live if c["status"] in ("confirmed", "accepted"))
    accept_ready = [g["row"] for g in cons if g["consensus"]
                    and not any(c["status"] == "accepted" for c in live if _row_key(c) == g["row"])]
    dangerous = sorted(c["id"] for c in live if c["kind"] == "patch" and c["status"] in ("draft", "proposed"))
    evidence = sorted(c["id"] for c in live if c["kind"] == "evidence"
                      or any(isinstance(l, dict) and l.get("rel") == "derived_from" for l in c["links"]))
    proposed = sorted(c["id"] for c in live if c["status"] == "proposed")
    rows = [("1. Кто работает", ", ".join(owners) or "—"),
            ("2. Над чем (темы)", ", ".join(sorted({c["topic"] for c in live if c["topic"]})) or "—"),
            ("3. Что изменилось", "ячеек %d (детали — text_frame changed_cells)" % len(live)),
            ("4. Где конфликт", ", ".join(conflict_rows) or "нет"),
            ("5. Что проверено", ", ".join(verified) or "—"),
            ("6. Что можно принять", ", ".join(accept_ready) or "—"),
            ("7. Что опасно запускать", ", ".join(dangerous) or "нет (сырых patch нет)"),
            ("8. Где доказательства", ", ".join(evidence) or "—"),
            ("9. Следующий шаг", (proposed[0] if proposed else (accept_ready[0] if accept_ready else "—"))),
            ("10. Спросить у человека", ", ".join(conflict_rows) or "нет")]
    return "\n".join("%-26s %s" % (k, v) for k, v in rows)


def emit_event(outbox, event):
    """Файл-нативный «провод»: дописать событие (cell_seed/status/presence) в events.jsonl. Офлайн, без сети."""
    os.makedirs(outbox, exist_ok=True)
    path = os.path.join(outbox, "events.jsonl")
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def read_events(outbox):
    path = os.path.join(outbox, "events.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def report(canvas_dir, view="all", as_json=False):
    cells, warn = load_cells(canvas_dir)
    cons = consensus(cells)
    if as_json:
        return json.dumps({"cells": len(cells), "warnings": warn, "consensus": cons,
                           "lanes": lane_view(cells)}, ensure_ascii=False, indent=2)
    blocks = []
    cid = os.path.basename(os.path.abspath(canvas_dir))
    blocks.append("=== CANVAS %s · %d ячеек%s ===" % (cid, len(cells), (" · ⚠%d" % len(warn)) if warn else ""))
    if view in ("all", "lanes"):
        blocks.append("── МАТРИЦА (строка×владелец)\n" + lane_view(cells))
    if view in ("all", "consensus"):
        lines = ["── КОНСЕНСУС / РАЗНОГЛАСИЕ"]
        for g in cons:
            for cc in g["consensus"]:
                lines.append("  ✓ [%s] consensus (%s): %s" % (g["row"], ",".join(cc["owners"]), cc["body"]))
            if len(g["variants"]) >= 2 and not g["consensus"]:
                lines.append("  ~ [%s] варианты: %s" % (g["row"], " | ".join("%s:%s" % (v["owner"], v["body"]) for v in g["variants"])))
            for x in g["conflicts"]:
                lines.append("  ! [%s] КОНФЛИКТ: %s" % (g["row"], x))
        blocks.append("\n".join(lines))
    if view in ("all", "10s"):
        blocks.append("── 10-СЕКУНДНЫЙ КРИТЕРИЙ\n" + summary_10s(cells))
    if warn:
        blocks.append("⚠ предупреждения: " + "; ".join(warn))
    return "\n\n".join(blocks)


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2 or args[0] != "report":
        print("text_mux: использование: text_mux.py report <canvas-dir> [--json] [--view lanes|consensus|10s]"); return 2
    canvas_dir = args[1] if os.path.isabs(args[1]) else os.path.join(ROOT, args[1])
    if not os.path.isdir(canvas_dir):
        print("text_mux: канва не найдена: %s" % canvas_dir); return 2
    view = "all"
    if "--view" in argv:
        i = argv.index("--view")
        if i + 1 < len(argv):
            view = argv[i + 1]
    print(report(canvas_dir, view=view, as_json=("--json" in argv)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
