"""fold.py — fold-not-delete для grow-only сторов (контр-инвариант C-II формулы defect-class-formula).

§C-II: durability(шаг2)+minority(шаг7) дают МОНОТОННЫЙ рост стора → деградация (как metrics давится на росте).
Противовес: старые элементы СВОРАЧИВАТЬ в summary+указатель, НЕ удаляя полезную нагрузку. Удаление данных
по-прежнему запрещено; развёрнутое хранение — нет. Дефолт-применение: свернуть старые `failed`-тикеты
commit_queue (queues/commit-queue/*.json), оставив `.patch` как durable-указатель (recover по сводке).

Read-only (dry-run) по умолчанию; `--apply` выполняет свёртку.

CLI:
  python tools/fold.py commit-queue [--older-days 7]            # dry-run: что свернётся
  python tools/fold.py commit-queue --older-days 7 --apply      # свернуть
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import time
import json
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)


def plan_fold(items, should_fold):
    """items=[(key, dict)] → (kept_keys, foldable_items). Чистая (тестируема без диска)."""
    kept, foldable = [], []
    for key, d in items:
        (foldable if should_fold(d) else kept).append((key, d))
    return [k for k, _ in kept], foldable


def _age_days(epoch):
    try:
        return (int(time.time()) - int(epoch)) / 86400.0
    except (ValueError, TypeError):
        return 0.0


def cq_should_fold(d, older_days):
    """failed-тикет старше порога = сворачиваемый (done уже удаляются; queued/active живые)."""
    return d.get("status") == "failed" and _age_days(d.get("created_epoch", 0)) >= older_days


def cq_summarize(d):
    return {"id": d.get("id"), "agent": d.get("agent"), "status": "failed",
            "reason": d.get("reason", ""), "created_epoch": d.get("created_epoch"),
            "has_patch": bool(d.get("has_patch"))}


def fold_commit_queue(root=None, older_days=7, apply=False):
    """Свернуть старые failed-тикеты commit_queue. Возвращает сводку. .patch НЕ удаляется (указатель)."""
    root = root or ROOT
    qdir = os.path.join(root, "queues", "commit-queue")
    items = []
    for p in sorted(glob.glob(os.path.join(qdir, "*.json"))):
        if os.path.basename(p).startswith("_"):          # пропустить _folded.jsonl
            continue
        try:
            items.append((p, json.load(open(p, encoding="utf-8"))))
        except Exception:
            continue
    _kept, foldable = plan_fold(items, lambda d: cq_should_fold(d, older_days))
    summaries = [cq_summarize(d) for _p, d in foldable]
    if not apply:
        return {"store": qdir, "foldable": len(foldable), "summaries": summaries, "applied": False}
    if foldable:
        with open(os.path.join(qdir, "_folded.jsonl"), "a", encoding="utf-8", newline="\n") as fh:
            for (p, d), s in zip(foldable, summaries):
                fh.write(json.dumps(s, ensure_ascii=False) + "\n")
                try:
                    os.remove(p)                          # удаляем ВЕРБОЗНЫЙ .json; .patch-указатель СОХРАНЯЕМ
                except OSError:
                    pass
    return {"store": qdir, "foldable": len(foldable), "applied": True,
            "summary_file": os.path.join(qdir, "_folded.jsonl")}


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    older = int(args[args.index("--older-days") + 1]) if "--older-days" in args else (
        int(argv[argv.index("--older-days") + 1]) if "--older-days" in argv else 7)
    apply = "--apply" in argv
    if not args or args[0] != "commit-queue":
        print("fold: использование: fold.py commit-queue [--older-days N] [--apply]"); return 2
    r = fold_commit_queue(older_days=older, apply=apply)
    print("=== FOLD (fold-not-delete, C-II) · %s ===" % r["store"])
    if r["applied"]:
        print("  ✓ свёрнуто %d failed-тикет(ов) → %s (.patch-указатели сохранены, данные не потеряны)" % (
            r["foldable"], os.path.basename(r["summary_file"])))
    else:
        print("  dry-run: к свёртке %d failed-тикет(ов) старше %dд (--apply чтобы свернуть):" % (r["foldable"], older))
        for s in r["summaries"][:10]:
            print("    ✗ %s '%s' %s%s" % (s["id"], s["agent"], s["reason"][:30],
                                          " · 💾patch" if s["has_patch"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
