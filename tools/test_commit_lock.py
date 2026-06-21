#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест commit-lock (tools/commit_lock.py) — сериализация коммитов."""
import os
import sys
import tempfile
import shutil

ROOT = tempfile.mkdtemp(prefix="cl_test_")
os.environ["COLLAB_ROOT"] = ROOT
os.makedirs(os.path.join(ROOT, "queues"), exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import commit_lock as cl


def run():
    ok = True
    try:
        assert cl.acquire("claude", wait=0) == 0, "первый acquire должен взять"
        assert (cl._read() or {}).get("agent") == "claude", cl._read()
        assert cl.acquire("codex", wait=0) == 1, "занятый лок не должен браться"
        assert cl.release("codex") == 1, "чужой release не должен снимать"
        assert cl.release("claude") == 0, "свой release снимает"
        assert cl.acquire("codex", wait=0) == 0, "после release свободно"
        assert cl.release("codex") == 0

        # протухший лок снимается и берётся
        with open(cl.LOCK, "w", encoding="utf-8", newline="\n") as f:
            f.write("agent: ghost\nepoch: 1\nlease_epoch: 1\n")
        assert cl.acquire("claude", wait=0) == 0, "протухший лок должен перехватываться"
        assert (cl._read() or {}).get("agent") == "claude", cl._read()
        cl.release("claude")

        print("TESTS OK commit_lock: acquire/busy/release/stale-takeover")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(ROOT, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
