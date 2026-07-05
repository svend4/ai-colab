#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_claims
# TYPE: active-script
# DOMAIN: core.orchestration
# DEPTH_LEVEL: 1
# SUMMARY: Тесты общих claim-примитивов _claims.py: атомарность, takeover, fencing, кросс-чтение pipeline↔agent_queue.
# ==========================================
"""
Тесты общих claim-примитивов `_claims.py` (волна 2, C35-a; самопроверено):

  1. read/fresh: отсутствующий файл, мусорный lease_epoch, валидный claim;
  2. атомарность create_claim: N параллельных потоков → ровно один победитель;
  3. takeover по протухшему lease: одиночный перехват, поздний писатель со
     старым снимком проигрывает (T-084), чужой takeover-lock блокирует,
     конкурентный перехват → ровно один победитель, свежий чужой claim
     неприкосновенен, свой свежий продлевается (renew_agent);
  4. release с fencing: чужой agent/claim_id не снимает, верный — снимает;
  5. перекрёстное чтение claim-файла обоими потребителями
     (pipeline ↔ agent_queue): формат не изменился, freshness/fencing
     совместимы в обе стороны, tmp/lock-хвостов не остаётся.

Запуск: python tools/test_claims.py   (или py -3 -m pytest tools/test_claims.py)
"""
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
import shutil
import tempfile
import threading

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)

from _ioutil import configure_output
configure_output()

import _claims


def _tmp():
    return tempfile.mkdtemp(prefix="claims_test_")


def _body(task="T-X", agent="a1", cid="cid001", lease=None):
    """Claim-текст pipeline-формата (task/agent/claim_id/lease_epoch)."""
    if lease is None:
        lease = int(time.time()) + 1800
    return ("---\ntask: %s\nagent: %s\nclaim_id: %s\nlease_epoch: %d\n---\n"
            % (task, agent, cid, lease))


# --- 1. read/fresh ------------------------------------------------------------------


def test_read_and_fresh_basics():
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-1")
        assert p.endswith("T-1.claim.md"), "единый суффикс имени claim-файла"
        # отсутствующий файл
        assert _claims.read_claim(p) is None, "нет файла → None"
        assert _claims.claim_is_fresh(p) is False, "нет файла → не свежий"
        # None/мусор в is_fresh
        assert _claims.is_fresh(None) is False, "None → протух"
        assert _claims.is_fresh({}) is False, "пустой dict → протух"
        assert _claims.is_fresh({"lease_epoch": "мусор"}) is False, "мусорный lease → протух"
        # валидный свежий claim
        _claims.create_claim(p, _body(task="T-1"))
        cur = _claims.read_claim(p)
        assert cur and cur.get("claim_id") == "cid001", "front-matter прочитан"
        assert _claims.is_fresh(cur) and _claims.claim_is_fresh(p), "lease в будущем → свежий"
        # протухший
        p2 = _claims.claim_file(d, "T-2")
        _claims.create_claim(p2, _body(task="T-2", lease=int(time.time()) - 60))
        assert _claims.claim_is_fresh(p2) is False, "lease в прошлом → протух"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- 2. атомарность create_claim ----------------------------------------------------


def test_create_claim_exclusive():
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-3")
        _claims.create_claim(p, _body(task="T-3", cid="first"))
        try:
            _claims.create_claim(p, _body(task="T-3", cid="second"))
            assert False, "повторное создание обязано падать FileExistsError"
        except FileExistsError:
            pass
        assert _claims.read_claim(p).get("claim_id") == "first", \
            "проигравший не должен затирать содержимое"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_create_claim_concurrent_single_winner():
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-4")
        wins, errors = [], []
        rlock = threading.Lock()

        def worker(i):
            try:
                _claims.create_claim(p, _body(task="T-4", cid="cid%03d" % i))
                with rlock:
                    wins.append(i)
            except FileExistsError:
                pass
            except Exception as exc:  # noqa: BLE001 — любой другой сбой — провал теста
                with rlock:
                    errors.append(repr(exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, "create_claim не должен бросать ничего кроме FileExistsError: %s" % errors
        assert len(wins) == 1, "победитель должен быть ровно один: %s" % wins
        assert _claims.read_claim(p).get("claim_id") == "cid%03d" % wins[0], \
            "на диске — claim победителя"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- 3. takeover по протухшему lease -------------------------------------------------


def test_takeover_stale_single():
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-5")
        _claims.create_claim(p, _body(task="T-5", agent="ghost", cid="oldcid", lease=1))
        old = _claims.read_claim(p)
        assert _claims.takeover_claim(p, _body(task="T-5", agent="new", cid="newcid"), old), \
            "одиночный перехват протухшего claim должен проходить"
        cur = _claims.read_claim(p)
        assert cur.get("agent") == "new" and cur.get("claim_id") == "newcid", cur
        assert _claims.claim_is_fresh(p), "после перехвата claim свежий"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_takeover_late_writer_with_stale_snapshot_loses():
    # T-084: оба прочитали ОДИН протухший claim; поздний писатель обязан
    # проиграть перепроверку под lock'ом, а не затереть свежий claim победителя.
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-6")
        _claims.create_claim(p, _body(task="T-6", agent="ghost", cid="oldcid", lease=1))
        old = _claims.read_claim(p)  # общий снимок для A и B
        assert _claims.takeover_claim(p, _body(task="T-6", agent="A", cid="cidA"), old), \
            "первый перехватчик должен победить"
        assert not _claims.takeover_claim(p, _body(task="T-6", agent="B", cid="cidB"), old), \
            "поздний писатель со старым снимком должен проиграть"
        cur = _claims.read_claim(p)
        assert cur.get("agent") == "A" and cur.get("claim_id") == "cidA", \
            "на диске должен остаться claim победителя: %s" % cur
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_takeover_blocked_by_foreign_lock():
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-7")
        _claims.create_claim(p, _body(task="T-7", agent="ghost", cid="lockedcid", lease=1))
        old = _claims.read_claim(p)
        lock = p + ".take.lockedcid"
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        try:
            assert not _claims.takeover_claim(p, _body(task="T-7", agent="B", cid="cidB"), old), \
                "под чужим takeover-lock перехват должен честно отказывать"
            assert _claims.read_claim(p).get("claim_id") == "lockedcid", \
                "старый claim не должен быть затёрт под чужим lock'ом"
        finally:
            os.remove(lock)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_takeover_fresh_claim_rules():
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-8")
        _claims.create_claim(p, _body(task="T-8", agent="a1", cid="freshcid"))
        cur = _claims.read_claim(p)
        # свежий чужой claim неприкосновенен (поведение pipeline: renew_agent=None)
        assert not _claims.takeover_claim(p, _body(task="T-8", agent="a2", cid="x1"), cur), \
            "свежий claim без renew_agent перехватывать нельзя"
        assert not _claims.takeover_claim(p, _body(task="T-8", agent="a2", cid="x2"), cur,
                                          renew_agent="a2"), \
            "свежий ЧУЖОЙ claim нельзя перехватить и с renew_agent"
        # свой свежий claim продлевается (поведение agent_queue: renewal)
        assert _claims.takeover_claim(p, _body(task="T-8", agent="a1", cid="renewed"), cur,
                                      renew_agent="a1"), \
            "продление своего свежего claim должно проходить"
        assert _claims.read_claim(p).get("claim_id") == "renewed", "lease продлён, claim_id ротирован"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_takeover_concurrent_one_winner():
    # Гонка флакичная — гоняем несколько раундов (как в test_pipeline_fencing:
    # одиночный прогон прятал баг двойного захвата до перепроверки T-084).
    d = _tmp()
    try:
        for rnd in range(8):
            p = _claims.claim_file(d, "T-9")
            for fn in os.listdir(d):  # чистка lock/tmp-хвостов раунда
                if fn.startswith("T-9.claim.md."):
                    try:
                        os.remove(os.path.join(d, fn))
                    except OSError:
                        pass
            if os.path.exists(p):
                os.remove(p)
            _claims.create_claim(p, _body(task="T-9", agent="ghost", cid="staleold", lease=1))
            old = _claims.read_claim(p)
            results, errors = [], []
            rlock = threading.Lock()

            def worker(i):
                try:
                    r = _claims.takeover_claim(
                        p, _body(task="T-9", agent="ag%d" % i, cid="cid-%d-%d" % (rnd, i)), old)
                except Exception as exc:  # noqa: BLE001
                    with rlock:
                        errors.append(repr(exc))
                    return
                with rlock:
                    results.append((i, r))

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert not errors, "раунд %d: takeover_claim не должен бросать исключений: %s" % (rnd, errors)
            winners = [i for i, r in results if r]
            assert len(winners) == 1, \
                "раунд %d: победителей %d (ожидался 1): %s" % (rnd, len(winners), results)
            cur = _claims.read_claim(p)
            assert cur.get("agent") == "ag%d" % winners[0], \
                "раунд %d: на диске — claim победителя: %s" % (rnd, cur)
            assert _claims.claim_is_fresh(p), "раунд %d: после перехвата claim свежий" % rnd
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- 4. release с fencing ------------------------------------------------------------


def test_release_with_fencing():
    d = _tmp()
    try:
        p = _claims.claim_file(d, "T-10")
        _claims.create_claim(p, _body(task="T-10", agent="a1", cid="relcid"))
        assert not _claims.release_claim(p, agent="a2"), "чужой agent не должен снимать claim"
        assert not _claims.release_claim(p, agent="a1", claim_id="wrong"), \
            "неверный claim_id (fencing) не должен снимать claim"
        assert os.path.exists(p), "после отказов файл на месте"
        assert _claims.release_claim(p, agent="a1", claim_id="relcid"), \
            "верная пара agent+claim_id снимает claim"
        assert not os.path.exists(p), "claim-файл удалён"
        assert not _claims.release_claim(p), "повторное снятие → False (файла нет)"
        # безусловное снятие (fencing проверен вызывающим, как pipeline._release)
        _claims.create_claim(p, _body(task="T-10", agent="a1", cid="relcid2"))
        assert _claims.release_claim(p), "безусловное снятие работает"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- 5. перекрёстное чтение pipeline ↔ agent_queue -----------------------------------


def test_cross_read_pipeline_and_agent_queue():
    """Оба потребителя читают claim-файлы друг друга: формат не изменился (C35-a)."""
    root = _tmp()
    claimed = os.path.join(root, "queues", "claimed")
    os.makedirs(claimed, exist_ok=True)
    import pipeline
    import agent_queue
    old_claimed, old_q = pipeline.CLAIMED, agent_queue.Q
    pipeline.CLAIMED = claimed
    agent_queue.Q = os.path.join(root, "queues")
    try:
        # --- pipeline пишет → agent_queue читает ---
        cid = pipeline.try_claim("T-CR1", "claude")
        assert cid, "pipeline.try_claim должен выдать claim"
        c = agent_queue.read_claim("T-CR1")
        assert c is not None, "agent_queue обязан прочитать pipeline-claim"
        assert c.get("agent") == "claude" and c.get("claim_id") == cid, c
        assert agent_queue.is_fresh(c), "agent_queue видит pipeline-lease свежим"
        for k in ("task", "agent", "claim_id", "lease_epoch"):
            assert k in c, "формат pipeline-claim не изменился: нет поля %s" % k

        # --- agent_queue пишет (расширенный формат) → pipeline читает ---
        lease = agent_queue.now_epoch() + 600
        d = {
            "task": "T-CR2",
            "agent": "codex",
            "claim_id": agent_queue.token(),
            "claimed_at": agent_queue.human(agent_queue.now_epoch()),
            "lease_until": agent_queue.human(lease),
            "lease_epoch": str(lease),
        }
        assert agent_queue.write_claim("T-CR2", d) is True
        h = pipeline.claim_holder("T-CR2")
        assert h is not None, "pipeline обязан прочитать agent_queue-claim"
        assert h.get("agent") == "codex" and h.get("claim_id") == d["claim_id"], h
        assert pipeline.claim_is_fresh("T-CR2"), "pipeline видит agent_queue-lease свежим"
        assert h.get("lease_until") == d["lease_until"] and h.get("claimed_at") == d["claimed_at"], \
            "доп. поля agent_queue (claimed_at/lease_until) сохранены — формат не менялся"
        # свежий чужой agent_queue-claim pipeline НЕ перехватывает
        assert pipeline.try_claim("T-CR2", "claude") is None, \
            "pipeline не должен перехватывать свежий agent_queue-claim"

        # --- протухший agent_queue-claim pipeline перехватывает атомарно ---
        past = agent_queue.now_epoch() - 3600
        d3 = dict(d, task="T-CR3", claim_id=agent_queue.token(),
                  claimed_at=agent_queue.human(past - 60),
                  lease_until=agent_queue.human(past), lease_epoch=str(past))
        assert agent_queue.write_claim("T-CR3", d3) is True
        cid3 = pipeline.try_claim("T-CR3", "claude")
        assert cid3, "pipeline должен перехватить протухший agent_queue-claim"
        c3 = agent_queue.read_claim("T-CR3")
        assert c3.get("agent") == "claude" and c3.get("claim_id") == cid3, \
            "agent_queue читает перехваченный pipeline-claim: %s" % c3

        # --- хвостов атомарной механики не остаётся ---
        leftovers = [fn for fn in os.listdir(claimed) if ".take." in fn or ".tmp." in fn]
        assert not leftovers, "lock/tmp-хвосты не должны оставаться: %s" % leftovers
    finally:
        pipeline.CLAIMED, agent_queue.Q = old_claimed, old_q
        shutil.rmtree(root, ignore_errors=True)


# --- standalone-запуск ----------------------------------------------------------------


def run():
    ok = True
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        try:
            fn()
            print("OK %s" % fn.__name__)
        except AssertionError as e:
            ok = False
            print("TEST FAIL %s: %s" % (fn.__name__, e))
    if ok:
        print("TESTS OK _claims: %d проверок (create/takeover/release/cross-read)" % len(fns))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
