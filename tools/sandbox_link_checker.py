#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.sandbox_link_checker
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Проверка локальных Markdown ссылок во входящей песочнице (read-only)
# ==========================================
"""

import os
import sys
import re
import json

LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def check_markdown_file(filepath, base_dir):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {"file": filepath, "broken_links": [], "error": str(e)}

    broken_links = []
    file_dir = os.path.dirname(filepath)

    for match in LINK_REGEX.finditer(content):
        link_text, link_path = match.groups()
        
        # Игнорируем внешние ссылки и анкоры
        if link_path.startswith(("http://", "https://", "mailto:", "#")):
            continue
            
        # Удаляем анкор из локального пути, если есть
        link_path_clean = link_path.split("#")[0]
        if not link_path_clean:
            continue
            
        # Формируем абсолютный путь
        if link_path_clean.startswith("/"):
            # Если начинается со слэша, считаем от корня песочницы (base_dir)
            target_path = os.path.join(base_dir, link_path_clean.lstrip("/"))
        else:
            # Иначе относительно текущего файла
            target_path = os.path.join(file_dir, link_path_clean)
            
        if not os.path.exists(target_path):
            broken_links.append({"text": link_text, "target": link_path})
            
    return {"file": filepath, "broken_links": broken_links}

def scan_directory(target_dir):
    base_dir = os.path.abspath(target_dir)
    results = []
    
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".md"):
                md_path = os.path.join(root, f)
                res = check_markdown_file(md_path, base_dir)
                if res.get("error") or res.get("broken_links"):
                    results.append(res)
                    
    return results

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No directory provided"}))
        sys.exit(1)
        
    target = sys.argv[1]
    if not os.path.isdir(target):
        print(json.dumps({"error": f"Not a directory: {target}"}))
        sys.exit(1)
        
    issues = scan_directory(target)
    print(json.dumps({"files_with_issues": len(issues), "issues": issues}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
