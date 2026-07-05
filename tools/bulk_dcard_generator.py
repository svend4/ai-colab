#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.bulk_dcard_generator
# TYPE: active-script
# DOMAIN: core.indexing
# DEPTH_LEVEL: 1
# SUMMARY: Автоматически добавляет D-Cards во все python-скрипты в tools/, у которых их нет.
# ==========================================
"""

import os
import re
from _cli import help_guard
from _ioutil import safe_write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS_DIR = os.path.join(ROOT, "tools")

DCARD_REGEX = re.compile(r'# \[FILE ID CARD\]')

def generate_dcard(basename):
    name_without_ext = os.path.splitext(basename)[0]
    return f'''"""
# ==========================================
# [FILE ID CARD]
# ID: tools.{name_without_ext}
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт {basename}. Описание сгенерировано автоматически.
# ==========================================
"""
'''

def process_file(filepath, basename):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if DCARD_REGEX.search(content):
        return False # Already has D-Card

    lines = content.split('\n')
    
    # Find insertion point (after shebang and coding lines)
    insert_idx = 0
    for i, line in enumerate(lines[:5]):
        if line.startswith('#!/usr/bin/env') or line.startswith('# -*- coding'):
            insert_idx = i + 1
            
    dcard_text = generate_dcard(basename)
    
    lines.insert(insert_idx, dcard_text.strip())
    
    # C33: рукописный исходник tools/*.py переписывается ЦЕЛИКОМ — safe_write даёт
    # гвард потери данных (вставка D-Card только ДОБАВЛЯЕТ строки, законного сжатия
    # тут не бывает — срабатывание гварда означало бы баг) плюс атомарность tmp+replace.
    safe_write(filepath, '\n'.join(lines))

    return True

def main():
    help_guard(__doc__)
    added = 0
    for root, dirs, files in os.walk(TOOLS_DIR):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                if process_file(full_path, file):
                    added += 1
                    
    print(f"Готово. Добавлено {added} D-Cards в файлы tools/")

if __name__ == "__main__":
    main()
