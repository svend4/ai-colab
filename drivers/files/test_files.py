#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты files driver (read-only) на маленьком безопасном корпусе — T-043."""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import files_driver as fd


def make_corpus():
    d = tempfile.mkdtemp(prefix="files_test_")
    with open(os.path.join(d, "plain.txt"), "w", encoding="utf-8") as f:
        f.write("hello world\n")
    with open(os.path.join(d, "unicode.txt"), "w", encoding="utf-8") as f:
        f.write("привет 🌍\n")
    open(os.path.join(d, "empty.txt"), "w").close()
    with open(os.path.join(d, "secret-like.txt"), "w", encoding="utf-8") as f:
        f.write("API_KEY=supersecret123\n")
    os.makedirs(os.path.join(d, "nested"))
    with open(os.path.join(d, "nested", "a.txt"), "w", encoding="utf-8") as f:
        f.write("nested file\n")
    return d


def run():
    d = make_corpus()
    ok = True
    try:
        files = fd.list_files(d)
        assert "nested/a.txt" in files, "вложенные не обходятся"
        assert len(files) == 5, files

        assert fd.read_file(os.path.join(d, "empty.txt"))["text"] == "", "empty не пустой"

        rb = fd.read_file(os.path.join(d, "plain.txt"), max_bytes=4)
        assert rb["truncated"] and rb["text"] == "hell", rb

        hits = fd.search("API_KEY", d)
        assert any(h["path"] == "secret-like.txt" for h in hits), "не нашёл API_KEY"
        assert all("supersecret123" not in h["text"] for h in hits), "СЕКРЕТ УТЁК"

        s = fd.summarize(d)
        assert s["files"] == 5 and s["total_bytes"] > 0, s

        print("TESTS OK files=%d hits=%d" % (len(files), len(hits)))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
