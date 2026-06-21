#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест аудит-хелпера (drivers/audit.py) — T-083, ревью T-078 находка E."""
import os
import sys
import json
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audit as A


def run():
    fd, path = tempfile.mkstemp(prefix="audit_", suffix=".jsonl")
    os.close(fd)
    os.environ["DRIVER_AUDIT_LOG"] = path
    ok = True
    try:
        rec = A.audit("data", "head", "x.csv", n=5)
        assert rec["driver"] == "data" and rec["action"] == "head", rec
        A.audit("repo-runner", "inspect_repo", "/r")
        with open(path, encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 2, lines
        assert lines[0]["target"] == "x.csv" and lines[0]["n"] == 5, lines[0]
        assert "ts" in lines[0] and isinstance(lines[0]["ts"], int), lines[0]
        assert lines[1]["driver"] == "repo-runner", lines[1]
        print("TESTS OK audit lines=%d" % len(lines))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        os.environ.pop("DRIVER_AUDIT_LOG", None)
        try:
            os.remove(path)
        except OSError:
            pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
