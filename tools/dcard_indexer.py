#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.dcard_indexer
# TYPE: active-script
# DOMAIN: core.indexing
# DEPTH_LEVEL: 1
# SUMMARY: Генератор индексов D-Card. Сканирует файлы проекта, извлекает визитки (D-Cards) и строит карту.
# ==========================================

Генератор D-Card Index.
"""
import os
import sys
import json
import re
from _canon import parse_front_matter
from _cli import help_guard

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# tmp-work/.claude — gitignored runtime-копии (mutmeta-песочницы, чужие worktrees):
# их D-Card — дубликаты канона со СТАРЫМИ путями; в каноническом индексе они дают
# шум (87 висячих ссылок G5 после переноса тестов C14) и раздувают dcard_index.md.
EXCLUDE_DIRS = ['.git', '__pycache__', 'venv', '.gemini', '.agents', 'queues', 'logs',
                'tmp-work', '.claude', 'node_modules', '.pytest_cache', '.idea']

DCARD_REGEX = re.compile(r'# \[FILE ID CARD\]\n(.*?)(?:# ==========================================)', re.DOTALL)

def extract_py_dcard(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            head = "".join([f.readline() for _ in range(30)])
    except (OSError, UnicodeDecodeError):
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

def extract_md_dcard(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            head = "".join([f.readline() for _ in range(30)])
    except (OSError, UnicodeDecodeError):
        return None

    if not head.startswith('---'):
        return None

    # Канонический парсер front-matter (_canon) вместо yaml.safe_load:
    # визитки — простые пары key: value, полноценный YAML не нужен,
    # а единственная сторонняя зависимость tools/ (PyYAML) исчезает.
    card = parse_front_matter(head)
    return card or None

def build_index():
    cards = []
    
    for root, dirs, files in os.walk(ROOT):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, ROOT).replace('\\', '/')
            
            card = None
            if file.endswith('.py'):
                card = extract_py_dcard(full_path)
            elif file.endswith('.md'):
                card = extract_md_dcard(full_path)
                
            if card:
                card['_filepath'] = rel_path
                cards.append(card)
                
    return cards

def write_markdown_index(cards):
    out_path = os.path.join(ROOT, 'docs', 'dcard_index.md')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # Sort by domain or type if available
    cards.sort(key=lambda x: (x.get('domain', ''), x.get('id', '')))
    
    with open(out_path, 'w', encoding='utf-8', newline="\n") as f:
        f.write("# D-Card Global Index (Control Plane)\n\n")
        f.write("> Автосгенерированный реестр файлов с метаданными (D-Cards).\n\n")
        
        # Group by domain
        domains = {}
        for c in cards:
            domain = c.get('domain', 'uncategorized')
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(c)
            
        for domain in sorted(domains.keys()):
            f.write(f"## Domain: {domain}\n\n")
            f.write("| ID | Type | Depth | File | Summary |\n")
            f.write("|---|---|---|---|---|\n")
            
            for c in domains[domain]:
                cid = c.get('id', 'unknown')
                ctype = c.get('type', '-')
                cdepth = c.get('depth_level', '-')
                filepath = c.get('_filepath', '-')
                summary = c.get('summary', c.get('title', ''))
                
                f.write(f"| `{cid}` | {ctype} | {cdepth} | [{os.path.basename(filepath)}](../{filepath}) | {summary} |\n")
            f.write("\n")
            
    print(f"Index created at {out_path} with {len(cards)} D-Cards.")

if __name__ == '__main__':
    help_guard(__doc__)
    cards = build_index()
    write_markdown_index(cards)
