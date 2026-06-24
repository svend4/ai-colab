#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.python_analyzer
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Семантический AST-анализатор Python кода (read-only)
# ==========================================
"""

import ast
import json
import sys
import os

DANGEROUS_MODULES = {"os", "sys", "subprocess", "socket", "requests", "urllib", "http", "shutil"}
DANGEROUS_FUNCS = {"eval", "exec", "__import__", "open"}

def analyze_python_file(filepath):
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    imports = []
    classes = []
    functions = []
    risks = []

    for node in ast.walk(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                if alias.name.split('.')[0] in DANGEROUS_MODULES:
                    risks.append(f"Dangerous import: {alias.name}")
        
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            for alias in node.names:
                full_name = f"{mod_name}.{alias.name}" if mod_name else alias.name
                imports.append(full_name)
            if mod_name.split('.')[0] in DANGEROUS_MODULES:
                risks.append(f"Dangerous from-import: {mod_name}")

        # Classes
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

        # Functions
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            functions.append(node.name)

        # Function Calls (eval, exec, etc.)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in DANGEROUS_FUNCS:
                    risks.append(f"Dangerous function call: {node.func.id}")

    return {
        "file": filepath,
        "imports": list(set(imports)),
        "classes": classes,
        "functions": functions,
        "risks": list(set(risks)),
        "status": "ok"
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file provided"}))
        sys.exit(1)
        
    target = sys.argv[1]
    result = analyze_python_file(target)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
