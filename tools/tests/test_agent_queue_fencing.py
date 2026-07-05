#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_agent_queue_fencing
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_agent_queue_fencing.py. Описание сгенерировано автоматически.
# ==========================================
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
import shutil
import tempfile
import sys
import threading
import unittest

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import agent_queue

class TestAgentQueueFencing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_root = os.environ.get("COLLAB_ROOT")
        os.environ["COLLAB_ROOT"] = self.tmp
        agent_queue.Q = os.path.join(self.tmp, "queues")
        os.makedirs(os.path.join(agent_queue.Q, "inbox"))
        os.makedirs(os.path.join(agent_queue.Q, "claimed"))
        os.makedirs(os.path.join(agent_queue.Q, "done"))
        os.makedirs(os.path.join(agent_queue.Q, "failed"))
        
        self.task = "T-TEST-FENCING"
        with open(agent_queue.inbox_path(self.task), "w", newline="\n") as f:
            f.write("test task inbox")
            
    def tearDown(self):
        shutil.rmtree(self.tmp)
        if self.old_root is not None:
            os.environ["COLLAB_ROOT"] = self.old_root
        else:
            if "COLLAB_ROOT" in os.environ:
                del os.environ["COLLAB_ROOT"]
            
    def test_fencing_protects_against_invalid_claim_id(self):
        class Args: pass
        a = Args()
        a.task = self.task
        a.agent = "agent1"
        a.ttl = 30
        
        # 1. agent1 claims the task
        agent_queue.cmd_claim(a)
        claim = agent_queue.read_claim(self.task)
        self.assertIsNotNone(claim)
        valid_claim_id = claim.get("claim_id")
        
        # 2. agent1 tries to complete with wrong claim_id
        a.claim_id = "wrong_id"
        a.result = "done"
        rc = agent_queue.cmd_complete(a)
        self.assertEqual(rc, 1, "Should fail with wrong claim_id")
        
        # Verify done marker was not created
        done_path = os.path.join(agent_queue.Q, "done", self.task + ".done.md")
        self.assertFalse(os.path.exists(done_path))
        
        # Verify claim still exists
        self.assertTrue(os.path.exists(agent_queue.claim_path(self.task)))
        
        # 3. agent1 completes with correct claim_id
        a.claim_id = valid_claim_id
        rc = agent_queue.cmd_complete(a)
        self.assertEqual(rc, 0, "Should succeed with correct claim_id")
        self.assertTrue(os.path.exists(done_path))
        self.assertFalse(os.path.exists(agent_queue.claim_path(self.task)))

    def test_fencing_protects_against_wrong_agent(self):
        class Args: pass
        a = Args()
        a.task = self.task
        a.agent = "agent1"
        a.ttl = 30
        
        # 1. agent1 claims the task
        agent_queue.cmd_claim(a)
        claim = agent_queue.read_claim(self.task)
        valid_claim_id = claim.get("claim_id")
        
        # 2. agent2 tries to fail the task even with the correct claim_id
        a.agent = "agent2"
        a.claim_id = valid_claim_id
        a.reason = "failing"
        rc = agent_queue.cmd_fail(a)
        self.assertEqual(rc, 1, "Should fail when wrong agent tries to modify")
        
        failed_path = os.path.join(agent_queue.Q, "failed", self.task + ".failed.md")
        self.assertFalse(os.path.exists(failed_path))

    # --- атомарность перехвата протухшего claim (аудит 2026-07-02, C9) ---

    def _write_stale_claim(self, agent="agent-old", claim_id="oldcid0001"):
        # Протухший claim: lease_epoch в прошлом.
        past = agent_queue.now_epoch() - 3600
        d = {
            "task": self.task,
            "agent": agent,
            "claim_id": claim_id,
            "claimed_at": agent_queue.human(past - 60),
            "lease_until": agent_queue.human(past),
            "lease_epoch": str(past),
        }
        pth = agent_queue.claim_path(self.task)
        with open(pth, "w", encoding="utf-8", newline="\n") as f:
            f.write(agent_queue.claim_text(d))
        return d

    def _claim_args(self, agent):
        class Args: pass
        a = Args()
        a.task = self.task
        a.agent = agent
        a.ttl = 30
        return a

    def test_stale_takeover_is_atomic_second_writer_loses(self):
        # Репродукция гонки из аудита (детерминированный интерливинг):
        # оба агента прочитали ОДИН И ТОТ ЖЕ протухший claim, оба пишут.
        # До фикса оба write_claim «успевали» (plain overwrite) — двойной захват;
        # теперь поздний писатель обязан проиграть перепроверку под lock'ом.
        self._write_stale_claim()
        old = agent_queue.read_claim(self.task)  # общий снимок для A и B

        def new_claim(agent):
            cid = agent_queue.token()
            lease = agent_queue.now_epoch() + 30 * 60
            return {
                "task": self.task,
                "agent": agent,
                "claim_id": cid,
                "claimed_at": agent_queue.human(agent_queue.now_epoch()),
                "lease_until": agent_queue.human(lease),
                "lease_epoch": str(lease),
            }

        d_a, d_b = new_claim("agent-A"), new_claim("agent-B")
        self.assertTrue(agent_queue.write_claim(self.task, d_a, old_claim=old),
                        "первый перехватчик должен победить")
        self.assertFalse(agent_queue.write_claim(self.task, d_b, old_claim=old),
                         "поздний писатель со старым снимком должен проиграть")
        cur = agent_queue.read_claim(self.task)
        self.assertEqual(cur.get("agent"), "agent-A",
                         "на диске должен остаться claim победителя")
        self.assertEqual(cur.get("claim_id"), d_a["claim_id"])

    def test_stale_takeover_blocked_by_takeover_lock(self):
        # Пока конкурент держит takeover-lock по тому же старому claim_id —
        # write_claim честно отказывает, а не пишет поверх.
        self._write_stale_claim(claim_id="lockedcid")
        old = agent_queue.read_claim(self.task)
        lock = agent_queue.claim_path(self.task) + ".take.lockedcid"
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        try:
            d = {
                "task": self.task, "agent": "agent-B",
                "claim_id": agent_queue.token(),
                "claimed_at": agent_queue.human(agent_queue.now_epoch()),
                "lease_until": agent_queue.human(agent_queue.now_epoch() + 60),
                "lease_epoch": str(agent_queue.now_epoch() + 60),
            }
            self.assertFalse(agent_queue.write_claim(self.task, d, old_claim=old))
            cur = agent_queue.read_claim(self.task)
            self.assertEqual(cur.get("claim_id"), "lockedcid",
                             "старый claim не должен быть затёрт под чужим lock'ом")
        finally:
            os.remove(lock)

    def test_stale_takeover_single_agent_succeeds(self):
        # Одиночный перехват протухшего claim по-прежнему работает.
        self._write_stale_claim()
        rc = agent_queue.cmd_claim(self._claim_args("agent-new"))
        self.assertEqual(rc, 0)
        cur = agent_queue.read_claim(self.task)
        self.assertEqual(cur.get("agent"), "agent-new")
        self.assertTrue(agent_queue.is_fresh(cur))

    def test_renew_own_fresh_claim_still_works(self):
        # Продление собственного свежего claim идёт тем же атомарным путём.
        a = self._claim_args("agent1")
        self.assertEqual(agent_queue.cmd_claim(a), 0)
        first = agent_queue.read_claim(self.task)
        self.assertEqual(agent_queue.cmd_claim(a), 0, "продление своего claim")
        second = agent_queue.read_claim(self.task)
        self.assertEqual(second.get("agent"), "agent1")
        self.assertNotEqual(second.get("claim_id"), first.get("claim_id"),
                            "продление ротирует claim_id")

    def test_concurrent_stale_takeover_only_one_wins(self):
        # Сценарий аудита «в лоб»: два потока конкурентно перехватывают один
        # протухший claim — OK (rc=0) должен получить ровно один.
        self._write_stale_claim()
        results = {}
        barrier = threading.Barrier(2)

        def worker(agent):
            barrier.wait()
            results[agent] = agent_queue.cmd_claim(self._claim_args(agent))

        threads = [threading.Thread(target=worker, args=(ag,))
                   for ag in ("agent-A", "agent-B")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        winners = [ag for ag, rc in results.items() if rc == 0]
        self.assertEqual(len(winners), 1,
                         "ровно один агент должен перехватить протухший claim: %r" % results)
        cur = agent_queue.read_claim(self.task)
        self.assertEqual(cur.get("agent"), winners[0],
                         "на диске — claim победителя")

if __name__ == "__main__":
    unittest.main()
