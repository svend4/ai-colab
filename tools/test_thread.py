#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_thread
# TYPE: active-script
# DOMAIN: core.thread
# DEPTH_LEVEL: 1
# SUMMARY: Tests for file-native thread objects.
# ==========================================
"""
"""Tests for tools/thread.py (T-264)."""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import thread as th


def run():
    topic = "thread-test"
    root = os.path.join(th.TOPICS, topic)
    ok = True
    try:
        shutil.rmtree(root, ignore_errors=True)

        data = th.init_thread(topic, agent="codex", mode="read-only", task_id="T-264")
        assert data["schema"] == th.SCHEMA, data
        assert data["topic"] == topic, data
        assert data["agent"] == "codex", data
        assert data["task_id"] == "T-264", data

        thread_path, loaded = th.load_thread(data["id"])
        assert thread_path.exists(), thread_path
        assert loaded["id"] == data["id"], loaded

        m1 = th.add_message(data["id"], "user", text="hello\nмир")
        assert m1["role"] == "user", m1
        m1_path = os.path.join(ROOT, m1["path"])
        assert os.path.exists(m1_path), m1_path
        with open(m1_path, encoding="utf-8") as f:
            msg = f.read()
        assert "schema: thread_message.v1" in msg, msg
        assert "hello\nмир" in msg, msg

        src = os.path.join(root, "source.md")
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write("# Source\n\nfile body\n")
        m2 = th.add_message(data["id"], "assistant", file_path=os.path.relpath(src, ROOT))
        assert m2["source"].endswith("source.md"), m2

        out = th.add_output(data["id"], os.path.relpath(src, ROOT), kind="report")
        assert out["exists"] is True, out
        assert out["kind"] == "report", out

        _, final = th.load_thread(data["id"])
        assert len(final["messages"]) == 2, final
        assert len(final["outputs"]) == 1, final
        json.dumps(final, ensure_ascii=False)

        listed = [d for _, d in th.iter_threads(topic=topic)]
        assert [d["id"] for d in listed] == [data["id"]], listed

        print("TESTS OK thread: init/add-message/add-output/status")
    except AssertionError as exc:
        ok = False
        print("TEST FAIL:", exc)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())