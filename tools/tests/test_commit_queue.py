"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_commit_queue
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_commit_queue.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест commit_queue.py — FIFO-позиции · голова-берёт-лок · предсохранение+recover · fail · видимость .git/index.lock · path-safety · битый-тикет-в-карантин · мусорный --ratio (аудит C37)."""
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
import time
import io
import contextlib

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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
        open(os.path.join(ROOT, ".git", "index.lock"), "w", encoding="utf-8", newline="\n").write("")
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

        # битый JSON-тикет НЕ исчезает молча (аудит C37): WARN в stderr + карантин corrupt/
        bad_name = "999-deadbeefdead.json"
        bad_path = os.path.join(cq.QDIR, bad_name)
        with open(bad_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{битый json")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ids = [t["id"] for t in cq._load_all()]
        if "999-deadbeefdead" in ids:
            fails.append("битый тикет не должен попадать в очередь")
        if "WARN commit_queue" not in err.getvalue() or bad_name not in err.getvalue():
            fails.append("битый тикет должен давать WARN с именем файла: %r" % err.getvalue()[:160])
        if os.path.exists(bad_path):
            fails.append("битый тикет должен быть перенесён из очереди (не оставаться в QDIR)")
        if not os.path.exists(os.path.join(cq.QDIR, "corrupt", bad_name)):
            fails.append("битый тикет должен лежать в queues/commit-queue/corrupt/ (след остаётся)")

        # мусорный --ratio в pipeline.cmd_next → ошибка + rc=2, валидный — работает (аудит C37)
        import pipeline as pl
        out_bad, out_ok = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_bad):
            rc_bad = pl.cmd_next("tester", ratio="code;0.7")
        with contextlib.redirect_stdout(out_ok):
            rc_ok = pl.cmd_next("tester", ratio="code:7,docs:3")
        if rc_bad != 2 or "ОШИБКА" not in out_bad.getvalue():
            fails.append("мусорный --ratio должен давать rc=2 и ОШИБКА (rc=%r, out=%r)"
                         % (rc_bad, out_bad.getvalue()[:120]))
        if rc_ok != 0:
            fails.append("валидный --ratio должен работать без ошибки (rc=%r)" % rc_ok)

        if fails:
            print("FAIL test_commit_queue:")
            for f in fails:
                print("  -", f)
            return 1
        print("OK test_commit_queue: FIFO-позиции · голова-берёт-лок · фидбек-с-позицией · предсохранение+recover · fail · .git/index.lock-видимость · ticket path-safety · битый-тикет(WARN+corrupt/) · --ratio(мусор→rc=2)")
        return 0
    finally:
        pass


if __name__ == "__main__":
    sys.exit(run())
