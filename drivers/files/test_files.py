#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты files driver (read-only) на маленьком безопасном корпусе — T-043."""
import os
import re
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import files_driver as fd
from test_tmp import make_temp_dir


def make_corpus():
    d = make_temp_dir("files_test_")
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

        redacted = fd.read_file(os.path.join(d, "secret-like.txt"))["text"]
        assert "supersecret123" not in redacted and "***" in redacted, "read() не маскирует секрет"

        hits = fd.search("API_KEY", d)
        assert any(h["path"] == "secret-like.txt" for h in hits), "не нашёл API_KEY"
        assert all("supersecret123" not in h["text"] for h in hits), "СЕКРЕТ УТЁК"
        assert len(fd.search("file", d, max_hits=1)) == 1, "max_hits не ограничивает выдачу"
        assert len(fd.list_files(d, max_files=2)) == 2, "max_files не ограничивает обход"

        try:
            fd.read_file(os.path.join(d, "plain.txt"), base_dir=os.path.join(d, "nested"))
            assert False, "base_dir не ограничивает выход за allowed-root"
        except fd.PathAccessError:
            pass

        s = fd.summarize(d)
        assert s["files"] == 5 and s["total_bytes"] > 0, s

        # регрессия (аудит C45): лимит в коде обязан совпадать с max_output_bytes
        # в манифесте drivers/files.md — контракт «манифест = код», как у data-драйвера
        manifest = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "files.md")
        with open(manifest, encoding="utf-8") as f:
            m = re.search(r"^max_output_bytes:\s*(\d+)", f.read(), re.M)
        assert m, "в drivers/files.md не найден max_output_bytes"
        assert int(m.group(1)) == fd.MAX_OUTPUT_BYTES, (
            "дрейф лимита: манифест %s != код %d" % (m.group(1), fd.MAX_OUTPUT_BYTES))

        print("TESTS OK files=%d hits=%d" % (len(files), len(hits)))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
