#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hermetic tests for tools/friction.py (T-150)."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import friction


def run():
    assert friction.resolve_fid("F-007") == "F-007"
    assert friction.resolve_fid("stale-index") == "F-007"
    assert "generate.py" in friction.recipe_text("F-007")

    clean = friction.check_volatile_tracking("", "LIVE.md\nPIPELINE.md\nlogs/heartbeat.json\nlogs/pipeline.json\n")
    assert clean["status"] == "ok", clean
    tracked = friction.check_volatile_tracking("LIVE.md\n", "LIVE.md\n")
    assert tracked["status"] == "fail" and "tracked" in " ".join(tracked["evidence"]), tracked
    missing = friction.check_volatile_tracking("", "LIVE.md\n")
    assert missing["status"] == "warn" and "missing" in " ".join(missing["evidence"]), missing

    git_checks = friction.check_git_status(" M TASKS.md\n?? docs/new.md\n M LIVE.md\n")
    by_id = {c["id"]: c for c in git_checks}
    assert by_id["F-006"]["status"] == "warn", by_id
    assert by_id["F-008"]["status"] == "warn", by_id
    assert by_id["F-015"]["status"] == "warn", by_id

    gen = friction.check_generate(1, "STALE: TASKS.md")
    assert gen["id"] == "F-007" and gen["status"] == "warn", gen
    gen_ok = friction.check_generate(0, "OK")
    assert gen_ok["status"] == "ok", gen_ok

    pipe = friction.check_pipeline("T-020 <- doing without active claim\nT-062 <- placeholder task")
    pipe_by_id = {c["id"]: c for c in pipe}
    assert pipe_by_id["F-009"]["status"] == "warn", pipe_by_id
    assert pipe_by_id["F-010"]["status"] == "warn", pipe_by_id

    tmp_base_candidates = [
        os.path.join(r"C:\tmp", "ai_colab_friction_test"),
        os.path.join(friction.ROOT, "tmp-work", "friction_test_runtime"),
    ]
    last_error = None
    tmp = None
    for candidate in tmp_base_candidates:
        try:
            shutil.rmtree(candidate, ignore_errors=True)
            os.makedirs(candidate, exist_ok=True)
            tmp = candidate
            break
        except OSError as exc:
            last_error = exc
    if tmp is None:
        raise RuntimeError("no writable friction test root: %r" % (last_error,))
    try:
        temp_check = friction.check_temp_probe(tmp)
        assert temp_check["status"] == "ok", temp_check
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    rec = friction.recommendation([gen, by_id["F-006"]])
    assert "LEVEL 1" in rec or "SELECTIVE-ADD" in rec, rec

    print("TESTS OK friction: registry/recipes + pure detectors + temp probe")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)