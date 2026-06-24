#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.enforce_metadata
# TYPE: active-script
# DOMAIN: core.indexing
# DEPTH_LEVEL: 1
# SUMMARY: Проверяет наличие и валидность D-Cards во всех файлах tools/.
# ==========================================
"""

import os
import sys
import re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS_DIR = os.path.join(ROOT, "tools")

REQUIRED_FIELDS = {"id", "type", "domain", "depth_level", "summary"}
DCARD_REGEX = re.compile(r'# \[FILE ID CARD\]\n(.*?)(?:# ==========================================)', re.DOTALL)

def extract_py_dcard(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            head = "".join([f.readline() for _ in range(30)])
    except Exception:
        return None

    match = DCARD_REGEX.search(head)
    if not match:
        return None
    
    lines = match.group(1).strip().split('\n')
    card = {}
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            parts = line[2:].split(':', 1)
            if len(parts) == 2:
                card[parts[0].strip().lower()] = parts[1].strip()
    return card

import argparse

def main():
    parser = argparse.ArgumentParser(description="Enforce D-Cards in tools/")
    parser.add_argument("--warn-only", action="store_true", help="Soft mode, do not fail on missing D-Cards")
    args = parser.parse_args()

    errors = 0
    for root, dirs, files in os.walk(TOOLS_DIR):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for file in files:
            if not file.endswith(".py"):
                continue
            
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, ROOT).replace('\\', '/')
            
            card = extract_py_dcard(full_path)
            if not card:
                print(f"ОШИБКА: Нет D-Card (или неверный формат) в {rel_path}")
                errors += 1
                continue
            
            missing = REQUIRED_FIELDS - set(card.keys())
            if missing:
                print(f"ОШИБКА: В D-Card файла {rel_path} отсутствуют обязательные поля: {', '.join(missing)}")
                errors += 1

    if errors > 0:
        print(f"\nИТОГО ОШИБОК: {errors}. Сделайте D-Cards обязательными во всех инструментах!")
        if args.warn_only:
            print("Soft mode enabled (--warn-only). Exiting with code 0.")
            sys.exit(0)
        sys.exit(1)
    else:
        print("OK: Все скрипты в tools/ имеют правильные D-Cards.")
        sys.exit(0)

if __name__ == "__main__":
    main()
