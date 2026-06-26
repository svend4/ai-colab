"""Тест fold.py — plan_fold(чистая) · cq_should_fold(failed+старый) · apply(json↓, .patch сохранён, queued цел)."""
import os
import sys
import time
import json

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fold

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []
    now = int(time.time())

    # 1) plan_fold (чистая)
    items = [("a", {"x": 1}), ("b", {"x": 2}), ("c", {"x": 3})]
    kept, foldable = fold.plan_fold(items, lambda d: d["x"] >= 2)
    if kept != ["a"] or [k for k, _ in foldable] != ["b", "c"]:
        fails.append("plan_fold: kept=[a], foldable=[b,c]: %s / %s" % (kept, [k for k, _ in foldable]))

    # 2) cq_should_fold: failed+старый → True; queued → False; failed+свежий → False
    if not fold.cq_should_fold({"status": "failed", "created_epoch": now - 10 * 86400}, 7):
        fails.append("старый failed → сворачиваемый")
    if fold.cq_should_fold({"status": "queued", "created_epoch": now - 99 * 86400}, 7):
        fails.append("queued НЕ сворачивать (живой)")
    if fold.cq_should_fold({"status": "failed", "created_epoch": now - 1 * 86400}, 7):
        fails.append("свежий failed НЕ сворачивать")

    # 3) apply на временном сторе
    root = os.path.join(REPO_ROOT, "tmp-work", "fold_test_%d_%d" % (os.getpid(), time.time_ns()))
    qdir = os.path.join(root, "queues", "commit-queue")
    os.makedirs(qdir, exist_ok=True)

    def w(tid, status, epoch, patch=False, reason=""):
        json.dump({"id": tid, "agent": "a", "status": status, "created_epoch": epoch,
                   "has_patch": patch, "reason": reason},
                  open(os.path.join(qdir, tid + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
        if patch:
            open(os.path.join(qdir, tid + ".patch"), "w", encoding="utf-8").write("diff payload")

    w("100-aaaaaaaaaaaa", "failed", now - 10 * 86400, patch=True, reason="гейт red")  # свернётся
    w("200-bbbbbbbbbbbb", "failed", now - 1 * 86400, patch=True)                       # свежий — нет
    w("300-cccccccccccc", "queued", now - 99 * 86400)                                  # живой — нет

    dry = fold.fold_commit_queue(root=root, older_days=7, apply=False)
    if dry["foldable"] != 1 or dry["applied"]:
        fails.append("dry-run: 1 сворачиваемый, applied=False: %s" % {k: dry[k] for k in ("foldable", "applied")})

    res = fold.fold_commit_queue(root=root, older_days=7, apply=True)
    if not res["applied"] or res["foldable"] != 1:
        fails.append("apply: 1 свёрнут: %s" % res)
    # вербозный .json старого failed удалён, но .patch (указатель) СОХРАНЁН
    if os.path.exists(os.path.join(qdir, "100-aaaaaaaaaaaa.json")):
        fails.append("свёрнутый .json должен быть удалён")
    if not os.path.exists(os.path.join(qdir, "100-aaaaaaaaaaaa.patch")):
        fails.append("C-II: .patch (payload-указатель) НЕ должен удаляться — данные не теряем")
    # queued и свежий failed целы
    if not os.path.exists(os.path.join(qdir, "300-cccccccccccc.json")):
        fails.append("queued (живой) не трогать")
    if not os.path.exists(os.path.join(qdir, "200-bbbbbbbbbbbb.json")):
        fails.append("свежий failed не трогать")
    # сводка записана
    sp = os.path.join(qdir, "_folded.jsonl")
    if not os.path.exists(sp) or "100-aaaaaaaaaaaa" not in open(sp, encoding="utf-8").read():
        fails.append("_folded.jsonl должен нести сводку свёрнутого")

    if fails:
        print("FAIL test_fold:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_fold: plan_fold(чистая) · cq_should_fold(failed+старый) · apply(json удалён, .patch сохранён, queued/свежий целы, сводка)")


if __name__ == "__main__":
    main()
