#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_doc_synthesis
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_doc_synthesis.py. Описание сгенерировано автоматически.
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

import json
import os
import shutil
import sys
import unittest
import uuid

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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
        with open(path, "w", encoding="utf-8", newline="\n") as f:
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



    def test_resolve_files_reads_stream_topic_corpus(self):
        topic = "test-doc-synthesis-" + uuid.uuid4().hex[:8]
        stream_dir = os.path.join(ROOT, "streams", topic, "20260625-codex")
        os.makedirs(stream_dir, exist_ok=True)
        stream_file = os.path.join(stream_dir, "STREAM.md")
        with open(stream_file, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join([
                "---",
                "id: 20260625-codex",
                "topic: %s" % topic,
                "status: ready-for-synthesis",
                "---",
                "",
                "# Stream fixture",
                "",
                "The top layer uses top.py, evidence, streams, divergence, and workflow checks.",
            ]) + "\n")
        expected = "streams/%s/20260625-codex/STREAM.md" % topic
        files = doc_synthesis.resolve_files(topic, [])
        self.assertEqual([expected], files)
        data = json.loads(doc_synthesis.render(topic, files, as_json=True))
        self.assertEqual(expected, data["documents"][0]["path"])
        self.assertTrue(any(t["id"] == "top-layer-facade" for t in data["themes"]))


    def test_resolve_files_ready_only_stream_topic_corpus(self):
        topic = "test-doc-synthesis-" + uuid.uuid4().hex[:8]
        ready_dir = os.path.join(ROOT, "streams", topic, "20260625-ready")
        proposed_dir = os.path.join(ROOT, "streams", topic, "20260625-proposed")
        os.makedirs(ready_dir, exist_ok=True)
        os.makedirs(proposed_dir, exist_ok=True)
        with open(os.path.join(ready_dir, "STREAM.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join([
                "---",
                "id: 20260625-ready",
                "topic: %s" % topic,
                "status: ready-for-synthesis",
                "---",
                "",
                "# Ready stream",
                "",
                "top.py evidence streams divergence workflow",
            ]) + "\n")
        with open(os.path.join(proposed_dir, "STREAM.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join([
                "---",
                "id: 20260625-proposed",
                "topic: %s" % topic,
                "status: proposed",
                "synthesis_ready: false",
                "---",
                "",
                "# Proposed stream",
            ]) + "\n")
        all_files = doc_synthesis.resolve_files(topic, [])
        ready_files = doc_synthesis.resolve_files(topic, [], ready_only=True)
        self.assertEqual(2, len(all_files), all_files)
        self.assertEqual(["streams/%s/20260625-ready/STREAM.md" % topic], ready_files)
        data = json.loads(doc_synthesis.render(topic, ready_files, as_json=True))
        self.assertEqual(1, len(data["documents"]))
        self.assertIn("20260625-ready", data["documents"][0]["path"])

if __name__ == "__main__":
    unittest.main()
