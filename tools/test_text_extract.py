#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/text_extract.py (T-133)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import text_extract as tx
from test_tmp import temp_dir


def run():
    ok = True
    try:
        with temp_dir("tx_corpus_") as d:
            md = os.path.join(d, "doc.md")
            html = os.path.join(d, "page.html")
            txt = os.path.join(d, "secret.txt")
            with open(md, "w", encoding="utf-8") as f:
                f.write("---\ntitle: Hidden Meta\n---\n# Title\n\nIntro line\n\nDeepNeedle in body\n")
            with open(html, "w", encoding="utf-8") as f:
                f.write("<html><head><style>.x{}</style><script>bad()</script></head>"
                        "<body><h1>Heading</h1><p>Visible HTML Text</p></body></html>")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("token=SUPERSECRETXYZ\nPlain body\n")

            md_item = tx.extract(md, base_dir=ROOT)
            assert md_item["supported"] is True, md_item
            assert "Title" in md_item["text"] and "DeepNeedle" in md_item["text"], md_item
            assert "Hidden Meta" not in md_item["text"], md_item
            assert "#" not in tx.summary_from_text(md_item["text"]), md_item

            html_item = tx.extract(html, base_dir=ROOT)
            assert "Visible HTML Text" in html_item["text"], html_item
            assert "bad()" not in html_item["text"], html_item

            txt_item = tx.extract(txt, base_dir=ROOT)
            assert "SUPERSECRETXYZ" not in txt_item["text"], txt_item
            assert "Plain body" in txt_item["text"], txt_item

            print("TESTS OK text_extract: md/txt/html redacted normalized")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
