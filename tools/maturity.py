# ==========================================
# [FILE ID CARD]
# ID: tools.maturity
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: зрелость атома 0-1000‰ (DIV-21): СИНТЕЗ трёх осей в один балл.
# ==========================================
"""maturity.py — зрелость атома 0-1000‰ (DIV-21): СИНТЕЗ трёх осей в один балл.

Идея Stefan «% выполнения / зрелость». Композит по 5 бинарным осям (каждая 200‰), переиспользуя уже
построенное: ось-граф (edges.py) + ось-время (decay.py) + front-matter. Балл = сколько осей выполнено
× 200. Низкий балл = «недозрелый» атом (нет визитки / изолят / застыл / без типа / не завершён).
Ранжированный список недозрелых — вход роутеру. Read-only.

5 осей зрелости (по 200‰):
  identity   — есть id + type (корректный front-matter)
  card       — есть title + gist (визитка-карточка, дискаверабелен)
  connected  — ≥1 структурное ребро в графе (не изолят) — ОСЬ-ГРАФ
  fresh      — не stale-активен (горячий или терминальный) — ОСЬ-ВРЕМЯ
  resolved   — терминальный статус (done/accepted/answered/rejected/superseded)

CLI:
  python tools/maturity.py                 # распределение + топ недозрелых
  python tools/maturity.py --json
  python tools/maturity.py <id>            # балл одного атома с разбивкой по осям
  python tools/maturity.py --list immature # списком (--threshold N, по умолч. 600)
"""
import os
from _ioutil import configure_output
import sys
import json

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
sys.path.insert(0, HERE)
import edges
import decay
from _cli import help_guard

AXES = ("identity", "card", "connected", "fresh", "resolved")
PER_AXIS = 200
STRUCTURAL = ("depends", "related", "superseded", "basis")
TERMINAL = ("done", "accepted", "answered", "rejected", "superseded", "archived")
SCORE_ATOMS = ("T-", "D-", "Q-")  # рабочие единицы (задачи/решения/вопросы)
DEFAULT_THRESHOLD = 600


def _axes_for(n, deg, stale_files):
    fm = n["fm"]
    status = (n["status"] or "").strip()
    return {
        "identity": bool(n["id"]) and bool((fm.get("type") or "").strip()),
        "card": bool((fm.get("title") or "").strip()) and bool((fm.get("gist") or "").strip()),
        "connected": deg.get(n["key"], 0) > 0,
        "fresh": n["path"] not in stale_files,
        "resolved": status in TERMINAL,
    }


def collect(now=None):
    nodes, by_id, by_slug = edges.load_nodes()
    elist = edges.build_edges(nodes, by_id, by_slug)
    deg = {}
    for e in elist:
        if e["type"] in STRUCTURAL:
            deg[e["src"]] = deg.get(e["src"], 0) + 1
            if not e["dangling"]:
                deg[e["dst"]] = deg.get(e["dst"], 0) + 1
    dec = decay.collect(now)
    stale_files = {r["file"] for r in dec["stale_active"]}
    rows = []
    for key, n in nodes.items():
        if not (n["id"] and n["id"][:2] in SCORE_ATOMS):
            continue
        ax = _axes_for(n, deg, stale_files)
        score = sum(PER_AXIS for v in ax.values() if v)
        rows.append({"id": n["id"], "file": n["path"], "status": n["status"],
                     "score": score, "axes": ax,
                     "missing": [a for a in AXES if not ax[a]]})
    rows.sort(key=lambda r: (r["score"], r["id"]))
    return rows


def _bucket(score):
    if score >= 800:
        return "mature"
    if score >= 600:
        return "ok"
    if score >= 400:
        return "developing"
    return "immature"


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    threshold = DEFAULT_THRESHOLD
    if "--threshold" in argv:
        i = argv.index("--threshold")
        if i + 1 < len(argv):
            threshold = int(argv[i + 1])
    listing = None
    if "--list" in argv:
        i = argv.index("--list")
        if i + 1 < len(argv):
            listing = argv[i + 1]

    rows = collect()

    if args:  # один атом
        rid = args[0]
        r = next((x for x in rows if x["id"] == rid), None)
        if not r:
            print("нет рабочего атома %s (T/D/Q)" % rid); return 1
        if as_json:
            print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
        print("=== ЗРЕЛОСТЬ %s: %d‰ (%s) ===" % (r["id"], r["score"], _bucket(r["score"])))
        for a in AXES:
            print("    %s %s" % ("✓" if r["axes"][a] else "✗", a))
        return 0

    if listing:
        sel = [r for r in rows if r["score"] < threshold] if listing == "immature" \
            else [r for r in rows if _bucket(r["score"]) == listing]
        if as_json:
            print(json.dumps(sel, ensure_ascii=False, indent=2)); return 0
        for r in sel:
            print("  %4d‰  %-7s %-8s %s  (нет: %s)" % (
                r["score"], _bucket(r["score"]), r["status"] or "—", r["id"], ", ".join(r["missing"])))
        return 0

    # сводка
    if as_json:
        dist = {}
        for r in rows:
            b = _bucket(r["score"]); dist[b] = dist.get(b, 0) + 1
        avg = round(sum(r["score"] for r in rows) / len(rows)) if rows else 0
        print(json.dumps({"total": len(rows), "avg_permille": avg, "distribution": dist,
                          "immature": [r for r in rows if r["score"] < threshold][:30]},
                         ensure_ascii=False, indent=2))
        return 0
    dist = {}
    for r in rows:
        b = _bucket(r["score"]); dist[b] = dist.get(b, 0) + 1
    avg = round(sum(r["score"] for r in rows) / len(rows)) if rows else 0
    print("=== ЗРЕЛОСТЬ атомов T/D/Q (DIV-21, синтез 3 осей) ===")
    print("  всего: %d   средняя: %d‰" % (len(rows), avg))
    print("  mature(≥800): %d · ok(≥600): %d · developing(≥400): %d · immature(<400): %d" % (
        dist.get("mature", 0), dist.get("ok", 0), dist.get("developing", 0), dist.get("immature", 0)))
    low = [r for r in rows if r["score"] < threshold]
    print("\n  Недозрелые (<%d‰, кандидаты роутеру): %d" % (threshold, len(low)))
    for r in low[:20]:
        print("    %4d‰  %-8s %s  (нет: %s)" % (r["score"], r["status"] or "—", r["id"], ", ".join(r["missing"])))
    if len(low) > 20:
        print("    … и ещё %d" % (len(low) - 20))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
