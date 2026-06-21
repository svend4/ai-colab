#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты конкурентных гарантий pipeline (T-082, ревью T-078 находки H/I):

  1. fencing в done: чужой/протухший claim_id отклоняется, верный — проходит,
     без claim_id — backward-compatible (как раньше);
  2. done чужим агентом отклоняется (старое поведение сохранено);
  3. атомарный перехват протухшего claim: N параллельных try_claim → ровно 1 победитель.

Изолированный COLLAB_ROOT во временной папке; pipeline импортируется ПОСЛЕ установки env.
"""
import os
import sys
import tempfile
import shutil
import threading

ROOT = tempfile.mkdtemp(prefix="pl_fence_")
os.environ["COLLAB_ROOT"] = ROOT
for sub in (("tasks",), ("queues", "claimed"), ("queues", "done"), ("queues", "failed")):
    os.makedirs(os.path.join(ROOT, *sub), exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tools/
import pipeline as P


def _make_task(tid):
    path = os.path.join(ROOT, "tasks", "%s.md" % tid)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\nid: %s\ntype: task\ntitle: t\nstatus: todo\nowner: pool\n"
                "priority: normal\nrisk: low\ndepends_on: []\nnext: x\n---\n# t\n" % tid)
    return path


def _seed_stale_claim(tid):
    cp = P.claim_path(tid)
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    with open(cp, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\ntask: %s\nagent: ghost\nclaim_id: oldoldold12\nlease_epoch: 1\n---\n" % tid)


def run():
    ok = True
    try:
        # --- 1. fencing в done ---
        p900 = _make_task("T-900")
        cid = P.try_claim("T-900", "claude")
        assert cid, "claim не выдан"
        P.set_status(p900, "doing")
        assert P.cmd_done("claude", "T-900", "r", claim_id="deadbeef00") == 1, \
            "done с чужим claim_id должен отклоняться"
        assert P.cmd_done("mavis", "T-900", "r") == 1, \
            "done чужим агентом должен отклоняться"
        assert P.cmd_done("claude", "T-900", "r", claim_id=cid) == 0, \
            "done с верным claim_id должен проходить"
        assert P.collect_tasks()["T-900"]["status"] == "done", "статус не стал done"

        # --- 2. backward-compatible: done без claim_id ---
        p902 = _make_task("T-902")
        cid2 = P.try_claim("T-902", "claude")
        P.set_status(p902, "doing")
        assert P.cmd_done("claude", "T-902", "r") == 0, \
            "done без claim_id должен работать (backward compat)"

        # --- 3. атомарный перехват протухшего claim: ровно 1 победитель ---
        # Гонка флакичная, поэтому гоняем МНОГО раундов: одиночный прогон её прятал
        # (ровно так баг двойного захвата дожил до перепроверки T-084).
        rounds = 16
        for rnd in range(rounds):
            # очистить возможные lock/tmp хвосты и пере-засеять протухший claim
            cp = P.claim_path("T-901")
            d = os.path.dirname(cp)
            for fn in os.listdir(d):
                if fn.startswith("T-901.claim.md."):  # .take.* / .tmp.*
                    try:
                        os.remove(os.path.join(d, fn))
                    except OSError:
                        pass
            _seed_stale_claim("T-901")
            results = []
            rlock = threading.Lock()

            def worker():
                r = P.try_claim("T-901", "claude")
                with rlock:
                    results.append(r)

            threads = [threading.Thread(target=worker) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            winners = [r for r in results if r]
            assert len(winners) == 1, \
                "раунд %d: перехват протухшего claim: победителей %d (ожидался 1): %s" \
                % (rnd, len(winners), results)
            assert P.claim_is_fresh("T-901"), "раунд %d: после перехвата claim должен быть свежим" % rnd

        print("TESTS OK fencing+takeover: %d раундов по 8 потоков → ровно 1 победитель; done-fencing ok"
              % rounds)
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(ROOT, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
