#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for inf_crdt.py — the CRDT laws and the concurrent-edit scenario."""

import unittest
import inf_crdt as crdt
from inf_crdt import LWW, ORSet, Doc


BASE = [
    {"id": "A1", "type": "decision", "q6": "-+--+-", "body": "base body", "links": []},
    {"id": "A2", "type": "evidence", "q6": "-+--++", "body": "evidence", "links": []},
]


class TestLWW(unittest.TestCase):
    def test_higher_ts_wins(self):
        a, b = LWW("x", 5, "A"), LWW("y", 7, "B")
        self.assertEqual(LWW.merge(a, b).value, "y")
        self.assertEqual(LWW.merge(b, a).value, "y")  # commutative

    def test_replica_breaks_tie(self):
        a, b = LWW("x", 5, "A"), LWW("y", 5, "B")
        self.assertEqual(LWW.merge(a, b).value, "y")   # B > A
        self.assertEqual(LWW.merge(b, a).value, "y")


class TestORSet(unittest.TestCase):
    def test_concurrent_adds_both_survive(self):
        a, b = ORSet(), ORSet()
        a.add("x", "A:1")
        b.add("y", "B:1")
        m = ORSet.merge(a, b)
        self.assertEqual(set(m.values()), {"x", "y"})

    def test_observed_remove(self):
        a = ORSet()
        a.add("x", "A:1")
        a.remove("x")
        self.assertEqual(a.values(), [])

    def test_add_wins_over_concurrent_remove(self):
        a = ORSet(); a.add("x", "A:1")
        b = a  # B observed the same add
        b2 = ORSet(adds={"x": {"A:1"}})
        b2.remove("x")                  # B removes the observed add
        a.add("x", "A:2")               # A concurrently re-adds with a NEW tag
        m = ORSet.merge(a, b2)
        self.assertIn("x", m.values())  # the unobserved re-add survives


class TestMergeLaws(unittest.TestCase):
    def _replicas(self):
        base = crdt.from_blocks(BASE, "seed")
        a, b, c = base.clone("A"), base.clone("B"), base.clone("C")
        a.edit_body("A1", "A-edit"); a.add_link("A1", "elaborate", "x", "a")
        b.edit_body("A1", "B-edit"); b.add_link("A1", "exception", "y", "b")
        c.add_block({"id": "C.k", "type": "claim", "q6": "++++++", "body": "C-only"})
        return a, b, c

    def test_commutative(self):
        a, b, _ = self._replicas()
        self.assertTrue(crdt.converged(a.clone().merge(b), b.clone().merge(a)))

    def test_idempotent(self):
        a, _, _ = self._replicas()
        self.assertTrue(crdt.converged(a.clone().merge(a), a))

    def test_associative(self):
        a, b, c = self._replicas()
        left = a.clone().merge(b.clone().merge(c))
        right = a.clone().merge(b).merge(c)
        self.assertTrue(crdt.converged(left, right))


class TestConcurrentSameBlock(unittest.TestCase):
    def setUp(self):
        base = crdt.from_blocks(BASE, "seed")
        self.a = base.clone("A")
        self.b = base.clone("B")
        # concurrent edit of the SAME field of the SAME block
        self.a.edit_body("A1", "A version")
        self.b.edit_body("A1", "B version")
        # concurrent links from the same block
        self.a.add_link("A1", "elaborate", "A.k1", "fromA")
        self.b.add_link("A1", "exception", "B.k1", "fromB")

    def test_converges_both_orders(self):
        ab = self.a.clone().merge(self.b)
        ba = self.b.clone().merge(self.a)
        self.assertTrue(crdt.converged(ab, ba))

    def test_deterministic_body_winner(self):
        merged = self.a.clone().merge(self.b)
        body = next(x["body"] for x in merged.to_blocks() if x["id"] == "A1")
        self.assertEqual(body, "B version")   # equal ts -> replica B wins the tie

    def test_both_links_survive(self):
        merged = self.a.clone().merge(self.b)
        a1 = next(x for x in merged.to_blocks() if x["id"] == "A1")
        targets = {l["target"] for l in a1.get("links", [])}
        self.assertIn("A.k1", targets)
        self.assertIn("B.k1", targets)


class TestRoundTrip(unittest.TestCase):
    def test_blocks_preserved(self):
        d = crdt.from_blocks(BASE, "x")
        ids = {b["id"] for b in d.to_blocks()}
        self.assertEqual(ids, {"A1", "A2"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
