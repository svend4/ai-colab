#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_agent_queue_fencing
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_agent_queue_fencing.py. Описание сгенерировано автоматически.
# ==========================================
"""
import os
import shutil
import tempfile
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
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
        with open(agent_queue.inbox_path(self.task), "w") as f:
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

if __name__ == "__main__":
    unittest.main()
