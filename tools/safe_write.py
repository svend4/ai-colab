#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.safe_write
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: CLI-обёртка над _ioutil.safe_write — запись файла с предохранителем от массовой потери строк.
# ==========================================
"""safe_write.py — CLI над _ioutil.safe_write (предохранитель от потери данных).

Grow-only: НЕ дублирует логику предохранителя — импортирует `_ioutil.safe_write` (блокирует запись через
`DataLossGuardException`, если новое содержимое теряет >15% или >20 строк без `--force`). Ghost из
docs/friction-retrospective-2026-06-22 (рецепт «безопасной записи» против инцидента урезания). Контент
берётся из `--content`, файла (`--from`) или stdin.

CLI:
  python tools/safe_write.py <path> --content "..."          # записать строку
  echo "..." | python tools/safe_write.py <path>             # из stdin
  python tools/safe_write.py <path> --from SRC [--force]     # из файла; --force обходит предохранитель
"""
import os
import sys

from _ioutil import safe_write, DataLossGuardException, configure_output
from _cli import help_guard

configure_output()


VALUE_FLAGS = {"--content", "--from"}


def _opt(argv, flag):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return None


def _positional(argv):
    """Позиционные аргументы, ИСКЛЮЧАЯ значения value-флагов (иначе `--content z` ловит z как путь)."""
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a in VALUE_FLAGS:
            skip = True
            continue
        if a.startswith("--"):
            continue
        out.append(a)
    return out


def main(argv):
    help_guard(__doc__, argv)
    paths = _positional(argv)
    if not paths:
        sys.stderr.write("safe_write: нужен путь файла\n")
        return 2
    path = paths[0]
    content = _opt(argv, "--content")
    if content is None:
        src = _opt(argv, "--from")
        if src:
            content = open(src, encoding="utf-8").read()
        else:
            content = sys.stdin.read()
    try:
        safe_write(path, content, force_truncate=("--force" in argv))
        print("OK: записано %s (%d символов)" % (path, len(content)))
        return 0
    except DataLossGuardException as exc:
        sys.stderr.write("ПРЕДОХРАНИТЕЛЬ: %s\n  (используй --force, если урезание намеренное)\n" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
