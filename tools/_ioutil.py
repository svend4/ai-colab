#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools._ioutil
# TYPE: helper-module
# DOMAIN: core.io
# DEPTH_LEVEL: 1
# SUMMARY: Единый helper UTF-8 вывода для CLI-инструментов репозитория.
# ==========================================
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
import uuid


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


class DataLossGuardException(Exception):
    """Исключение, выбрасываемое при попытке удалить слишком много данных из файла."""
    pass


def atomic_write(filepath, text, newline="\n"):
    """Атомарная запись текста: tmp-файл рядом + os.replace (аудит C11/C49).

    Прямой `open(path, "w")` сначала усекает файл до нуля: падение процесса
    (kill/OOM/disk-full) между truncate и write теряет ВЕСЬ файл. Здесь контент
    пишется во временный файл рядом, затем атомарно подменяет оригинал через
    os.replace — читатель никогда не видит пустой/усечённый файл. Паттерн тот же,
    что в pipeline.cmd_heartbeat/try_claim; при сбое tmp-хвост подчищается.
    """
    tmp = "%s.tmp.%s" % (filepath, uuid.uuid4().hex[:8])
    try:
        with open(tmp, "w", encoding="utf-8", newline=newline) as f:
            f.write(text)
        os.replace(tmp, filepath)
    finally:
        # не оставлять tmp-хвостов, если запись/подмена упала
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def safe_write(filepath, new_content, force_truncate=False, max_loss_ratio=0.15, max_loss_lines=20):
    """Безопасная запись с предохранителем от случайного удаления данных.

    Сравнивает старый и новый размер файла (если файл существует).
    Блокирует запись, если новый контент меньше старого более чем на `max_loss_ratio` (по умолчанию 15%)
    ИЛИ если удалено больше `max_loss_lines` строк.

    Для обхода предохранителя необходимо явно передать `force_truncate=True`.
    """
    if os.path.exists(filepath) and not force_truncate:
        with open(filepath, "r", encoding="utf-8") as f:
            old_content = f.read()

        old_len = len(old_content)
        new_len = len(new_content)

        old_lines = len(old_content.splitlines())
        new_lines = len(new_content.splitlines())

        if old_len > 0 and new_len < old_len:
            loss_ratio = (old_len - new_len) / old_len
            line_loss = old_lines - new_lines

            if loss_ratio > max_loss_ratio or line_loss > max_loss_lines:
                raise DataLossGuardException(
                    f"DATA LOSS GUARD: Попытка удалить слишком много данных в {filepath}.\n"
                    f"Удаляется {old_len - new_len} байт ({loss_ratio*100:.1f}%) и {line_loss} строк.\n"
                    f"Предохранитель сработал (допустимо: {max_loss_ratio*100}% или {max_loss_lines} строк).\n"
                    f"Используйте force_truncate=True, если это удаление намеренно."
                )

    # Если всё хорошо или это новый файл (записываем с unix-переносами).
    # Атомарно: tmp + os.replace — краш между truncate и write больше не может
    # оставить пустой/усечённый файл (аудит C11).
    atomic_write(filepath, new_content)
