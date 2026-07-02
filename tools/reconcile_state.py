#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.reconcile_state
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт reconcile_state.py. Описание сгенерировано автоматически.
# ==========================================
"""
HELP = """State reconciliation layer (T-066 → реализация).

Сверяет primary state (tasks/*.md, queues/claimed, queues/done) с производными
снимками (index.json, logs/pipeline.json) и пишет ОТЧЁТ о расхождениях. На первом
этапе ничего не чинит автоматически — только сообщает (см. docs/state-reconciliation-layer.md).

Переиспользует pipeline.py (тот же парсер front-matter, claim/TTL, build_pipeline_state),
чтобы вывод совпадал с конвейером.

    python tools/reconcile_state.py            # = report: посчитать + записать отчёт в queues/outbox/
    python tools/reconcile_state.py check      # посчитать и напечатать, НИЧЕГО не писать
    python tools/reconcile_state.py report      # посчитать и записать json+md отчёт
    python tools/reconcile_state.py fix         # dry-run: что бы перегенерировал (производное); ничего не пишет
    python tools/reconcile_state.py fix --apply # перегенерировать ТОЛЬКО производное (index/snapshot); primary не трогает

Exit code: 0 — расхождений нет; 1 — есть warning; 2 — есть error.
`fix` чинит лишь производные снимки (index.json/навигация, PIPELINE.md/logs/pipeline.json), детерминированно
из primary; source of truth (tasks/*.md, queues/*) — никогда; primary-дрейф выводится как ручные action items.
"""
import os
import sys
import json
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P
from _cli import help_guard


ROOT = P.ROOT
DONE = P.DONE
CLAIMED = P.CLAIMED
OUTBOX = os.path.join(ROOT, "queues", "outbox")
INDEX_JSON = os.path.join(ROOT, "index.json")
PIPELINE_JSON = P.PIPELINE_JSON

PRIMARY_DONE_STATES = ("done",)
ACTIVE_STATES = ("todo", "doing")


def _done_marker(tid):
    return os.path.join(DONE, "%s.done.md" % tid)


def _ids_from_dir(dirpath, suffix):
    out = []
    if not os.path.isdir(dirpath):
        return out
    for fn in os.listdir(dirpath):
        if fn.endswith(suffix):
            out.append(fn[: -len(suffix)])
    return out


def check_tasks(items):
    tasks = P.collect_tasks()

    # --- по каждой задаче ---
    for tid, t in sorted(tasks.items()):
        status = t["status"]
        marker = os.path.exists(_done_marker(tid))

        if status in PRIMARY_DONE_STATES and not marker:
            items.append(("warning", "done-missing-marker", tid,
                          "Задача done, но нет queues/done/%s.done.md" % tid,
                          ["tasks/%s.md" % tid, "queues/done/"]))
        if marker and status in ACTIVE_STATES:
            items.append(("error", "marker-but-not-done", tid,
                          "Есть done-marker, но задача всё ещё '%s' — риск двойного выполнения" % status,
                          ["tasks/%s.md" % tid, "queues/done/%s.done.md" % tid]))

        if status == "doing":
            cp = P.claim_path(tid)
            if not os.path.exists(cp):
                items.append(("warning", "doing-no-claim", tid,
                              "Задача doing, но нет активного claim — операционно «осиротевшая»",
                              ["tasks/%s.md" % tid, "queues/claimed/"]))
            elif not P.claim_is_fresh(tid):
                items.append(("warning", "doing-stale-claim", tid,
                              "Задача doing, но claim протух (lease истёк)",
                              ["tasks/%s.md" % tid, "queues/claimed/%s.claim.md" % tid]))

        if status == "todo" and P.is_placeholder_task(t):
            items.append(("info", "placeholder-todo", tid,
                          "Placeholder-задача (зарезервировано) видна как todo — заполнить или явно припарковать",
                          ["tasks/%s.md" % tid]))

    # --- осиротевшие маркеры/claim ---
    for tid in sorted(_ids_from_dir(DONE, ".done.md")):
        if tid not in tasks:
            items.append(("warning", "orphan-done-marker", tid,
                          "Есть done-marker, но нет tasks/%s.md" % tid,
                          ["queues/done/%s.done.md" % tid]))

    for tid in sorted(_ids_from_dir(CLAIMED, ".claim.md")):
        if tid not in tasks:
            items.append(("warning", "orphan-claim", tid,
                          "Есть claim, но нет tasks/%s.md" % tid,
                          ["queues/claimed/%s.claim.md" % tid]))
        elif tasks[tid]["status"] != "doing":
            sev = "warning" if P.claim_is_fresh(tid) else "info"
            items.append((sev, "claim-without-doing", tid,
                          "Есть claim, но задача в статусе '%s', не doing" % tasks[tid]["status"],
                          ["tasks/%s.md" % tid, "queues/claimed/%s.claim.md" % tid]))
    return tasks


def check_index(items, tasks):
    """index.json.tasks[].status должен совпадать с tasks/*.md (защищённо)."""
    try:
        with open(INDEX_JSON, encoding="utf-8") as f:
            data = json.load(f)
        idx = data.get("tasks") if isinstance(data, dict) else None
        if not isinstance(idx, list):
            return
    except Exception:
        items.append(("info", "index-unreadable", "-",
                      "index.json не прочитан/нет tasks[] — пропускаю сверку индекса",
                      ["index.json"]))
        return
    for it in idx:
        if not isinstance(it, dict):
            continue
        tid = it.get("id")
        ist = it.get("status")
        if tid in tasks and ist is not None and ist != tasks[tid]["status"]:
            items.append(("warning", "index-status-drift", tid,
                          "index.json: status '%s' != tasks/%s.md: '%s'" % (ist, tid, tasks[tid]["status"]),
                          ["index.json", "tasks/%s.md" % tid]))


def check_pipeline(items):
    """logs/pipeline.json должен быть вычислим из tasks+claims (защищённо)."""
    try:
        with open(PIPELINE_JSON, encoding="utf-8") as f:
            saved = json.load(f)
    except Exception:
        items.append(("info", "pipeline-json-missing", "-",
                      "logs/pipeline.json не прочитан — пропускаю сверку снимка конвейера",
                      ["logs/pipeline.json"]))
        return
    recomputed = P.build_pipeline_state()
    for key in ("doing", "ready", "blocked"):
        a = {x.get("id") for x in (saved.get(key) or []) if isinstance(x, dict)}
        b = {x.get("id") for x in (recomputed.get(key) or [])}
        if a != b:
            only_saved = ", ".join(sorted(a - b)) or "—"
            only_now = ", ".join(sorted(b - a)) or "—"
            items.append(("warning", "pipeline-snapshot-drift", "-",
                          "PIPELINE/%s разошёлся: только в снимке [%s], только сейчас [%s] — запусти snapshot"
                          % (key, only_saved, only_now),
                          ["logs/pipeline.json", "PIPELINE.md"]))


def reconcile():
    items = []
    tasks = check_tasks(items)
    check_index(items, tasks)
    check_pipeline(items)
    sev_rank = {"error": 2, "warning": 1, "info": 0}
    worst = max([sev_rank[i[0]] for i in items], default=-1)
    status = "ok" if worst < 0 else ("error" if worst == 2 else ("warning" if worst == 1 else "info"))
    report = {
        "epoch": int(time.time()),
        "status": status,
        "counts": {
            "error": sum(1 for i in items if i[0] == "error"),
            "warning": sum(1 for i in items if i[0] == "warning"),
            "info": sum(1 for i in items if i[0] == "info"),
        },
        "items": [
            {"severity": s, "code": c, "task": t, "message": m, "sources": src}
            for (s, c, t, m, src) in items
        ],
    }
    return report


def render_md(report):
    lines = [
        "# Reconcile report",
        "",
        "Время (epoch): %d" % report["epoch"],
        "",
        "Статус: **%s** (error=%d, warning=%d, info=%d)" % (
            report["status"], report["counts"]["error"],
            report["counts"]["warning"], report["counts"]["info"]),
        "",
        "| Severity | Code | Task | Message |",
        "|---|---|---|---|",
    ]
    if not report["items"]:
        lines.append("| — | — | — | расхождений не найдено |")
    for it in report["items"]:
        lines.append("| %s | %s | %s | %s |" % (
            it["severity"], it["code"], it["task"], it["message"].replace("|", "/")))
    lines.append("")
    return "\n".join(lines)


def write_reports(report):
    os.makedirs(OUTBOX, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(report["epoch"]))
    jpath = os.path.join(OUTBOX, "reconcile-%s.json" % stamp)
    mpath = os.path.join(OUTBOX, "reconcile-%s.md" % stamp)
    with open(jpath, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(mpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(report))
    return jpath, mpath


def print_summary(report, wrote=None):
    print("RECONCILE status=%s error=%d warning=%d info=%d" % (
        report["status"], report["counts"]["error"],
        report["counts"]["warning"], report["counts"]["info"]))
    for it in report["items"]:
        print("  [%s] %s %s — %s" % (it["severity"], it["code"], it["task"], it["message"]))
    if wrote:
        print("Отчёт: %s" % ", ".join(os.path.relpath(p, ROOT) for p in wrote))


def exit_code(report):
    if report["counts"]["error"]:
        return 2
    if report["counts"]["warning"]:
        return 1
    return 0


# Производные коды, которые fix МОЖЕТ безопасно перегенерировать (детерминированно из primary).
# Всё остальное (маркеры/claims/статусы задач) — PRIMARY, его fix НИКОГДА не трогает.
DERIVED_CODES = {"index-status-drift", "pipeline-snapshot-drift"}
_REGEN = {
    "index-status-drift": ("index.json/навигация", ["generate.py"]),
    "pipeline-snapshot-drift": ("PIPELINE.md/logs/pipeline.json", ["pipeline.py", "snapshot"]),
}


def _partition_fix(report):
    """Разделить находки на derived (авто-чинимые) и primary (отказ; severity error/warning)."""
    derived = [it for it in report["items"] if it["code"] in DERIVED_CODES]
    primary = [it for it in report["items"]
               if it["code"] not in DERIVED_CODES and it["severity"] in ("error", "warning")]
    return derived, primary


def _regen(cmd_tail):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", cmd_tail[0]), *cmd_tail[1:]],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL)
    return p.returncode


def cmd_fix(apply=False):
    """Починить ТОЛЬКО производный дрейф (index/snapshot); dry-run по умолчанию, запись лишь при --apply.

    Source of truth (tasks/*.md, queues/*) не трогается никогда; primary-дрейф — ручные action items.
    Идемпотентно: регенерация детерминирована из primary, повтор на чистом дереве — no-op.
    """
    report = reconcile()
    derived, primary = _partition_fix(report)
    print("RECONCILE FIX (%s)" % ("apply" if apply else "dry-run"))
    codes = sorted({it["code"] for it in derived})
    if not derived:
        print("  производного дрейфа нет — регенерировать нечего.")
    elif not apply:
        print("  would regenerate (dry-run, ничего не пишу):")
        for code in codes:
            print("    - %s (по %d находкам '%s') — запусти с --apply" %
                  (_REGEN[code][0], sum(1 for it in derived if it["code"] == code), code))
    else:
        for code in codes:
            label, tail = _REGEN[code]
            rc = _regen(tail)
            print("  регенерировал %s → rc=%d" % (label, rc))
        report = reconcile()  # перепроверка: производный дрейф должен очиститься
        derived2, primary = _partition_fix(report)
        print("  после регенерации: производного дрейфа осталось %d" % len(derived2))
    if primary:
        print("  ОТКАЗ авто-чинить PRIMARY-дрейф (%d) — источник истины не трогаем, это ручные action items:"
              % len(primary))
        for it in primary:
            print("    [%s] %s %s — %s" % (it["severity"], it["code"], it["task"], it["message"]))
    return exit_code(report)


def main():
    help_guard(HELP, sys.argv[1:])
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "fix":
        return cmd_fix(apply="--apply" in sys.argv[2:])
    report = reconcile()
    wrote = None
    if cmd != "check":          # check печатает, но не пишет; report/default/прочее — пишут
        wrote = write_reports(report)
    print_summary(report, wrote)
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
