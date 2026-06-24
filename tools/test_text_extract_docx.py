#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_text_extract_docx
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_text_extract_docx.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест DOCX-ветки text_extract (котёл-пункт 5): stdlib zipfile, без зависимости, с redaction+confinement."""
import os
import sys
import zipfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import text_extract as tx
from test_tmp import make_temp_dir


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _make_docx(path, paragraphs):
    body = "".join("<w:p><w:r><w:t>%s</w:t></w:r></w:p>" % p for p in paragraphs)
    doc = ('<?xml version="1.0"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           '<w:body>%s</w:body></w:document>') % body
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", doc)


def run():
    ok = True
    base = make_temp_dir("docx_")
    try:
        p = os.path.join(base, "doc.docx")
        _make_docx(p, ["Первый абзац DeepNeedle", "token=SUPERSECRETXYZ123"])
        item = tx.extract(p, base_dir=base)
        assert item["supported"] is True, item
        assert item["type"] == "docx", item
        assert "DeepNeedle" in item["text"], item
        assert "Первый абзац" in item["text"], item
        # redaction секрета (как у read_file(redact=True) для текстовых)
        assert "SUPERSECRETXYZ123" not in item["text"], "секрет не замаскирован: %r" % item["text"]

        # confinement: файл вне allowed-root -> PathAccessError
        try:
            tx.extract(p, base_dir=os.path.join(base, "sub"))
            assert False, "ожидался PathAccessError для пути вне корня"
        except tx.PathAccessError:
            pass

        # битый «docx» -> понятная ValueError, не краш
        bad = os.path.join(base, "bad.docx")
        with open(bad, "wb") as f:
            f.write(b"not a zip")
        try:
            tx.extract(bad, base_dir=base)
            assert False, "ожидался ValueError для не-zip"
        except ValueError:
            pass

        print("TESTS OK text_extract docx: stdlib-извлечение + redaction + confinement + bad-zip")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
