#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Канонический helper UTF-8 вывода для инструментов канона (DEDUP, ревью находка).

Имя `_ioutil`, а не `_io`: `_io` — встроенный модуль CPython (C-ускоритель stdlib
`io`), он перехватывает `import _io` даже впереди `sys.path[0]`, поэтому файл с
таким именем недостижим и опасен. `_ioutil` коллизий не даёт.

Единый источник вместо ~40 идентичных копий boilerplate по `tools/*.py`. Каждый
тул сейчас повторяет два куска: `os.environ.setdefault("PYTHONUTF8", "1")` и
локальную `def configure_output(): ...` с циклом `sys.stdout/stderr.reconfigure`.
Логика тут намеренно идентична прежним копиям, чтобы консолидация не меняла
поведение: PYTHONUTF8 ставится через setdefault (не перетирает явный env), а
stdout/stderr переключаются на utf-8 с errors="replace" только если у потока есть
`reconfigure` (py3.7+) и он не None (поток мог быть перехвачен/закрыт).

Использование в туле — заменяет 5 строк (env + def + вызов) на 2:

    from _ioutil import configure_output
    configure_output()
"""
import os
import sys


def configure_output():
    """Включить UTF-8 для PYTHONUTF8 и stdout/stderr (идемпотентно, без падений).

    setdefault не трогает уже выставленный PYTHONUTF8; reconfigure вызывается
    только при наличии метода и непустого потока, как в прежних копиях.
    """
    os.environ.setdefault("PYTHONUTF8", "1")
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
