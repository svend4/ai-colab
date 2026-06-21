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


def make_temp_dir(prefix):
    path = os.path.join(base_dir(), "%s%s" % (prefix, uuid.uuid4().hex[:12]))
    os.makedirs(path, exist_ok=False)
    return path


@contextmanager
def temp_dir(prefix):
    path = make_temp_dir(prefix)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

