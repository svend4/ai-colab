#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow backlog rescan tool.

Читает `темы/perspective-backlog-*.md`, ищет задачи, которые упоминаются в таблице `Ранжированный бэклог`
или списке `Готовы к запуску`, и сверяет их статусы с `tasks/*.md`.
Если задача выполнена (`status: done` или `closed`), скрипт предлагает перенести строку
в `Shipped / closed`.
"""

import os
import re
import sys
import glob
from _ioutil import configure_output

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import dispatch

configure_output()

def rescan():
    # Load tasks
    tasks = dispatch.load_tasks()
    done_tasks = {t_id: t for t_id, t in tasks.items() if t["status"] in ("done", "closed")}
    
    # Find backlog files
    backlogs = glob.glob(os.path.join(ROOT, "темы", "perspective-backlog-*.md"))
    if not backlogs:
        print("Не найдены файлы perspective-backlog-*.md")
        return
    
    # Sort by name (date) to pick the latest
    latest_backlog = sorted(backlogs)[-1]
    print(f"СКАНИРОВАНИЕ: {os.path.basename(latest_backlog)}")
    print("-" * 50)
    
    with open(latest_backlog, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.split("\n")
    suggestions = []
    
    in_ready = False
    in_ranked = False
    
    for i, line in enumerate(lines):
        if "## Готовы к запуску" in line:
            in_ready = True
            in_ranked = False
            continue
        elif "## Ранжированный бэклог" in line:
            in_ready = False
            in_ranked = True
            continue
        elif "## Shipped" in line or "## Как пользоваться" in line:
            in_ready = False
            in_ranked = False
            continue
            
        if not (in_ready or in_ranked):
            continue
            
        if not line.strip() or line.strip().startswith("| # |") or line.strip().startswith("|---"):
            continue
            
        # Skip lines already marked as shipped
        if "shipped T-" in line or "~~" in line:
            continue
            
        done_title_matches = []
        for d_id, d_task in done_tasks.items():
            if d_task["title"] and d_task["title"].lower() in line.lower():
                done_title_matches.append(d_id)
                
        if done_title_matches:
            section = "Готовы к запуску" if in_ready else "Ранжированный бэклог"
            m_str = ", ".join(done_title_matches)
            suggestions.append(f"Строка {i+1} ({section}) совпадает с заголовком завершённой задачи {m_str}:\n  > {line.strip()}\n  Рекомендуется перенести её в Shipped / closed.")

    if not suggestions:
        print("✅ Все задачи в бэклоге актуальны. Завершённых в активных секциях нет.")
    else:
        print("⚠️ НАЙДЕНЫ ВЫПОЛНЕННЫЕ ЗАДАЧИ В АКТИВНОМ БЭКЛОГЕ:\n")
        for s in suggestions:
            print(s)
            print()

if __name__ == "__main__":
    rescan()
