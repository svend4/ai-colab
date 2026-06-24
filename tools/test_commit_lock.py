#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_commit_lock
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_commit_lock.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест commit-lock (tools/commit_lock.py) — сериализация коммитов."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)


def prepare_root():
    candidates = [
        os.path.join(r"C:\tmp", "ai_colab_commit_lock_test"),
        os.path.join(REPO_ROOT, "tmp-work", "commit_lock_test_runtime"),
    ]
    last_error = None
    for root in candidates:
        try:
            shutil.rmtree(root, ignore_errors=True)
            os.makedirs(os.path.join(root, "queues"), exist_ok=True)
            probe = os.path.join(root, "queues", ".write_probe")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            return root
        except OSError as exc:
            last_error = exc
    raise RuntimeError("no writable commit_lock test root: %r" % (last_error,))


ROOT = prepare_root()
os.environ["COLLAB_ROOT"] = ROOT
sys.path.insert(0, HERE)
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

        # Протухший лок снимается и берётся.
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
