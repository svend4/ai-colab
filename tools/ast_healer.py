#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ast: allow-subprocess
import os
import sys
import ast

def get_output_path(original_path):
    """
    Generates a new filename so we never overwrite original files!
    e.g. script.py -> script_healed.py
    """
    base, ext = os.path.splitext(original_path)
    return f"{base}_healed{ext}"

class HealingTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.healed_count = 0

    def visit_Call(self, node):
        self.generic_visit(node)
        
        # Detect subprocess.run or subprocess.Popen or os.system
        is_forbidden = False
        
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'subprocess' and node.func.attr in ('run', 'Popen'):
                    is_forbidden = True
                elif node.func.value.id == 'os' and node.func.attr == 'system':
                    is_forbidden = True
                    
        if is_forbidden:
            self.healed_count += 1
            # Replace with:
            # print("HEALED: subprocess/os.system call was intercepted.")
            # raise RuntimeError("Use sandbox_runner.py instead of raw subprocess")
            # 
            # In AST form: 
            # Let's just replace it with a simple print statement for now, 
            # or a safe mock function call.
            # To keep it simple, we replace it with:
            # tools.sandbox_runner.run_sandbox('healed_driver', 'healed_image', ['echo', 'healed'])
            
            # For a pure AST replacement, let's create a Call to a placeholder.
            replacement_func = ast.Attribute(
                value=ast.Name(id='sandbox_runner', ctx=ast.Load()),
                attr='run_sandbox',
                ctx=ast.Load()
            )
            # Dummy args
            args = [
                ast.Constant(value="auto_healed"), 
                ast.Constant(value="alpine"),
                ast.List(elts=[ast.Constant(value="echo"), ast.Constant(value="healed")], ctx=ast.Load())
            ]
            
            new_node = ast.Call(func=replacement_func, args=args, keywords=[])
            ast.copy_location(new_node, node)
            return new_node
            
        return node

def heal_script(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
        
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return False
        
    healer = HealingTransformer()
    healed_tree = healer.visit(tree)
    
    if healer.healed_count == 0:
        print(f"[{filepath}] No forbidden calls found. No healing required.")
        return True
        
    ast.fix_missing_locations(healed_tree)
    
    # Needs Python 3.9+ for ast.unparse
    try:
        healed_source = ast.unparse(healed_tree)
    except AttributeError:
        print("Error: ast.unparse requires Python 3.9+")
        return False
        
    # We must NEVER overwrite.
    out_path = get_output_path(filepath)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        # We also inject the import for sandbox_runner if we healed something
        f.write("import sys, os\n")
        f.write("try:\n    import tools.sandbox_runner as sandbox_runner\nexcept ImportError:\n    pass\n\n")
        f.write(healed_source)
        
    print(f"[{filepath}] Healed {healer.healed_count} node(s).")
    print(f"Output saved to NEW file: {out_path} (original remains intact).")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/ast_healer.py <path_to_script.py>")
        sys.exit(1)
        
    for path in sys.argv[1:]:
        heal_script(path)
