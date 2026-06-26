#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for infon.py — stdlib unittest, zero dependencies."""

import json
import unittest

import infon


SAMPLE = """\
∞ a  type:claim  q6:------
  rel:   r
  args:  [x, y]
  links: →b(elab)  ⇒c(exc)  ·d
  ──
  body of a
  second line

∞ b  type:evidence  q6:-----+
  ──
  body of b

∞ c  type:claim  q6:++++++
  ──
  body of c

# d is intentionally missing to test dangling-link detection
"""


class TestParse(unittest.TestCase):
    def setUp(self):
        self.g = infon.parse(SAMPLE)

    def test_block_count_and_order(self):
        self.assertEqual(len(self.g), 3)
        self.assertEqual(self.g.order, ["a", "b", "c"])

    def test_fields(self):
        a = self.g.blocks["a"]
        self.assertEqual(a.type, "claim")
        self.assertEqual(a.q6, "------")
        self.assertEqual(a.rel, "r")
        self.assertEqual(a.args, ["x", "y"])
        self.assertEqual(a.pol, "+")

    def test_multiline_body(self):
        # block-nesting indentation is stripped (dedented)
        self.assertEqual(self.g.blocks["a"].body, "body of a\nsecond line")

    def test_body_preserves_relative_indent(self):
        g = infon.parse("∞ x\n  ──\n  parent\n    child\n")
        self.assertEqual(g.blocks["x"].body, "parent\n  child")

    def test_links_and_kinds(self):
        a = self.g.blocks["a"]
        self.assertEqual(len(a.links), 3)
        self.assertEqual(a.links[0].kind, "elaborate")
        self.assertEqual(a.links[0].target, "b")
        self.assertEqual(a.links[0].label, "elab")
        self.assertEqual(a.links[1].kind, "exception")
        self.assertEqual(a.links[2].kind, "context")   # bare ·d
        self.assertEqual(a.links[2].target, "d")

    def test_ascii_aliases(self):
        g = infon.parse("@@ z  type:claim  q6:++++++\n"
                         "  links: ->a(e) =>b(x) ..c\n"
                         "  ---\n"
                         "  ascii body\n")
        z = g.blocks["z"]
        self.assertEqual(z.body, "ascii body")
        self.assertEqual([l.kind for l in z.links],
                         ["elaborate", "exception", "context"])

    def test_polarity_negative(self):
        g = infon.parse("∞ n\n  pol: -\n  ──\n  x\n")
        self.assertEqual(g.blocks["n"].pol, "-")

    def test_malformed_q6_warns(self):
        g = infon.parse("∞ m  q6:+++\n  ──\n  x\n")
        self.assertIsNone(g.blocks["m"].q6)
        self.assertTrue(any("malformed q6" in w for w in g.warnings))

    def test_duplicate_id_warns(self):
        g = infon.parse("∞ d\n  ──\n  one\n∞ d\n  ──\n  two\n")
        self.assertEqual(len(g), 1)
        self.assertTrue(any("duplicate" in w for w in g.warnings))


class TestQ6(unittest.TestCase):
    def test_vec(self):
        self.assertEqual(infon.q6_vec("+-+-+-"), (1, -1, 1, -1, 1, -1))

    def test_hamming(self):
        self.assertEqual(infon.hamming("------", "------"), 0)
        self.assertEqual(infon.hamming("------", "-----+"), 1)
        self.assertEqual(infon.hamming("------", "++++++"), 6)

    def test_hamming_length_mismatch(self):
        with self.assertRaises(ValueError):
            infon.hamming("-----", "------")


class TestCluster(unittest.TestCase):
    def test_three_clusters_in_example(self):
        with open("example.inf", encoding="utf-8") as fh:
            g = infon.parse(fh.read())
        clusters = infon.cluster(g, radius=1)
        multi = [c for c in clusters if len(c) > 1]
        self.assertEqual(len(multi), 3)
        sizes = sorted(len(c) for c in multi)
        self.assertEqual(sizes, [2, 3, 4])
        # Z1 (++++++) is far from everything -> singleton
        singles = [c for c in clusters if len(c) == 1]
        self.assertIn(["Z1"], singles)

    def test_radius_zero_isolates(self):
        g = infon.parse(
            "∞ a q6:------\n ──\n x\n∞ b q6:-----+\n ──\n y\n"
        )
        clusters = infon.cluster(g, radius=0)
        self.assertEqual(sorted(len(c) for c in clusters), [1, 1])


class TestWalk(unittest.TestCase):
    def test_domino_walk(self):
        g = infon.parse(
            "∞ a\n links: →b →c\n ──\n a\n"
            "∞ b\n links: →d\n ──\n b\n"
            "∞ c\n ──\n c\n"
            "∞ d\n ──\n d\n"
        )
        ids = [bid for _, bid, _ in infon.walk(g, "a")]
        self.assertEqual(ids[0], "a")
        self.assertIn("d", ids)

    def test_kind_filter(self):
        g = infon.parse(
            "∞ a\n links: →b(e) ⇒c(x)\n ──\n a\n"
            "∞ b\n ──\n b\n∞ c\n ──\n c\n"
        )
        ids = [bid for _, bid, _ in infon.walk(g, "a", kind="exception")]
        self.assertEqual(ids, ["a", "c"])

    def test_cycle_safe(self):
        g = infon.parse(
            "∞ a\n links: →b\n ──\n a\n"
            "∞ b\n links: →a\n ──\n b\n"
        )
        # should terminate
        steps = infon.walk(g, "a")
        self.assertTrue(len(steps) >= 2)


class TestValidate(unittest.TestCase):
    def test_dangling_detected(self):
        g = infon.parse(SAMPLE)
        issues = infon.validate(g)
        self.assertTrue(any("dangling" in m and "'d'" in m for m in issues))


class TestNodeLink(unittest.TestCase):
    def test_roundtrip(self):
        data = {
            "directed": True,
            "nodes": [
                {"id": "n1", "type": "norm", "label": "Erste Norm", "q6": "+-+-+-"},
                {"id": "n2", "type": "fall", "label": "Ein Fall"},
            ],
            "links": [
                {"source": "n1", "target": "n2", "relation": "context"},
            ],
        }
        text = infon.from_nodelink(data)
        g = infon.parse(text)
        self.assertEqual(len(g), 2)
        self.assertEqual(g.blocks["n1"].q6, "+-+-+-")        # real q6 preserved
        self.assertIsNotNone(g.blocks["n2"].q6)              # derived placeholder
        self.assertEqual(g.blocks["n1"].links[0].target, "n2")
        self.assertEqual(g.blocks["n1"].links[0].kind, "context")
        self.assertEqual(g.blocks["n1"].body, "Erste Norm")


if __name__ == "__main__":
    unittest.main(verbosity=2)
