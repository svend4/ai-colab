#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ast: allow-subprocess
import os
import sys
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_git(args):
    # run git command and return output
    cmd = ["git"] + args
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def get_file_creation_date(filepath):
    # This might return multiple lines if the file was deleted and recreated.
    # We take the oldest date (the last one in the output).
    out = run_git(["log", "--diff-filter=A", "--format=%aI", "--", filepath])
    if not out:
        return None
    lines = [line.strip() for line in out.split('\n') if line.strip()]
    if lines:
        return lines[-1] # oldest addition
    return None

def get_historical_content(date, filename="DECISIONS.md"):
    # Find the commit just before or exactly on this date
    commit_hash = run_git(["rev-list", "-n", "1", f"--before={date}", "HEAD"])
    if not commit_hash:
        return None
        
    # Get the content of the file at that commit
    content = run_git(["show", f"{commit_hash}:{filename}"])
    return content, commit_hash

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/chrono_guard.py <filepath>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    rel_target = os.path.relpath(target_file, ROOT).replace('\\', '/')
    
    date_str = get_file_creation_date(rel_target)
    if not date_str:
        print(f"Error: Could not determine creation date for {rel_target}. Is it tracked by git?")
        sys.exit(1)
        
    print(f"File {rel_target} was created on: {date_str}")
    
    historical_content, commit_hash = get_historical_content(date_str, "DECISIONS.md")
    if not historical_content:
        print("Could not retrieve DECISIONS.md from that time. Maybe it didn't exist yet?")
        sys.exit(1)
        
    # Create the report
    basename = os.path.basename(target_file).replace('.md', '').replace('.py', '')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"chrono_{basename}_{timestamp}.md"
    reports_dir = os.path.join(ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    report_path = os.path.join(reports_dir, report_name)
    
    lines = [
        f"# Хроно-Контекст: {rel_target}",
        f"**Дата создания:** {date_str}",
        f"**Коммит состояния:** {commit_hash}",
        "",
        "> [!IMPORTANT]",
        "> Этот файл содержит исторический контекст. Когда агент работает с очень старым файлом,",
        "> он должен руководствоваться **этими** правилами, чтобы не сломать логику того времени,",
        "> либо осознанно выполнить рефакторинг в соответствии с новыми правилами.",
        "",
        "## Состояние DECISIONS.md на момент создания файла:",
        "```markdown",
        historical_content,
        "```"
    ]
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    print(f"Chrono-Context generated: {os.path.relpath(report_path, ROOT)}")
    print("No original files were modified.")

if __name__ == "__main__":
    main()
