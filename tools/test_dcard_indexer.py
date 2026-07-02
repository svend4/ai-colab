#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест dcard_indexer.py — извлечение D-Card из .py/.md и сборка индекса.

Закрывает аудит C47: (1) голые `except:` заменены на конкретные исключения,
(2) yaml.safe_load заменён на канонический _canon.parse_front_matter —
сторонняя зависимость PyYAML больше не нужна. Самопроверено.
"""
import os
import re
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
configure_output()
import dcard_indexer as di


def _w(path, text, mode="w"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    kwargs = {"encoding": "utf-8", "newline": "\n"} if "b" not in mode else {}
    with open(path, mode, **kwargs) as f:
        f.write(text)


PY_CARD = (
    "#!/usr/bin/env python3\n"
    '"""\n'
    "# ==========================================\n"
    "# [FILE ID CARD]\n"
    "# ID: tools.sample\n"
    "# TYPE: active-script\n"
    "# DOMAIN: core.testing\n"
    "# DEPTH_LEVEL: 1\n"
    "# SUMMARY: Пример для теста.\n"
    "# ==========================================\n"
    '"""\n'
)

MD_CARD = (
    "---\n"
    "id: docs.sample\n"
    "type: doc\n"
    "domain: core.testing\n"
    "summary: Пример визитки key: value\n"
    "---\n"
    "# Тело документа\n"
)


def run():
    tmp_root = os.path.join(REPO_ROOT, "tmp-work")
    os.makedirs(tmp_root, exist_ok=True)
    root = tempfile.mkdtemp(prefix="dcard_test_", dir=tmp_root)
    saved_root = di.ROOT
    try:
        # 1) Регрессия C47: в исходнике нет ни import yaml, ни голых except.
        with open(di.__file__, "r", encoding="utf-8") as f:
            src = f.read()
        assert "import yaml" not in src, "PyYAML снова импортируется"
        assert not re.search(r"except\s*:", src), "остался голый except:"

        # 2) .py: визитка извлекается, ключи в нижнем регистре.
        py_path = os.path.join(root, "sample.py")
        _w(py_path, PY_CARD)
        card = di.extract_py_dcard(py_path)
        assert card and card["id"] == "tools.sample" and card["domain"] == "core.testing", card

        # 3) .md: front-matter парсится каноническим _canon-парсером (без yaml),
        #    значение с двоеточием не режется (split(':', 1)).
        md_path = os.path.join(root, "sample.md")
        _w(md_path, MD_CARD)
        card = di.extract_md_dcard(md_path)
        assert card and card["id"] == "docs.sample", card
        assert card["summary"] == "Пример визитки key: value", card

        # 4) .md без front-matter и без закрывающего --- → None.
        _w(os.path.join(root, "plain.md"), "# Просто заметка\n")
        assert di.extract_md_dcard(os.path.join(root, "plain.md")) is None
        _w(os.path.join(root, "broken.md"), "---\nid: x\nбез закрытия\n")
        assert di.extract_md_dcard(os.path.join(root, "broken.md")) is None

        # 5) Ошибки чтения обрабатываются адресно, а не голым except:
        #    несуществующий файл (OSError) и битый utf-8 (UnicodeDecodeError) → None.
        assert di.extract_py_dcard(os.path.join(root, "нет-такого.py")) is None
        assert di.extract_md_dcard(os.path.join(root, "нет-такого.md")) is None
        bad_path = os.path.join(root, "bad.md")
        _w(bad_path, b"---\nid: x\n\xff\xfe\n---\n", mode="wb")
        assert di.extract_md_dcard(bad_path) is None
        assert di.extract_py_dcard(bad_path) is None

        # 6) Сквозная сборка: build_index + write_markdown_index на временном ROOT.
        di.ROOT = root
        cards = di.build_index()
        ids = sorted(c.get("id") for c in cards)
        assert ids == ["docs.sample", "tools.sample"], ids
        di.write_markdown_index(cards)
        out_path = os.path.join(root, "docs", "dcard_index.md")
        with open(out_path, "r", encoding="utf-8") as f:
            out = f.read()
        assert "`tools.sample`" in out and "`docs.sample`" in out, out

        print("TESTS OK dcard_indexer: no-yaml/no-bare-except · py+md dcard · OSError/UnicodeDecodeError → None · build+write")
        return 0
    finally:
        di.ROOT = saved_root
        shutil.rmtree(root, ignore_errors=True)


def test_dcard_indexer():
    # Обёртка для pytest: вся логика в run().
    assert run() == 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
