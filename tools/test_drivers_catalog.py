#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_drivers_catalog
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_drivers_catalog.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Hermetic-тесты для tools/drivers_catalog.py (каталог драйверов: манифесты vs реальность).

Изоляция через COLLAB_ROOT → временный drivers/ с известными манифестами.
drivers_catalog.py вычисляет ROOT/DRIVERS на import-time, поэтому запуск идёт
через subprocess с COLLAB_ROOT в env. Проверяем три инварианта:
  1. collect: пропуск служебных (README/_template/SCHEMA/CATALOG) и без id; сорт по id.
  2. render_catalog: markdown-таблица со всеми строками.
  3. --check контракт: stale → exit 1 (ничего не пишет); запись → exit 0, idempotent.
"""
import os
import sys
import json
import tempfile
import shutil
import subprocess

from _ioutil import configure_output

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
configure_output()

from _canon import parse_front_matter
import drivers_catalog as dcat


def write_md(path, fm):
    lines = ["---"]
    for k, v in fm.items():
        lines.append("%s: %s" % (k, v))
    lines.append("---")
    lines.append("")
    lines.append("body")
    text = "\n".join(lines)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    if fm.get("id"):
        assert parse_front_matter(text).get("id") == fm["id"], text


def make_drivers(root):
    d = os.path.join(root, "drivers")
    os.makedirs(d, exist_ok=True)
    # Намеренно не по алфавиту имён файлов, чтобы проверить сортировку по id.
    write_md(os.path.join(d, "zeta.md"), {
        "id": "DRV-002", "title": "Zeta driver", "level": "L1",
        "mode": "read", "risk": "low", "status": "active",
    })
    write_md(os.path.join(d, "alpha.md"), {
        "id": "DRV-001", "title": "Alpha driver", "level": "L0",
        "mode": "write", "risk": "high", "status": "draft",
    })
    # Служебные — должны быть пропущены (CATALOG.md/index.json — это выходные
    # цели каталога, их как фикстуры не создаём, чтобы проверить запись с нуля).
    for skip in ("README.md", "_template.md", "SCHEMA.md"):
        write_md(os.path.join(d, skip), {"id": "SHOULD-SKIP", "title": "x"})
    # Без id — пропускается.
    with open(os.path.join(d, "noid.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("---\ntitle: no id here\n---\nbody\n")
    return d


def test_collect_pure(root):
    # collect() читает DRIVERS, который зафиксирован на import-time под реальный repo.
    # Поэтому проверяем чистую логику через monkeypatch DRIVERS на наш temp.
    saved = dcat.DRIVERS
    try:
        dcat.DRIVERS = os.path.join(root, "drivers")
        items = dcat.collect()
        ids = [it["id"] for it in items]
        assert ids == ["DRV-001", "DRV-002"], ids  # сортировка + пропуск служебных/без-id
        first = items[0]
        # все FIELDS присутствуют
        for f in dcat.FIELDS:
            assert f in first, (f, first)
        assert first["title"] == "Alpha driver" and first["risk"] == "high", first
        # отсутствующие в манифесте поля → пустая строка, не KeyError
        assert first["secrets"] == "" and first["activation"] == "", first

        md = dcat.render_catalog(items)
        assert "| ID | Драйвер |" in md, md
        assert "| DRV-001 | Alpha driver | L0 | write | high | draft |" in md, md
        assert "| DRV-002 | Zeta driver | L1 | read | low | active |" in md, md
        # порядок строк = порядок items
        assert md.index("DRV-001") < md.index("DRV-002"), md
    finally:
        dcat.DRIVERS = saved


def _run(root, *args):
    env = dict(os.environ)
    env["COLLAB_ROOT"] = root
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, os.path.join(HERE, "drivers_catalog.py"), *args],
        env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL,
    )


def test_check_and_write_contract(root):
    d = os.path.join(root, "drivers")
    index_path = os.path.join(d, "index.json")
    catalog_path = os.path.join(d, "CATALOG.md")

    # 1. --check на отсутствующем каталоге → stale → exit 1, ничего не записано.
    p = _run(root, "--check")
    assert p.returncode == 1, (p.returncode, p.stdout, p.stderr)
    assert "STALE" in p.stdout, p.stdout
    assert not os.path.exists(index_path), "check не должен писать index.json"
    assert not os.path.exists(catalog_path), "check не должен писать CATALOG.md"

    # 2. Запись → exit 0, файлы созданы, index.json валиден и отсортирован.
    p = _run(root)
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert os.path.exists(index_path) and os.path.exists(catalog_path), p.stdout
    with open(index_path, encoding="utf-8") as f:
        payload = json.load(f)
    ids = [d_["id"] for d_ in payload["drivers"]]
    assert ids == ["DRV-001", "DRV-002"], ids
    assert "Драйверов в каталоге: 2" in p.stdout, p.stdout

    # 3. --check сразу после записи → актуально → exit 0.
    p = _run(root, "--check")
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert "STALE" not in p.stdout, p.stdout

    # 4. Повторная запись идемпотентна — каталог остаётся актуальным (exit 0).
    p = _run(root)
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert "актуален" in p.stdout, p.stdout

    # 5. Меняем драйвер → --check снова видит расхождение (манифест vs каталог).
    write_md(os.path.join(d, "alpha.md"), {
        "id": "DRV-001", "title": "Alpha RENAMED", "level": "L0",
        "mode": "write", "risk": "high", "status": "draft",
    })
    p = _run(root, "--check")
    assert p.returncode == 1, (p.returncode, p.stdout, p.stderr)
    assert "STALE" in p.stdout, p.stdout


def run():
    tmp = tempfile.mkdtemp(prefix="drivers_catalog_test_")
    try:
        make_drivers(tmp)
        test_collect_pure(tmp)
        test_check_and_write_contract(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("TESTS OK drivers_catalog: collect(skip/sort/fields) + render table + --check/write/idempotent contract")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
