#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ast: allow-subprocess
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Regex for matching D-xxx, T-xxx, Q-xxx, etc.
ID_PATTERN = re.compile(r'\b([DQT]-\d{3})\b')
# Regex for matching markdown links [text](path)
LINK_PATTERN = re.compile(r'\[.*?\]\((.*?)\)')

def find_markdowns():
    md_files = []
    # Root markdown files
    for root_file in ['DECISIONS.md', 'TASKS.md', 'QUESTIONS.md', 'STATUS.md', 'PROTOCOL.md']:
        path = os.path.join(ROOT, root_file)
        if os.path.exists(path):
            md_files.append(root_file)
            
    # Folders to scan
    for folder in ['docs', 'tasks', 'topics', 'decisions']:
        dir_path = os.path.join(ROOT, folder)
        if not os.path.isdir(dir_path):
            continue
        for dirpath, _, filenames in os.walk(dir_path):
            for f in filenames:
                if f.endswith('.md'):
                    rel_path = os.path.relpath(os.path.join(dirpath, f), ROOT).replace('\\', '/')
                    md_files.append(rel_path)
    return md_files

def extract_core_invariants(content, max_lines=20):
    lines = content.split('\n')
    extracted = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('> [!') or stripped.startswith('- '):
            extracted.append(stripped)
        if len(extracted) >= max_lines:
            break
    return "\n".join(extracted)

def main():
    md_files = find_markdowns()
    
    # Map filenames to their contents for faster access
    contents = {}
    for mf in md_files:
        try:
            with open(os.path.join(ROOT, mf), 'r', encoding='utf-8') as f:
                contents[mf] = f.read()
        except Exception:
            pass
            
    # Step 1: Build Knowledge Graph
    graph = defaultdict(list)
    
    # We also want to map IDs to filenames, since many link by ID
    id_to_file = {}
    for mf in md_files:
        # Simplistic heuristic: if filename starts with D-XXX, map it
        basename = os.path.basename(mf)
        match = re.match(r'^([DQT]-\d{3})', basename)
        if match:
            id_to_file[match.group(1)] = mf

    for mf, text in contents.items():
        # Find explicit links
        for link in LINK_PATTERN.findall(text):
            # Very basic cleanup (remove hashes, parameters)
            link = link.split('#')[0].split('?')[0]
            if link in contents:
                graph[mf].append(link)
        
        # Find ID mentions
        for id_mention in ID_PATTERN.findall(text):
            if id_mention in id_to_file:
                target = id_to_file[id_mention]
                if target != mf:  # don't link to self
                    graph[mf].append(target)
                    
    # Step 2: PageRank (Pure Python)
    d = 0.85
    N = len(contents)
    if N == 0:
        print("No markdown files found.")
        return
        
    pr = {node: 1.0 / N for node in contents}
    
    for _ in range(20): # Iterations
        new_pr = {}
        for node in contents:
            # sum of (pr(T) / C(T)) for all T pointing to node
            pointing_sum = 0.0
            for other_node, out_links in graph.items():
                if node in out_links:
                    pointing_sum += pr[other_node] / len(out_links)
            new_pr[node] = (1 - d) / N + d * pointing_sum
        pr = new_pr
        
    # Step 3: Distillation
    # Get top 15 most important nodes
    top_nodes = sorted(pr.keys(), key=lambda k: pr[k], reverse=True)[:15]
    
    hologram_lines = [
        "---",
        "title: Holographic Snapshot",
        "status: generated",
        "---",
        "# HOLOGRAPHIC SNAPSHOT (Авто-генерируемый концентрат знаний)",
        "Этот файл содержит сжатую выжимку самых «весомых» документов репозитория (по метрике PageRank графа связей).",
        "Предназначен для быстрого восстановления контекста.",
        ""
    ]
    
    for node in top_nodes:
        hologram_lines.append(f"## Узел: [{node}]({node}) (вес: {pr[node]:.4f})")
        hologram_lines.append(extract_core_invariants(contents[node]))
        hologram_lines.append("")
        
    indexes_dir = os.path.join(ROOT, 'indexes')
    os.makedirs(indexes_dir, exist_ok=True)
    out_path = os.path.join(indexes_dir, 'hologram.md')
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(hologram_lines))
        
    print(f"Hologram generated successfully: indexes/hologram.md ({len(top_nodes)} core nodes)")

if __name__ == "__main__":
    main()
