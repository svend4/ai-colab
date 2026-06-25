"""sanation.py — омоложение ВЕРХУШКИ канона (информационный рефакторинг, не классический).

Операционализирует docs/information-refactoring-sanation-standard.md: оздоравливает живой
метаданный слой (визитка/граф/свежесть/зрелость), НЕ трогая тело и историю. Метафора поезда:
санируем ведущий состав, кандидатов на отцепку (cold+terminal) показываем для архива (тело сохранить,
D-026 — не truncate). Read-only отчёт + одна безопасная регенерация (--apply: индексы навигации).

Качественно, не количественно: цель — выше зрелость/свежесть верхушки, не меньше файлов.

CLI:
  python tools/sanation.py            # отчёт здоровья верхушки + кандидаты санации
  python tools/sanation.py --json
  python tools/sanation.py --apply    # + регенерировать folder-индексы (безопасная идемпотентная запись)
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import json

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
sys.path.insert(0, HERE)
import edges
import decay

TERMINAL = ("done", "accepted", "answered", "rejected", "superseded", "archived", "historical")


def collect():
    nodes, by_id, by_slug = edges.load_nodes()
    elist = edges.build_edges(nodes, by_id, by_slug)
    gc = edges.check(nodes, elist, by_id)
    dec = decay.collect()

    # 1) визитка-покрытие (живая верхушка): title = базовая визитка; gist — богатая (для topics/docs)
    idn = [n for n in nodes.values() if n["id"]]
    total = len(nodes)
    with_card = sum(1 for n in nodes.values() if (n["fm"].get("title") or "").strip())

    # 2) кандидаты на ОТЦЕПКУ (cold + терминальный) — архив, тело сохранить (D-026)
    archive = sorted(
        ({"id": r["id"] or r["file"], "file": r["file"], "status": r["status"], "age": r["age_days"]}
         for r in dec["rows"] if r["temp"] == "cold" and r["status"] in TERMINAL),
        key=lambda x: -(x["age"] or 0))

    # 3) кандидаты на BACKFILL визитки: атом БЕЗ title (истинно нет визитки) ИЛИ topics/docs без gist
    backfill = sorted(
        ({"id": n["id"] or n["slug"], "file": n["path"],
          "lack": "title" if not (n["fm"].get("title") or "").strip() else "gist"}
         for n in nodes.values()
         if not (n["fm"].get("title") or "").strip()
         or (n["folder"] in ("topics", "docs") and not (n["fm"].get("gist") or "").strip())),
        key=lambda x: x["file"])

    freshness = dec["counts"]
    return {
        "top_health": {
            "atoms": total,
            "visitka_covered": with_card,
            "visitka_pct": round(100 * with_card / total) if total else 0,
            "graph_hard_defects": len(gc["dangling"]) + len(gc["cycles"]),
            "graph_soft": len(gc.get("topic_unresolved", [])) + len(gc.get("asym_related", [])),
            "fresh_hot": freshness.get("hot", 0),
            "fresh_warm": freshness.get("warm", 0),
            "fresh_cold": freshness.get("cold", 0),
            "stale_active": len(dec.get("stale_active", [])),
        },
        "candidates": {
            "detach_to_archive": archive,        # cold+terminal → архив (тело сохранить)
            "backfill_visitka": backfill,        # без gist → backfill через ROUTE
            "stale_active": dec.get("stale_active", []),  # активное застывшее → ре-оценка
        },
    }


def apply_safe():
    """Единственная безопасная идемпотентная регенерация верхушки: folder-индексы навигации."""
    try:
        import folder_index
        done = []
        for d in folder_index.BIG:
            folder_index.write(d)
            done.append(d)
        return done
    except Exception as e:
        return ["WARN: %s" % e]


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    do_apply = "--apply" in argv
    r = collect()
    if do_apply:
        r["applied_indexes"] = apply_safe()
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    h = r["top_health"]
    print("=== САНАЦИЯ — здоровье ВЕРХУШКИ канона (омоложение, не переписывание) ===")
    print("  атомов: %d · визитка: %d (%d%%) · граф: %d жёстких / %d мягких" % (
        h["atoms"], h["visitka_covered"], h["visitka_pct"], h["graph_hard_defects"], h["graph_soft"]))
    print("  свежесть: 🔥%d hot · 🌡%d warm · ❄%d cold · застывших-активных: %d" % (
        h["fresh_hot"], h["fresh_warm"], h["fresh_cold"], h["stale_active"]))
    c = r["candidates"]
    print("\n  Кандидаты санации (НЕ авто — через ROUTE/человека, тело сохранить — D-026):")
    print("    • отцепить в архив (cold+terminal): %d" % len(c["detach_to_archive"]))
    for x in c["detach_to_archive"][:8]:
        print("        ❄ %sд %-9s %s" % (x["age"], x["status"], x["id"]))
    print("    • backfill визитки (нет title / тема-док без gist): %d" % len(c["backfill_visitka"]))
    for x in c["backfill_visitka"][:8]:
        print("        нет %-5s %s" % (x.get("lack", "?"), x["id"]))
    print("    • застывшее активное (ре-оценка): %d" % len(c["stale_active"]))
    if do_apply:
        print("\n  ✓ верхушка омоложена: регенерированы индексы %s" % ", ".join(r["applied_indexes"]))
    else:
        print("\n  (--apply: безопасно регенерировать folder-индексы; контент-санация — через ROUTE)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
