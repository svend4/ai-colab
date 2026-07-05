#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.conftest
# TYPE: active-script
# DOMAIN: core.testing
# DEPTH_LEVEL: 2
# SUMMARY: pytest-инфраструктура tools/tests/: sys.path-бутстрап (tools/, drivers/) + fixture root (C12-a).
# ==========================================
"""
"""conftest.py — общая pytest-инфраструктура тестового контура tools/tests/.

Два назначения (C12-a + C14-c, аудит 2026-07-02, план fix-wave2):

1. sys.path-бутстрап. Тесты перенесены из tools/ в tools/tests/ (C14: шардинг tools/,
   снятие dir_health FAIL 244>200), но импортируют инструменты как top-level модули
   (`import metrics`, `from _canon import parse_front_matter`). pytest импортирует
   conftest.py ДО модулей тестов, поэтому вставка tools/ (и drivers/ — часть тестов
   импортирует драйверы) в sys.path здесь покрывает pytest-прогон. Standalone-запуски
   (`python tools/tests/test_x.py`) покрыты бутстрап-блоком в самих файлах.

2. Fixture `root` (C12-a). Шесть тестов (test_capabilities, test_drivers_catalog,
   test_metrics) написаны как самозапускающиеся скрипты: их run() создаёт tmp-каталог,
   вызывает модульную функцию подготовки фикстур (make_drivers/make_canon) и передаёт
   каталог позиционным аргументом `root`. Pytest трактовал `root` как отсутствующую
   fixture → 6 ERROR «fixture 'root' not found». Fixture повторяет контракт run():
   tmp_path + вызов make_*-функции модуля теста, возвращает строковый путь.

Конвенция для НОВЫХ тестов tools/tests/ (зафиксирована по Q-W2-3, двухступенчатый канон):
  - быстрый прогон:  py -3 -m pytest tools/tests/
  - полный прогон:   python tools/test_all.py  (самозапускающиеся __main__-скрипты)
  - новые файлы писать pytest-collectable (module-level test_*, fixtures);
    миграция старых скриптов — органически при касании (C13-c).
"""
import os
import sys

import pytest

# tools/tests/ → tools/ → корень репозитория
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(_TESTS_DIR)
REPO_ROOT = os.path.dirname(TOOLS_DIR)

# Бутстрап ДО импорта модулей тестов: инструменты (tools/) и драйверы (drivers/) —
# top-level импорты в тестах. Вставляем только отсутствующие пути, без дублей.
for _p in (TOOLS_DIR, os.path.join(REPO_ROOT, "drivers")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture
def root(request, tmp_path):
    """Временный канон/каталог фикстур — повторяет то, что делает run() скриптов.

    Контракт (C12-a): run() самозапускающегося скрипта делает
        tmp = tempfile.mkdtemp(); make_drivers(tmp) | make_canon(tmp); test_x(tmp)
    Fixture воспроизводит ровно это: tmp_path (pytest сам чистит) + первая найденная
    модульная функция подготовки (make_drivers/make_canon) + строковый путь наружу
    (тесты используют os.path.join/COLLAB_ROOT — строка, не pathlib.Path).
    """
    base = str(tmp_path)
    for name in ("make_drivers", "make_canon"):
        maker = getattr(request.module, name, None)
        if callable(maker):
            maker(base)
            break
    return base
