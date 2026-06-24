#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import shutil
import sys
import unittest
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import doc_synthesis


def make_project_tmp(prefix):
    base = os.path.join(ROOT, "tmp-work")
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, f"{prefix}{uuid.uuid4().hex}")
    os.makedirs(path)
    return path


class TestDocSynthesis(unittest.TestCase):
    def setUp(self):
        self.test_dir = make_project_tmp("doc_synthesis_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        for name in os.listdir(os.path.join(ROOT, "streams")) if os.path.isdir(os.path.join(ROOT, "streams")) else []:
            if name.startswith("test-doc-synthesis-"):
                shutil.rmtree(os.path.join(ROOT, "streams", name), ignore_errors=True)

    def write_doc(self, name, text):
        path = os.path.join(self.test_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return os.path.relpath(path, ROOT).replace("\\", "/")

    def test_render_custom_documents(self):
        a = self.write_doc("a.md", "# A\n\nThe top layer uses top.py, evidence, validate, and index metadata.\n")
        b = self.write_doc("b.md", "# B\n\nThe top layer uses top.py and checks evidence before integration.\n")
        out = doc_synthesis.render("custom", [a, b])
        self.assertIn("Documents scanned: 2", out)
        self.assertIn("top-layer-facade", out)
        self.assertIn("evidence-assurance", out)
        self.assertIn("status: proposed", out)
        self.assertIn("ratify-build", out)
        self.assertIn("divergence-detail", out)
        data = json.loads(doc_synthesis.render("custom", [a, b], as_json=True))
        top_theme = next(t for t in data["themes"] if t["id"] == "top-layer-facade")
        self.assertTrue(top_theme["refs"])
        self.assertIn(":", top_theme["refs"][0]["ref"])

    def test_candidates_and_streams(self):
        a = self.write_doc("c.md", "# C\n\nArchitecture core needs top.py, workflow, evidence and divergence streams.\n")
        rows = doc_synthesis.find_candidates("architecture-core", limit=5)
        self.assertTrue(rows)
        topic = "test-doc-synthesis-" + uuid.uuid4().hex[:8]
        written = doc_synthesis.write_streams(topic, [a])
        self.assertTrue(any(p.endswith("README.md") for p in written), written)
        self.assertTrue(any(p.endswith("divergence.md") for p in written), written)


if __name__ == "__main__":
    unittest.main()