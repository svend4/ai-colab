#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты git-log driver (read-only история git) — против временного git-репозитория."""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVERS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, DRIVERS)
import git_log as gl
from test_tmp import temp_dir  # workspace-safe temp (конвенция репо)


def _run(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def run():
    ok = True
    try:
        with temp_dir("gitlog_test_") as d:
            _run(d, "git", "init", "-q")
            _run(d, "git", "config", "user.email", "tester@example.com")
            _run(d, "git", "config", "user.name", "Tester")
            with open(os.path.join(d, "a.txt"), "w", encoding="utf-8") as f:
                f.write("1\n")
            _run(d, "git", "add", "-A")
            _run(d, "git", "commit", "-qm", "first")
            with open(os.path.join(d, "a.txt"), "w", encoding="utf-8") as f:
                f.write("2\n")
            _run(d, "git", "add", "-A")
            _run(d, "git", "commit", "-qm", "second")

            rc = gl.recent_commits(d, n=10)
            assert len(rc) == 2 and rc[0]["subject"] == "second", rc

            au = gl.author_stats(d)
            assert au and au[0]["author"] == "Tester" and au[0]["commits"] == 2, au

            fh = gl.file_history(d, "a.txt")
            assert len(fh) == 2, fh

            s = gl.summary(d)
            assert s["total_commits"] == 2 and s["authors"] == 1, s

            # confinement: выход за allowed-root
            try:
                gl.recent_commits("..", base_dir=d)
                assert False, "confinement не сработал"
            except gl.PathAccessError:
                pass

            # не git-репозиторий → NotARepoError
            sub = os.path.join(d, "sub")
            os.makedirs(sub)
            try:
                gl.recent_commits(sub, base_dir=d)
                assert False, "NotARepoError не сработал"
            except gl.NotARepoError:
                pass

            print("TESTS OK git-log: commits=%d authors=%d file_hist=%d" % (len(rc), len(au), len(fh)))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
