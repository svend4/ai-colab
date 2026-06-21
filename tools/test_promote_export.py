#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест promote.py export — курируемая копия набора (core-export), герметично во временный каталог."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import promote
from test_tmp import make_temp_dir


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    dest = make_temp_dir("coreexport_")
    try:
        # реальные файлы ядра + один заведомо отсутствующий
        r = promote.export(["tools/_canon.py", "tools/commit_lock.py", "tools/does-not-exist.py"], dest)
        assert "tools/_canon.py" in r["copied"], r
        assert "tools/commit_lock.py" in r["copied"], r
        assert "tools/does-not-exist.py" in r["missing"], r
        # файлы реально материализованы с сохранением путей
        assert os.path.isfile(os.path.join(dest, "tools", "_canon.py")), "копия _canon.py отсутствует"
        # содержимое байт-в-байт
        a = open(os.path.join(ROOT, "tools", "_canon.py"), encoding="utf-8").read()
        b = open(os.path.join(dest, "tools", "_canon.py"), encoding="utf-8").read()
        assert a == b, "копия _canon.py отличается от исходника"
        # EXPORT.md создан и перечисляет файлы
        em = open(os.path.join(dest, "EXPORT.md"), encoding="utf-8").read()
        assert "tools/_canon.py" in em, "EXPORT.md без списка"
        # исходник НЕ тронут (это копия, не move)
        assert os.path.isfile(os.path.join(ROOT, "tools", "_canon.py")), "исходник пропал — это должен быть copy!"

        # manifest-режим: читает files: из front-matter
        files = promote._list_field(
            promote._read_fm(os.path.join(ROOT, "core", "engine-manifest.md")).get("files"))
        assert "tools/merge_gate.py" in files, "манифест не отдал files: %s" % files[:3]

        print("TESTS OK promote_export: курируемая копия (copy, not move) + EXPORT.md + manifest files:")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
