#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_drift_title_quote
# TYPE: active-script
# DOMAIN: core.drift
# DEPTH_LEVEL: 2
# SUMMARY: Тест исключения цитат титулов в drift_check: L0-L8 в строке-цитате dcard_index не дрейф, живой L0-L8 — дрейф.
# ==========================================
"""Тест точечного исключения строк-цитат титулов в scan_layer_drift — «самопроверено».

Кейс из аудита: генерируемый docs/dcard_index.md цитирует title исторической задачи
T-032 «Карта покрытия слоёв L0–L8» в табличной строке со ссылкой `[...](../tasks/T-032.md)`.
Цитата титула в деривате-цитатнике — не дрейф канона (T-032 не переименовываем — история),
а живой L0-L8 в обычном doc обязан флажиться по-прежнему. Исключение точечное (по строке,
регэксп _TITLE_QUOTE_ROW), а не по файлу: живая строка в том же файле всё равно ловится.

Пишется pytest-collectable (конвенция tools/tests/ по Q-W2-3/C13-c).
"""
# --- бутстрап путей (C14): тест живёт в tools/tests/, инструменты — в tools/.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys

import drift_check as dc

# Реальная строка-цитата из docs/dcard_index.md (титул T-032, en dash в L0–L8)
QUOTE_ROW = ("| `T-032` | task | - | [T-032.md](../tasks/T-032.md) "
             "| Карта покрытия слоёв L0–L8 (docs/layers-coverage.md) |\n")


def _write(docs, name, text):
    os.makedirs(docs, exist_ok=True)
    with open(os.path.join(docs, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def test_title_quote_row_regex():
    # табличная строка с относительной markdown-ссылкой — цитата чужого титула
    assert dc._TITLE_QUOTE_ROW.match(QUOTE_ROW)
    # обычная проза и таблица без ссылки-цитаты — НЕ цитата (сканируются как раньше)
    assert not dc._TITLE_QUOTE_ROW.match("живая нумерация L0-L8 в прозе\n")
    assert not dc._TITLE_QUOTE_ROW.match("| колонка | L0-L8 без ссылки |\n")


def test_quote_in_generated_index_not_flagged(tmp_path):
    docs = os.path.join(str(tmp_path), "docs")
    # дериват-цитатник: заголовок + строка-цитата титула T-032 (как в docs/dcard_index.md)
    _write(docs, "dcard_index.md",
           "# D-Card Global Index (Control Plane)\n\n"
           "| ID | Type | Depth | File | Summary |\n|---|---|---|---|---|\n" + QUOTE_ROW)
    assert dc.scan_layer_drift(docs) == [], \
        "цитата титула в генерируемом индексе не должна считаться дрейфом"


def test_live_layer_drift_still_flagged(tmp_path):
    docs = os.path.join(str(tmp_path), "docs")
    # живой doc с L0-L8 как нумерацией — дрейф, как и раньше (дефис и en dash)
    _write(docs, "live.md", "# Слои\n\nсистема слоёв L0-L8 покрывает всё\n")
    _write(docs, "clean.md", "# Ок\n\nканон L0-L7\n")
    assert dc.scan_layer_drift(docs) == ["live.md"]


def test_quote_and_live_line_in_same_file_flagged(tmp_path):
    # исключение точечное (по строке): файл с цитатой И живой строкой всё равно флажится
    docs = os.path.join(str(tmp_path), "docs")
    _write(docs, "mixed.md", QUOTE_ROW + "\nживая нумерация L0-L8 в прозе\n")
    assert dc.scan_layer_drift(docs) == ["mixed.md"], \
        "живая L0-L8-строка не должна маскироваться соседней цитатой"


if __name__ == "__main__":
    # standalone-запуск (двухступенчатый канон: файл гоняет и test_all.py)
    import tempfile
    import shutil
    failed = 0
    test_title_quote_row_regex()
    for fn in (test_quote_in_generated_index_not_flagged,
               test_live_layer_drift_still_flagged,
               test_quote_and_live_line_in_same_file_flagged):
        tmp = tempfile.mkdtemp(prefix="drift_quote_")
        try:
            fn(tmp)
        except AssertionError as e:
            failed += 1
            print("TEST FAIL (%s): %s" % (fn.__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if failed:
        sys.exit(1)
    print("TESTS OK drift_title_quote: regex цитаты + dcard_index-цитата не флажится + "
          "живой L0-L8 флажится + точечность по строке (mixed-файл ловится)")
    sys.exit(0)
