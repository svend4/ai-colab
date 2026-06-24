#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_pipeline_fencing
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_pipeline_fencing.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Тесты конкурентных гарантий pipeline (T-082, ревью T-078 находки H/I):

  1. fencing в done: чужой/протухший claim_id отклоняется, верный — проходит,
     optional applied evidence пишется в done-маркер,
     без claim_id — отклоняется как нарушение fencing;
  2. done чужим агентом отклоняется (старое поведение сохранено);
  3. атомарный перехват протухшего claim: N параллельных try_claim → ровно 1 победитель;
  4. applied-warning: служебная задача без --applied получает WARN, обычная нет;
  5. targeted claim: success/busy/not-ready/placeholder без wrong-next.

Изолированный COLLAB_ROOT во временной папке; pipeline импортируется ПОСЛЕ установки env.
"""
import os
import sys
import shutil
import threading
import contextlib
import io

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, os.path.join(REPO_ROOT, "drivers"))
from test_tmp import make_temp_dir

ROOT = make_temp_dir("pl_fence_")
os.environ["COLLAB_ROOT"] = ROOT
for sub in (("tasks",), ("queues", "claimed"), ("queues", "done"), ("queues", "failed")):
    os.makedirs(os.path.join(ROOT, *sub), exist_ok=True)

sys.path.insert(0, TOOLS)  # tools/
import pipeline as P


def _make_task(tid, status="todo", title="t", deps="[]", topic=""):
    path = os.path.join(ROOT, "tasks", "%s.md" % tid)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\nid: %s\ntype: task\ntitle: %s\nstatus: %s\nowner: pool\n"
                "priority: normal\nrisk: low\ntopic: %s\ndepends_on: %s\nnext: x\n---\n# t\n"
                % (tid, title, status, topic, deps))
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
        assert P.cmd_done("claude", "T-900", "r", claim_id=cid, applied="AGENTS.md, PROTOCOL.md") == 0, \
            "done с верным claim_id должен проходить"
        assert P.collect_tasks()["T-900"]["status"] == "done", "статус не стал done"
        with open(os.path.join(P.DONE, "T-900.done.md"), "r", encoding="utf-8") as f:
            done_text = f.read()
        assert "applied: AGENTS.md, PROTOCOL.md" in done_text, done_text
        assert "Applied instructions: AGENTS.md, PROTOCOL.md" in done_text, done_text

        # --- 2. strict fencing: done без claim_id отклоняется ---
        p902 = _make_task("T-902")
        cid2 = P.try_claim("T-902", "claude")
        assert cid2, "missing-claim setup claim не выдан"
        P.set_status(p902, "doing")
        missing_claim_done = io.StringIO()
        with contextlib.redirect_stdout(missing_claim_done):
            assert P.cmd_done("claude", "T-902", "r") == 1, \
                "done без claim_id должен отклоняться"
        assert "требуется указать --claim ID" in missing_claim_done.getvalue(), missing_claim_done.getvalue()
        assert P.collect_tasks()["T-902"]["status"] == "doing", "missing claim не должен ставить done"

        # --- 3. applied-warning для служебных задач ---
        p908 = _make_task("T-908", topic="docs/instruction-assurance.md")
        cid3 = P.try_claim("T-908", "codex")
        assert cid3, "service warning setup claim не выдан"
        P.set_status(p908, "doing")
        service_done = io.StringIO()
        with contextlib.redirect_stdout(service_done):
            assert P.cmd_done("codex", "T-908", "r", claim_id=cid3) == 0, \
                "служебная задача без --applied должна закрываться мягко"
        assert "WARN: T-908" in service_done.getvalue(), service_done.getvalue()

        # --- 3b. strict applied-evidence gate (opt-in; дефолт остаётся мягким) ---
        # без evidence + --strict => ОТКАЗ, задача НЕ закрывается
        p909 = _make_task("T-909", topic="tools/x.py")
        cid9 = P.try_claim("T-909", "codex")
        P.set_status(p909, "doing")
        sf_fail = io.StringIO()
        with contextlib.redirect_stdout(sf_fail):
            assert P.cmd_done("codex", "T-909", "r", claim_id=cid9, strict=True) == 1, \
                "strict: служебная задача без applied должна ОТКЛОНЯТЬСЯ"
        assert "ОТКАЗ: T-909" in sf_fail.getvalue(), sf_fail.getvalue()
        assert P.collect_tasks()["T-909"]["status"] != "done", "strict-отказ не должен ставить done"

        # полноценное (task-specific) evidence + --strict => проходит
        p910 = _make_task("T-910", topic="tools/x.py")
        cid10 = P.try_claim("T-910", "codex")
        P.set_status(p910, "doing")
        assert P.cmd_done("codex", "T-910", "r", claim_id=cid10,
                          applied="AGENTS.md, PROTOCOL.md, tools/x.py, Checks", strict=True) == 0, \
            "strict: полноценное evidence должно проходить"
        assert P.collect_tasks()["T-910"]["status"] == "done", "strict+evidence должно ставить done"

        # boilerplate-only evidence + --strict => ОТКАЗ (формальный отчёт не проходит)
        p911 = _make_task("T-911", topic="tools/x.py")
        cid11 = P.try_claim("T-911", "codex")
        P.set_status(p911, "doing")
        sf_boiler = io.StringIO()
        with contextlib.redirect_stdout(sf_boiler):
            assert P.cmd_done("codex", "T-911", "r", claim_id=cid11,
                              applied="AGENTS.md, PROTOCOL.md, Checks", strict=True) == 1, \
                "strict: формальное boilerplate evidence должно отклоняться"
        assert "ОТКАЗ: T-911" in sf_boiler.getvalue(), sf_boiler.getvalue()
        assert P.collect_tasks()["T-911"]["status"] != "done", "strict boilerplate-отказ не должен ставить done"

        # тот же boilerplate БЕЗ --strict => мягко проходит (дефолт не сломан)
        p912 = _make_task("T-912", topic="tools/x.py")
        cid12 = P.try_claim("T-912", "codex")
        P.set_status(p912, "doing")
        assert P.cmd_done("codex", "T-912", "r", claim_id=cid12,
                          applied="AGENTS.md, PROTOCOL.md, Checks") == 0, \
            "без --strict формальное evidence закрывает задачу (backward-compat)"
        assert P.collect_tasks()["T-912"]["status"] == "done", "не-strict должен ставить done"

        # --- 4. атомарный перехват протухшего claim: ровно 1 победитель ---
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
            errors = []
            rlock = threading.Lock()

            def worker():
                try:
                    r = P.try_claim("T-901", "claude")
                except Exception as exc:
                    with rlock:
                        errors.append(repr(exc))
                    return
                with rlock:
                    results.append(r)

            threads = [threading.Thread(target=worker) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert not errors, "раунд %d: try_claim не должен выбрасывать исключения из worker: %s" % (rnd, errors)
            winners = [r for r in results if r]
            assert len(winners) == 1, \
                "раунд %d: перехват протухшего claim: победителей %d (ожидался 1): %s" \
                % (rnd, len(winners), results)
            assert P.claim_is_fresh("T-901"), "раунд %d: после перехвата claim должен быть свежим" % rnd

        # --- 5. targeted claim: success/busy/not-ready/placeholder ---
        _make_task("T-903")
        assert P.cmd_claim("codex", "T-903") == 0, "targeted claim ready должен проходить"
        h = P.claim_holder("T-903") or {}
        assert h.get("agent") == "codex" and h.get("claim_id"), h
        assert P.collect_tasks()["T-903"]["status"] == "doing", "targeted claim должен ставить doing"

        _make_task("T-904")
        busy_cid = P.try_claim("T-904", "claude")
        assert busy_cid, "busy setup claim не выдан"
        assert P.cmd_claim("codex", "T-904") == 1, "targeted claim занятой задачи должен отклоняться"
        assert (P.claim_holder("T-904") or {}).get("agent") == "claude", "чужой claim не должен перезаписываться"
        assert P.collect_tasks()["T-904"]["status"] == "todo", "busy targeted claim не должен менять status"

        _make_task("T-905", deps="[T-999]")
        assert P.cmd_claim("codex", "T-905") == 1, "targeted claim с незакрытой зависимостью должен отклоняться"
        assert not P.claim_holder("T-905"), "not-ready dependency не должен создавать claim"

        _make_task("T-906", title="(зарезервировано — заполните)")
        assert P.cmd_claim("codex", "T-906") == 1, "placeholder не должен claim-иться"
        assert not P.claim_holder("T-906"), "placeholder не должен создавать claim"

        _make_task("T-907", status="done")
        assert P.cmd_claim("codex", "T-907") == 1, "done задача не должна claim-иться"
        assert not P.claim_holder("T-907"), "done задача не должна создавать claim"

        assert P.cmd_claim("codex", "T-999") == 1, "missing task должен отклоняться"

        print("TESTS OK fencing+takeover+targeted-claim: %d раундов по 8 потоков; done-fencing ok; missing-claim rejection ok; applied-warning ok; claim success/busy/not-ready/placeholder ok"
              % rounds)
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(ROOT, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
