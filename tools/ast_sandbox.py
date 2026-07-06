#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST-Sandbox Guard (D-036)
Статический анализатор Python-кода для предотвращения исполнения деструктивного
кода или логических бомб, написанных агентами.

Использование:
    python tools/ast_sandbox.py <file1.py> [<file2.py> ...]
"""

import ast
import sys
import os

class SandboxVisitor(ast.NodeVisitor):
    def __init__(self, filename, source_code):
        self.filename = filename
        self.source_code = source_code
        self.errors = []
        
        # Check for inline pragmas
        self.allow_subprocess = "# ast: allow-subprocess" in source_code
        self.allow_eval = "# ast: allow-eval" in source_code
        self.allow_loops = "# ast: allow-loops" in source_code

    def visit_While(self, node):
        if not self.allow_loops:
            # Check if it's while True:
            is_infinite = False
            if isinstance(node.test, ast.Constant):
                if node.test.value is True or node.test.value == 1:
                    is_infinite = True
            elif isinstance(node.test, ast.Name):
                if node.test.id == 'True':
                    is_infinite = True
                    
            if is_infinite:
                # Look for break, return, raise
                class BreakFinder(ast.NodeVisitor):
                    def __init__(self):
                        self.found = False
                    def visit_Break(self, n): self.found = True
                    def visit_Return(self, n): self.found = True
                    def visit_Raise(self, n): self.found = True
                    
                finder = BreakFinder()
                for stmt in node.body:
                    finder.visit(stmt)
                    
                if not finder.found:
                    self.errors.append(f"Line {node.lineno}: Infinite loop (while True) without break/return/raise found.")
                    
        self.generic_visit(node)

    def visit_Call(self, node):
        # check for eval / exec
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ('eval', 'exec') and not self.allow_eval:
                self.errors.append(f"Line {node.lineno}: Usage of '{func_name}' is forbidden.")
                
        # check for os.system / subprocess.*
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                attr_name = node.func.attr
                
                if not self.allow_subprocess:
                    if module_name == 'os' and attr_name in ('system', 'popen'):
                        self.errors.append(f"Line {node.lineno}: Usage of 'os.{attr_name}' is forbidden.")
                    elif module_name == 'subprocess':
                        self.errors.append(f"Line {node.lineno}: Usage of 'subprocess.{attr_name}' is forbidden.")
                        
        self.generic_visit(node)


def check_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            
        tree = ast.parse(source, filename=filepath)
        visitor = SandboxVisitor(filepath, source)
        visitor.visit(tree)
        
        return visitor.errors
    except SyntaxError as e:
        return [f"Line {e.lineno}: SyntaxError - {e.msg}"]
    except Exception as e:
        return [f"Error parsing file: {e}"]


def main():
    if len(sys.argv) < 2:
        print("Usage: ast_sandbox.py <file1.py> [<file2.py> ...]")
        return 2

    files = sys.argv[1:]
    has_errors = False
    
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"WARN: File {filepath} not found.")
            continue
            
        errors = check_file(filepath)
        if errors:
            has_errors = True
            print(f"ERROR: {filepath} failed AST sandbox check:")
            for err in errors:
                print(f"  - {err}")
                
    if has_errors:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
