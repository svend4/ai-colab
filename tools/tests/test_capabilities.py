#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_capabilities
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_capabilities.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Hermetic-тесты для tools/capabilities.py (capability manifest — system-capabilities.json).

capabilities.py вычисляет ROOT/DRIVERS/OUT на import-time из __file__ и НЕ читает
COLLAB_ROOT, поэтому изолируем in-process: monkeypatch capabilities.DRIVERS на
временный drivers/ и capabilities.OUT на временный файл. Проверяем ключевую логику:

  1. build(): читает только манифесты type=driver, пропускает README/SCHEMA/_*/не-driver;
     drivers сортируются по id; drivers_ready = число status=ready; tools берутся из
     tools|interfaces через _list; стабильные метаданные (default_mode/commands/docs).
  2. _list(): парсинг "[a, b]" и "a, b" → ["a","b"], пустое → [].
  3. snapshot()/check() контракт: snapshot пишет детерминированный JSON (sort_keys,
     trailing \n), check на отсутствии → 1 (stale), после snapshot → 0, drift → 1.
"""
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
import json
import tempfile
import shutil

from _ioutil import configure_output

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
configure_output()

from _canon import parse_front_matter
import capabilities as cap


def write_md(path, fm, body="body\n"):
    lines = ["---"]
    for k, v in fm.items():
        lines.append("%s: %s" % (k, v))
    lines.append("---")
    lines.append("")
    text = "\n".join(lines) + body
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    # фикстуры должны быть валидным front-matter для общего парсера
    assert parse_front_matter(text).get("type") == fm.get("type"), text


def make_drivers(root):
    d = os.path.join(root, "drivers")
    os.makedirs(d, exist_ok=True)
    # Намеренно не по алфавиту имён файлов — проверяем сортировку по id.
    write_md(os.path.join(d, "zeta.md"), {
        "type": "driver", "id": "DRV-002", "title": "Zeta driver",
        "status": "ready", "level": "L1", "mode": "read", "risk": "low",
        "audit": "true", "tools": "[scan, map]",
    })
    write_md(os.path.join(d, "alpha.md"), {
        "type": "driver", "id": "DRV-001", "title": "Alpha driver",
        "status": "draft", "level": "L0", "mode": "write", "risk": "high",
        "audit": "false", "interfaces": "run, build",
    })
    # type != driver — пропускается build()
    write_md(os.path.join(d, "note.md"), {
        "type": "note", "id": "N-001", "title": "not a driver",
    })
    # служебные имена — пропускаются ещё до парсинга type
    write_md(os.path.join(d, "README.md"), {"type": "driver", "id": "SKIP-README", "title": "x"})
    write_md(os.path.join(d, "SCHEMA.md"), {"type": "driver", "id": "SKIP-SCHEMA", "title": "x"})
    write_md(os.path.join(d, "_template.md"), {"type": "driver", "id": "SKIP-UNDERSCORE", "title": "x"})
    # не .md — игнорируется
    with open(os.path.join(d, "ignore.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("not markdown\n")
    return d


def test_list():
    assert cap._list("[a, b, c]") == ["a", "b", "c"], cap._list("[a, b, c]")
    assert cap._list("x, y") == ["x", "y"], cap._list("x, y")
    assert cap._list("") == [], cap._list("")
    assert cap._list(None) == [], cap._list(None)
    assert cap._list("[ solo ]") == ["solo"], cap._list("[ solo ]")


def test_build(root):
    saved = cap.DRIVERS
    try:
        cap.DRIVERS = os.path.join(root, "drivers")
        payload = cap.build()

        ids = [d["id"] for d in payload["drivers"]]
        assert ids == ["DRV-001", "DRV-002"], ids  # сортировка по id + пропуск служебных/не-driver
        assert payload["drivers_total"] == 2, payload["drivers_total"]
        assert payload["drivers_ready"] == 1, payload["drivers_ready"]  # только DRV-002 ready

        a = payload["drivers"][0]
        assert a["title"] == "Alpha driver" and a["status"] == "draft", a
        assert a["audit"] is False, a                 # "false" -> False
        assert a["tools"] == ["run", "build"], a      # fallback на interfaces, когда tools нет
        z = payload["drivers"][1]
        assert z["audit"] is True, z                  # "true" -> True
        assert z["tools"] == ["scan", "map"], z       # tools имеет приоритет

        # стабильный контракт верхнего уровня
        assert payload["default_mode"] == "read-only", payload["default_mode"]
        assert payload["system"].startswith("AI-OS Bridge"), payload["system"]
        assert isinstance(payload["commands"], list) and payload["commands"], "commands непусты"
        assert "onboarding_agent" in payload["docs"], payload["docs"]
        # каждая команда — {cmd, does}
        for c in payload["commands"]:
            assert "cmd" in c and "does" in c, c
    finally:
        cap.DRIVERS = saved


def test_snapshot_check_contract(root):
    saved_drivers, saved_out = cap.DRIVERS, cap.OUT
    out = os.path.join(root, "system-capabilities.json")
    try:
        cap.DRIVERS = os.path.join(root, "drivers")
        cap.OUT = out

        # 1. check без файла → stale → 1, ничего не пишет
        assert not os.path.exists(out)
        rc = cap.check()
        assert rc == 1, rc
        assert not os.path.exists(out), "check не должен создавать файл"

        # 2. snapshot пишет файл → 0, детерминированный JSON (sort_keys + trailing \n)
        rc = cap.snapshot()
        assert rc == 0, rc
        assert os.path.exists(out), "snapshot должен создать файл"
        with open(out, encoding="utf-8") as f:
            raw = f.read()
        assert raw.endswith("\n"), "файл оканчивается \\n"
        payload = json.loads(raw)
        # sort_keys: ключи верхнего уровня отсортированы
        top = list(payload.keys())
        assert top == sorted(top), top
        assert payload["drivers_total"] == 2, payload

        # 3. check сразу после snapshot → актуально → 0
        rc = cap.check()
        assert rc == 0, rc

        # 4. drift: меняем драйвер → check видит расхождение → 1
        write_md(os.path.join(root, "drivers", "alpha.md"), {
            "type": "driver", "id": "DRV-001", "title": "Alpha RENAMED",
            "status": "draft", "level": "L0", "mode": "write", "risk": "high",
        })
        rc = cap.check()
        assert rc == 1, rc

        # 5. повторный snapshot снова делает check зелёным (idempotent re-gen)
        assert cap.snapshot() == 0
        assert cap.check() == 0
    finally:
        cap.DRIVERS, cap.OUT = saved_drivers, saved_out


def run():
    tmp = tempfile.mkdtemp(prefix="capabilities_test_")
    try:
        make_drivers(tmp)
        test_list()
        test_build(tmp)
        test_snapshot_check_contract(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("TESTS OK capabilities: _list parse + build(skip/sort/ready/tools/audit) + snapshot/check drift contract")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
