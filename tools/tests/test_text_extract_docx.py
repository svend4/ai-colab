#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_text_extract_docx
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_text_extract_docx.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест DOCX-ветки text_extract (котёл-пункт 5): stdlib zipfile, без зависимости, с redaction+confinement."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import zipfile
import shutil
from unittest import mock

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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


def _boundary_checks(base):
    # Граница корня. На Python 3.12 realpath() после цикла симлинков схлопывает «..» по тексту:
    # L/../S/secret.docx оказывался внутри корня, хотя читал файл снаружи через симлинк S.
    root = os.path.join(base, "allowed")
    outside = os.path.join(base, "outside")
    os.makedirs(root)
    os.makedirs(outside)
    marker = "TOPSECRET_DOCX_BOUNDARY_MARKER"
    _make_docx(os.path.join(outside, "secret.docx"), [marker])
    _make_docx(os.path.join(root, "inside.docx"), ["внутренний абзац"])
    os.symlink(os.path.join(root, "L"), os.path.join(root, "L"))
    os.symlink(os.path.join("..", "outside"), os.path.join(root, "S"))

    def refused(path, base_dir):
        try:
            item = tx.extract(path, base_dir=base_dir)
        except tx.PathAccessError:
            return True
        assert marker not in repr(item), "утечка через %r: %r" % (path, item)
        return False

    assert refused("L/../S/secret.docx", root), "«..» после симлинк-цикла вывел из корня"
    os.symlink(os.path.join(root, "Ltx"), os.path.join(root, "Ltx"))
    assert refused("S/secret.docx", root), "симлинк наружу не отказан"
    assert refused("Ltx/../inside.docx", root), "«..» после петли внутри корня вернул файл"
    assert refused(os.path.join(outside, "secret.docx"), root), "абсолютный путь наружу не отказан"
    cwd = os.getcwd()
    os.chdir(root)
    try:
        for bad_base in ("", ".", "   "):
            assert refused("inside.docx", bad_base), "база %r приняла текущую папку" % bad_base
    finally:
        os.chdir(cwd)
    assert tx.extract("inside.docx", base_dir=root)["supported"] is True


def _race_and_hardlink_checks(base):
    # Каталог или файл внутри корня подменяется симлинком наружу уже после проверки: цепочка dir_fd с
    # O_NOFOLLOW даёт ELOOP и отказ. Жёсткая ссылка на файл снаружи тоже отказ.
    root = os.path.join(base, "allowed2")
    outside = os.path.join(base, "outside2")
    marker = "TOPSECRET_DOCX_RACE_MARKER"
    os.makedirs(os.path.join(root, "sub"))
    os.makedirs(outside)
    _make_docx(os.path.join(outside, "secret.docx"), [marker])
    _make_docx(os.path.join(root, "sub", "inside.docx"), ["внутренний абзац"])
    _make_docx(os.path.join(root, "one.docx"), ["один"])
    real_open = os.open
    swapped = []

    def refused(rel):
        try:
            item = tx.extract(rel, base_dir=root)
        except tx.PathAccessError:
            return True
        assert marker not in repr(item), "утечка через %r: %r" % (rel, item)
        return False

    def swap_dir(name, flags, *args, **kwargs):
        if name == "sub" and not swapped:
            swapped.append(name)
            shutil.rmtree(os.path.join(root, "sub"))
            os.symlink(outside, os.path.join(root, "sub"))
        return real_open(name, flags, *args, **kwargs)

    if tx._SAFE_OPEN:  # гонка воспроизводится только с O_NOFOLLOW и dir_fd (нет на Windows)
        with mock.patch.object(tx.os, "open", side_effect=swap_dir):
            assert refused(os.path.join("sub", "inside.docx")), "подмена каталога перед открытием не отказана"
        assert swapped == ["sub"], "подмена каталога не сработала"

        swapped.clear()
        target = os.path.join(root, "one.docx")

        def swap_file(name, flags, *args, **kwargs):
            if name == "one.docx" and not swapped:
                swapped.append(name)
                os.remove(target)
                os.symlink(os.path.join(outside, "secret.docx"), target)
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(tx.os, "open", side_effect=swap_file):
            assert refused("one.docx"), "подмена файла перед открытием не отказана"
        assert swapped == ["one.docx"], "подмена файла не сработала"

    os.link(os.path.join(outside, "secret.docx"), os.path.join(root, "hard.docx"))
    assert refused("hard.docx"), "жёсткая ссылка на файл снаружи не отказана"

    if hasattr(os, "mkfifo"):  # FIFO в корне не открывается: тип проверяется по stat до open()
        os.mkfifo(os.path.join(root, "pipe.docx"))
        opened = []

        def record_open(name, flags, *args, **kwargs):
            opened.append(os.path.basename(str(name)))
            return real_open(name, flags, *args, **kwargs)

        with mock.patch.object(tx.os, "open", side_effect=record_open):
            try:
                tx.extract("pipe.docx", base_dir=root)
                assert False, "FIFO в корне не отказан"
            except FileNotFoundError:
                pass
        assert "pipe.docx" not in opened, "FIFO открыт до проверки типа"


def run():
    ok = True
    base = make_temp_dir("docx_")
    try:
        _boundary_checks(base)
        _race_and_hardlink_checks(base)
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
