#!/usr/bin/env python3
import os
import ast
import hashlib
from collections import defaultdict

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT, "tools")

class AstHasher(ast.NodeVisitor):
    def __init__(self):
        self.node_types = []
        
    def generic_visit(self, node):
        self.node_types.append(type(node).__name__)
        super().generic_visit(node)
        
def get_function_hash(func_node):
    hasher = AstHasher()
    hasher.visit(func_node)
    # The signature of the function is just the sequence of AST node types.
    # We ignore names (variables) to find structural duplicates!
    signature = ",".join(hasher.node_types)
    return hashlib.md5(signature.encode('utf-8')).hexdigest()

def scan_for_duplicates():
    print("="*60)
    print("AST HEALER: Structural Code Duplication Scanner")
    print("="*60)
    
    if not os.path.isdir(TOOLS_DIR):
        return
        
    # Mapping of structural_hash -> list of (filename, func_name)
    structure_map = defaultdict(list)
    
    for filename in os.listdir(TOOLS_DIR):
        if not filename.endswith(".py"): continue
        filepath = os.path.join(TOOLS_DIR, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code, filename=filepath)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Ignore tiny functions
                    if len(node.body) <= 2: continue
                    
                    structural_hash = get_function_hash(node)
                    structure_map[structural_hash].append((filename, node.name))
                    
        except SyntaxError:
            pass # Skip scripts with syntax errors
        except UnicodeDecodeError:
            pass
            
    # Report findings
    duplicates_found = 0
    for structural_hash, occurrences in structure_map.items():
        if len(occurrences) > 1:
            duplicates_found += 1
            print(f"\n[!] Structural Duplication Detected:")
            for filename, func_name in occurrences:
                print(f"    - function '{func_name}' in {filename}")
                
    if duplicates_found == 0:
        print("No structural duplicates found. Code is mathematically DRY.")
    else:
        print(f"\nFound {duplicates_found} logical clones. Consider refactoring into _ioutil.py!")

if __name__ == "__main__":
    scan_for_duplicates()
