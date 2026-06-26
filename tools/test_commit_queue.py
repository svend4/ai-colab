"""Тест commit_queue.py — FIFO-позиции · голова-берёт-лок · предсохранение+recover · fail · видимость .git/index.lock · path-safety."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
ROOT = os.path.join(REPO_ROOT, "tmp-work", "commit_queue_test_%d_%d" % (os.getpid(), time.time_ns()))
os.makedirs(os.path.join(ROOT, "queues"), exist_ok=True)
os.environ["COLLAB_ROOT"] = ROOT  # ДО импорта: и commit_queue, и commit_lock возьмут этот ROOT

sys.path.insert(0, HERE)
import commit_queue as cq
import commit_lock as cl

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def run():
    fails = []
    try:
        a = cq.enqueue("alice", intent="commit A", epoch=100)
        b = cq.enqueue("bob", intent="commit B", epoch=200)

        # FIFO позиции
        if cq.position(a["id"]) != 1 or cq.position(b["id"]) != 2:
            fails.append("FIFO: a=1,b=2; got %d,%d" % (cq.position(a["id"]), cq.position(b["id"])))

        # bob не голова → ждёт; фидбек несёт ПОЗИЦИЮ (не «занято»)
        ready, msg = cq.turn("bob", b["id"])
        if ready or "позиция" not in msg:
            fails.append("bob не голова → ждёт с позицией: %s" % msg[:60])

        # alice голова → берёт commit-lock, тикет → active
        ready, msg = cq.turn("alice", a["id"])
        if not ready:
            fails.append("alice голова → turn True: %s" % msg[:60])
        if (cl._read() or {}).get("agent") != "alice":
            fails.append("commit-lock должен держать alice")
        if cq._get(a["id"])["status"] != "active":
            fails.append("тикет alice → active")

        # alice повторно → остаётся её очередь (не падаем, не пере-берём)
        if not cq.turn("alice", a["id"])[0]:
            fails.append("alice active → turn остаётся True")

        # done(alice): лок свободен, тикет удалён, bob становится головой
        cq.done("alice", a["id"])
        if cl._read() is not None:
            fails.append("после done commit-lock свободен")
        if cq._get(a["id"]) is not None:
            fails.append("тикет alice удалён после done")
        if cq.position(b["id"]) != 1:
            fails.append("bob теперь голова (позиция 1)")
        if not cq.turn("bob", b["id"])[0]:
            fails.append("bob теперь берёт лок")
        cq.done("bob", b["id"])

        # ТЕМПОРАЛЬНОЕ предсохранение + recover
        c = cq.enqueue("carol", intent="WIP", staged_diff="diff --git a b\n+пример строки\n", epoch=300)
        if not os.path.exists(cq._patch_path(c["id"])):
            fails.append("предсохранение .patch должно существовать")
        if not any(t["id"] == c["id"] for t in cq.recover()):
            fails.append("recover должен показать предсохранённый тикет")

        # fail: отпускает лок, тикет → failed, предсохранение СОХРАНЯЕТСЯ
        cq.turn("carol", c["id"])  # голова → active (берёт лок)
        cq.fail("carol", c["id"], reason="гейт red")
        if cq._get(c["id"])["status"] != "failed":
            fails.append("fail → status failed")
        if not os.path.exists(cq._patch_path(c["id"])):
            fails.append("fail сохраняет предсохранение для recover")
        if cl._read() is not None:
            fails.append("fail отпускает commit-lock")
        if c["id"] not in [t["id"] for t in cq.recover()]:
            fails.append("failed-тикет с patch виден в recover")

        # видимость РЕАЛЬНОГО .git/index.lock (немая коллизия → информативно)
        os.makedirs(os.path.join(ROOT, ".git"), exist_ok=True)
        open(os.path.join(ROOT, ".git", "index.lock"), "w", encoding="utf-8").write("")
        if not cq.git_index_lock_info().get("exists"):
            fails.append("git_index_lock_info должен видеть .git/index.lock")
        if "index.lock ЗАНЯТ" not in cq.board_text():
            fails.append("board должен показывать занятый .git/index.lock")

        # ticket id из CLI не должен превращаться в путь за пределами queues/commit-queue
        bad = "..\\outside"
        ready, msg = cq.turn("mallory", bad)
        if ready or "некорректный ticket id" not in msg:
            fails.append("turn должен отвергать path-like ticket id: %s" % msg)
        msg = cq.done("mallory", bad)
        if "некорректный ticket id" not in msg:
            fails.append("done должен отвергать path-like ticket id: %s" % msg)

        if fails:
            print("FAIL test_commit_queue:")
            for f in fails:
                print("  -", f)
            return 1
        print("OK test_commit_queue: FIFO-позиции · голова-берёт-лок · фидбек-с-позицией · предсохранение+recover · fail · .git/index.lock-видимость · ticket path-safety")
        return 0
    finally:
        pass


if __name__ == "__main__":
    sys.exit(run())
