#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cauldron Task Materializer (T-276)
Служит мостом между абстрактным консенсусом "Котла" (Synthesis Report)
и строгим графом задач (tasks/T-*.md). 

Парсит секции:
- new_task_candidates
- decisions_needed
- route.ratify_build
- route.divergence_detail

Режимы:
  plan  - Dry-run: выводит, какие задачи/решения были бы созданы.
  apply - Реально создает заглушки через tools/next_id.py.
"""

import os
import sys
import argparse
import re
import subprocess
import json

def parse_synthesis_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    candidates = []
    
    # Очень простой блочный парсер на основе заголовков
    # Мы ищем заголовки, указывающие на необходимость материализации
    
    # 1. new_task_candidates
    task_match = re.search(r'(?i)#+.*?new_task_candidates(.*?)(?=\n#+ |\Z)', content, re.DOTALL)
    if task_match:
        lines = task_match.group(1).strip().split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                candidates.append({'type': 'task', 'title': line.strip()[1:].strip(), 'source': 'new_task_candidates'})

    # 2. decisions_needed
    dec_match = re.search(r'(?i)#+.*?decisions_needed(.*?)(?=\n#+ |\Z)', content, re.DOTALL)
    if dec_match:
        lines = dec_match.group(1).strip().split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                candidates.append({'type': 'decision', 'title': f"Decision needed: {line.strip()[1:].strip()}", 'source': 'decisions_needed'})

    # 3. route.ratify_build
    ratify_match = re.search(r'(?i)#+.*?route\.ratify_build(.*?)(?=\n#+ |\Z)', content, re.DOTALL)
    if ratify_match:
        lines = ratify_match.group(1).strip().split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                candidates.append({'type': 'task', 'title': f"Ratify Build: {line.strip()[1:].strip()}", 'source': 'route.ratify_build'})

    # 4. route.divergence_detail
    div_match = re.search(r'(?i)#+.*?route\.divergence_detail(.*?)(?=\n#+ |\Z)', content, re.DOTALL)
    if div_match:
        lines = div_match.group(1).strip().split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                candidates.append({'type': 'task', 'title': f"Divergence Resolution: {line.strip()[1:].strip()}", 'source': 'route.divergence_detail'})

    return candidates

def run_plan(filepath, output_json=False):
    candidates = parse_synthesis_file(filepath)
    if output_json:
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
        return
        
    print(f"=== CAULDRON MATERIALIZER PLAN ===")
    print(f"Source: {filepath}")
    print(f"Discovered items to materialize: {len(candidates)}\n")
    
    for idx, c in enumerate(candidates, 1):
        print(f"{idx}. [{c['type'].upper()}] {c['title']} (from: {c['source']})")
        
    print("\nNote: This is a dry-run. No files were created.")
    print("To materialize, use: python tools/cauldron_task_materializer.py apply <file> --agent <agent_name>")

def run_apply(filepath, agent):
    candidates = parse_synthesis_file(filepath)
    print(f"=== CAULDRON MATERIALIZER APPLY ===")
    print(f"Source: {filepath}")
    print(f"Agent: {agent}")
    print(f"Items to materialize: {len(candidates)}\n")
    
    for c in candidates:
        print(f"-> Materializing [{c['type']}] {c['title'][:50]}...")
        # Call next_id.py
        cmd = [sys.executable, "tools/next_id.py", c['type'], "--agent", agent]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            # next_id returns format: "ID: T-123\nPATH: tasks/T-123.md\nTOKEN: abcdef"
            id_match = re.search(r'([A-Z]-\d{3})', output)
            path_match = re.search(r'(tasks/[A-Z]-\d{3}\.md|decisions/[A-Z]-\d{3}\.md)', output)
            
            if id_match and path_match:
                new_id = id_match.group(1).strip()
                path = path_match.group(1).strip()
                print(f"   Success: Created {new_id} at {path}")
                
                # Append the specific title and context to the stub file
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(f"\n## Auto-Materialized Context\n")
                    f.write(f"- **Source file:** `{filepath}`\n")
                    f.write(f"- **Section:** `{c['source']}`\n")
                    f.write(f"- **Original extract:** {c['title']}\n")
            else:
                print(f"   Warning: Could not parse output from next_id.py:\n{output}")
                
        except subprocess.CalledProcessError as e:
            print(f"   ERROR: Failed to run next_id.py. \n{e.stderr}")

    print("\nMaterialization complete. Next steps:")
    print("1. Edit the generated stubs in tasks/ or decisions/ to add details.")
    print("2. Run: python tools/generate.py")
    print("3. Run: python tools/validate.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cauldron Task Materializer (Dry-run by default)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    plan_parser = subparsers.add_parser("plan", help="Dry-run creation of candidates")
    plan_parser.add_argument("file", help="Path to synthesis/cauldron report")
    plan_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    apply_parser = subparsers.add_parser("apply", help="Create task stubs using next_id.py")
    apply_parser.add_argument("file", help="Path to synthesis/cauldron report")
    apply_parser.add_argument("--agent", required=True, help="Agent name claiming the creation")
    
    args = parser.parse_args()
    
    if args.command == "plan":
        run_plan(args.file, args.json)
    elif args.command == "apply":
        run_apply(args.file, args.agent)
