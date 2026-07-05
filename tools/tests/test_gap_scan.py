#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест gap_scan.py — детектор разрывов замысел↔реальность (orphan / drift / dangling).

Гермётичен: строит ИЗОЛИРОВАННЫЙ temp-репозиторий (уникальный tempfile.mkdtemp — урок B-03:
без общих путей tmp-work/, чтобы не было флейка в батче).

Тестирует функции IN-PROCESS (импортирует модуль, перенаправляет ROOT/TOOLS на temp-репо), а не
через subprocess по абсолютному пути — иначе мутация модуля не доходит до теста (co-defective, C-III).
Утверждения — на ТОЧНЫЕ множества, чтобы структурные мутации детектора краснели.
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
import tempfile
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
from _ioutil import configure_output  # UTF-8 stdout на Windows
configure_output()
import gap_scan


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _build(root):
    _w(os.path.join(root, "README.md"), "# repo\n")
    _w(os.path.join(root, "PROTOCOL.md"), "правила\n")
    _w(os.path.join(root, "AGENTS.md"), "агенты\n")
    # docs ссылается на used_tool, drifter (оба существуют → не orphan) и ghost (нет файла → dangling)
    _w(os.path.join(root, "docs", "guide.md"),
       "См. `python tools/used_tool.py`, `tools/drifter.py`, и `python tools/ghost.py`.\n")
    # roadmap: future_tool не существует, но строка помечена PLANNED_MARKER → G5 её пропускает (C40);
    # ghost2 без маркера на соседней строке — настоящая висячая ссылка (маркер действует построчно)
    _w(os.path.join(root, "docs", "roadmap.md"),
       "Сделать `tools/future_tool.py` %s — план.\nА `tools/ghost2.py` — висячая ссылка.\n"
       % gap_scan.PLANNED_MARKER)
    _w(os.path.join(root, "tools", "orphan_tool.py"), "print('никто не ссылается')\n")
    # свой тест — исключён; лежит в tools/tests/ (канон C14 — gap_scan ищет own_test там)
    _w(os.path.join(root, "tools", "tests", "test_orphan_tool.py"), "import orphan_tool\n")
    _w(os.path.join(root, "tools", "used_tool.py"), "print('used')\n")
    dead = list(gap_scan.DEAD_DIR_LITERALS)[0]  # мёртвый литерал берём из карты детектора, не хардкодим
    _w(os.path.join(root, "tools", "drifter.py"), "def f():\n    return load(%r)\n" % dead)  # дрейф на строке 2
    _w(os.path.join(root, "tools", "pipeline.py"), "print('entry')\n")  # allowlist → не orphan
    # C15-b (волна 2): allowlist-сирота «про запас» — без единой ссылки, но шуметь не должен
    _w(os.path.join(root, "tools", "fold.py"), "print('held in reserve')\n")
    # P8-b (волна 2): carded_tool с визиткой (dcard-детектор его НЕ флажит); used_tool/orphan_tool/
    # drifter/pipeline/fold — без визитки (флажатся все не-тестовые без [FILE ID CARD])
    _w(os.path.join(root, "tools", "carded_tool.py"),
       "# ==========================================\n"
       "# [FILE ID CARD]\n"
       "# ID: tools.carded_tool\n"
       "# SUMMARY: с визиткой\n"
       "# ==========================================\n"
       "print('carded, referenced')\n")
    _w(os.path.join(root, "docs", "carded.md"), "См. `tools/carded_tool.py`.\n")  # не orphan
    _w(os.path.join(root, "tools", "_helper.py"), "x = 1\n")  # _-хелпер → не модуль


def run():
    root = tempfile.mkdtemp(prefix="gap_scan_test_")
    saved = (gap_scan.ROOT, gap_scan.TOOLS)
    try:
        _build(root)
        gap_scan.ROOT = root
        gap_scan.TOOLS = os.path.join(root, "tools")

        orphans = {x["name"] for x in gap_scan.find_orphans()}
        assert orphans == {"tools/orphan_tool.py"}, "orphans должно быть РОВНО {orphan_tool}: %s" % orphans
        # C15-b: fold в ORPHAN_ALLOWLIST → не шумит, хотя ссылок на него нет
        assert "tools/fold.py" not in orphans, "заallowlist-ленный сирота (fold) не должен шуметь"

        drift = {x["name"] for x in gap_scan.find_drift()}
        assert drift == {"tools/drifter.py:2"}, "drift должно быть РОВНО {drifter.py:2}: %s" % drift
        # evidence должен называть и мёртвый, и живой каталог (иначе мутация карты не краснеет)
        dead = list(gap_scan.DEAD_DIR_LITERALS)[0]
        alive = gap_scan.DEAD_DIR_LITERALS[dead]
        ev = gap_scan.find_drift()[0]["evidence"]
        assert alive in ev and dead in ev, "evidence дрейфа должен называть и мёртвый, и живой каталог: %s" % ev

        # [planned]-строка (future_tool) пропущена, немаркированные ghost/ghost2 пойманы (C40)
        dangling = {x["name"] for x in gap_scan.find_dangling()}
        assert dangling == {"tools/ghost.py", "tools/ghost2.py"}, \
            "dangling должно быть РОВНО {ghost.py, ghost2.py} (future_tool с %s — не разрыв): %s" % (
                gap_scan.PLANNED_MARKER, dangling)

        # P8-b: dcard-детектор — все не-тестовые без [FILE ID CARD] пойманы, carded_tool чист
        dcards = {x["name"] for x in gap_scan.find_missing_dcards()}
        assert dcards == {"tools/orphan_tool.py", "tools/used_tool.py", "tools/drifter.py",
                          "tools/pipeline.py", "tools/fold.py"}, \
            "dcard должно флажить РОВНО не-тестовые без визитки: %s" % dcards
        assert "tools/carded_tool.py" not in dcards, "файл с [FILE ID CARD] не должен флажиться"

        # run() агрегирует все четыре; счётчики точные
        res = gap_scan.run()
        assert len(res["orphans"]) == 1 and len(res["drift"]) == 1 and len(res["dangling"]) == 2 \
            and len(res["dcard"]) == 5, \
            "run() агрегаты: %s" % {k: len(v) for k, v in res.items()}
        # выборочный запуск только dcard (используется хуком P8-b): rc=1 при находках
        assert gap_scan.main(["dcard", "--strict"]) == 1, "--strict при missing-dcard должен дать 1"

        # --strict → rc=1 при находках, rc=0 если детектор пуст
        assert gap_scan.main(["drift", "--strict"]) == 1, "--strict при дрейфе должен дать 1"
        # на пустом репо drift пуст → strict 0
        empty = tempfile.mkdtemp(prefix="gap_scan_empty_")
        os.makedirs(os.path.join(empty, "tools"))
        gap_scan.ROOT, gap_scan.TOOLS = empty, os.path.join(empty, "tools")
        try:
            assert gap_scan.main(["drift", "--strict"]) == 0, "пустой drift → strict 0"
        finally:
            shutil.rmtree(empty, ignore_errors=True)

        print("TESTS OK gap_scan: orphan(allowlist+C15-allowlist+doc-ref+self-test) · drift(dead-dir->alive, точная строка) · dangling([planned] пропущен) · dcard(P8-b: без визитки флажится, с визиткой нет) · strict 1/0")
        return 0
    finally:
        gap_scan.ROOT, gap_scan.TOOLS = saved
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
