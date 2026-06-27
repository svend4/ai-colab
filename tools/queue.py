#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.queue
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Совместимостный алиас на agent_queue.py (историческое имя queue.py из доков, T-009).
# ==========================================
"""queue.py — совместимостный алиас на agent_queue.py (Queue 2.0).

Историческое имя `queue.py` фигурирует в docs/glossary.md, tools/README.md и истории (T-009), но модуль
был переименован в `agent_queue.py`. Команды `python tools/queue.py ...` из доков переставали работать
(висячая ссылка, G5). Этот тонкий shim делегирует в agent_queue — логика НЕ дублируется. Grow-only:
новый файл-обёртка, agent_queue.py не тронут (D-032).

CLI: те же подкоманды, что у agent_queue.py (list/claim/complete/fail/release/check).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_queue


def main(argv=None):
    sys.stderr.write("queue.py — алиас, канонический модуль: agent_queue.py (T-009/D-032)\n")
    return agent_queue.main()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
