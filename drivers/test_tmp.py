#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test temp directories that work in the local collaboration workspace."""
import os
import shutil
import uuid
from contextlib import contextmanager


DRIVERS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DRIVERS_DIR)


def base_dir():
    base = os.environ.get("COLLAB_TEST_TMP")
    if not base:
        base = os.path.join(ROOT, "tmp-work")
    os.makedirs(base, exist_ok=True)
    return os.path.abspath(base)


def _probe_writable(path):
    probe = os.path.join(path, ".write-probe")
    with open(probe, "w", encoding="utf-8", newline="\n") as f:
        f.write("ok\n")
    with open(probe, encoding="utf-8") as f:
        assert f.read() == "ok\n"
    os.remove(probe)


def make_temp_dir(prefix):
    last_error = None
    for _ in range(100):
        path = os.path.join(base_dir(), "%s%s" % (prefix, uuid.uuid4().hex[:12]))
        try:
            os.makedirs(path, exist_ok=False)
            _probe_writable(path)
            return path
        except OSError as exc:
            last_error = exc
            shutil.rmtree(path, ignore_errors=True)
    raise OSError("cannot create writable project temp dir: %r" % (last_error,))


@contextmanager
def temp_dir(prefix):
    path = make_temp_dir(prefix)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

