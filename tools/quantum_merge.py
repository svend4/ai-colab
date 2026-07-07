#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ast: allow-subprocess
import os
import sys
import ast

def parse_ast(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return ast.parse(source), source

def hash_ast(node):
    # Python 3.9+ ast.unparse gives a normalized string representation
    try:
        return hash(ast.unparse(node))
    except AttributeError:
        # Fallback for older python
        return hash(ast.dump(node))

def rename_function(node, new_name):
    # Shallow copy the node and change its name
    new_node = ast.FunctionDef(
        name=new_name,
        args=node.args,
        body=node.body,
        decorator_list=node.decorator_list,
        returns=node.returns,
        type_comment=node.type_comment
    )
    ast.copy_location(new_node, node)
    return new_node

def is_func(node):
    return isinstance(node, ast.FunctionDef)

def semantic_merge(file_a, file_b):
    tree_a, src_a = parse_ast(file_a)
    tree_b, src_b = parse_ast(file_b)
    
    funcs_a = {node.name: node for node in tree_a.body if is_func(node)}
    funcs_b = {node.name: node for node in tree_b.body if is_func(node)}
    
    merged_body = []
    
    # First, append all non-function nodes from file A (imports, globals)
    # In a real tool we'd need to merge imports too, but for Concept 4 we keep A's header
    for node in tree_a.body:
        if not is_func(node):
            merged_body.append(node)
            
    # Merge functions
    all_func_names = set(funcs_a.keys()).union(funcs_b.keys())
    
    for name in sorted(all_func_names):
        if name in funcs_a and name in funcs_b:
            if hash_ast(funcs_a[name]) != hash_ast(funcs_b[name]):
                # Conflict! Superposition
                print(f"Conflict in function '{name}'. Creating superposition...")
                
                # Add decorator for A
                dec_a = ast.Name(id='VARIANT_A', ctx=ast.Load())
                node_a = rename_function(funcs_a[name], f"{name}_VAR_A")
                node_a.decorator_list.insert(0, dec_a)
                merged_body.append(node_a)
                
                # Add decorator for B
                dec_b = ast.Name(id='VARIANT_B', ctx=ast.Load())
                node_b = rename_function(funcs_b[name], f"{name}_VAR_B")
                node_b.decorator_list.insert(0, dec_b)
                merged_body.append(node_b)
            else:
                # Identical
                merged_body.append(funcs_a[name])
        elif name in funcs_a:
            merged_body.append(funcs_a[name])
        else:
            merged_body.append(funcs_b[name])
            
    # Build new module
    merged_tree = ast.Module(body=merged_body, type_ignores=[])
    ast.fix_missing_locations(merged_tree)
    
    try:
        merged_code = ast.unparse(merged_tree)
    except AttributeError:
        print("Error: ast.unparse requires Python 3.9+")
        return None
        
    # Inject dummy decorators so the code runs
    header = "# SUPERPOSITION MERGE\n# " + "="*30 + "\ndef VARIANT_A(f): return f\ndef VARIANT_B(f): return f\n\n"
    return header + merged_code

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/quantum_merge.py <file_a.py> <file_b.py>")
        sys.exit(1)
        
    file_a = sys.argv[1]
    file_b = sys.argv[2]
    
    if not os.path.exists(file_a) or not os.path.exists(file_b):
        print("Error: Both files must exist.")
        sys.exit(1)
        
    result = semantic_merge(file_a, file_b)
    if result:
        # Generate new file without modifying originals
        name_a = os.path.basename(file_a).replace('.py', '')
        name_b = os.path.basename(file_b).replace('.py', '')
        out_name = f"quantum_{name_a}_{name_b}.py"
        out_path = os.path.join(os.path.dirname(file_a), out_name)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(result)
            
        print(f"Quantum merge complete. Superposition saved to: {out_path}")
        print("Original files were untouched.")
