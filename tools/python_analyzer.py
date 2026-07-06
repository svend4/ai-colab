# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.python_analyzer
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Read-only semantic AST analyzer for Python code.
# ==========================================
"""

import argparse
import ast
import json
import os
import sys

DEFAULT_MAX_BYTES = 50000
DANGEROUS_MODULES = {
    "http",
    "os",
    "requests",
    "shutil",
    "socket",
    "subprocess",
    "sys",
    "urllib",
}
DANGEROUS_FUNCS = {"__import__", "eval", "exec", "open"}
DANGEROUS_ATTR_CALLS = {
    "os.popen",
    "os.remove",
    "os.rename",
    "os.rmdir",
    "os.system",
    "shutil.rmtree",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.Popen",
    "subprocess.run",
}


def _is_relative_to(path, base):
    try:
        return os.path.commonpath([path, base]) == base
    except ValueError:
        return False


def _resolve_path(path, base_dir=None):
    if base_dir is None:
        return os.path.abspath(os.path.expanduser(path)), path
    base = os.path.abspath(os.path.expanduser(base_dir))
    raw = os.path.expanduser(path)
    target = os.path.abspath(raw if os.path.isabs(raw) else os.path.join(base, raw))
    if not _is_relative_to(target, base):
        raise ValueError("path is outside allowed root: %s" % target)
    rel = os.path.relpath(target, base).replace(os.sep, "/")
    return target, rel


def _summary(result):
    return {
        "imports": len(result.get("imports", [])),
        "classes": len(result.get("classes", [])),
        "functions": len(result.get("functions", [])),
        "risks": len(result.get("risks", [])),
    }


def _name_of_call(func):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parent = _name_of_call(func.value)
        if parent:
            return "%s.%s" % (parent, func.attr)
        return func.attr
    return None


def _risk(name, reason, node=None, severity="medium"):
    item = {"name": name, "reason": reason, "severity": severity}
    if node is not None and getattr(node, "lineno", None):
        item["line"] = node.lineno
    return item


def _module_root(module):
    return (module or "").split(".")[0]


def _class_owner(tree, function_node):
    owner = None
    for cls in ast.walk(tree):
        if isinstance(cls, ast.ClassDef) and function_node in list(ast.walk(cls)):
            owner = cls.name
    return owner


def analyze_source(source, path="<memory>"):
    """Analyze Python source as data. Target code is parsed, never imported or executed."""
    result = {
        "path": path,
        "syntax_ok": True,
        "imports": [],
        "classes": [],
        "functions": [],
        "risks": [],
        "summary": {"imports": 0, "classes": 0, "functions": 0, "risks": 0},
    }
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        result["syntax_ok"] = False
        result["error"] = {
            "type": "SyntaxError",
            "message": str(exc),
            "line": exc.lineno,
            "offset": exc.offset,
        }
        result["risks"].append(
            {
                "name": "SyntaxError",
                "reason": str(exc),
                "severity": "high",
                "line": exc.lineno,
            }
        )
        result["summary"] = _summary(result)
        return result

    seen_imports = set()
    seen_risks = set()

    def add_risk(item):
        key = (item.get("name"), item.get("line"), item.get("reason"))
        if key not in seen_risks:
            seen_risks.add(key)
            result["risks"].append(item)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                if module not in seen_imports:
                    seen_imports.add(module)
                    result["imports"].append(
                        {"module": module, "name": alias.asname or alias.name, "line": node.lineno}
                    )
                if _module_root(module) in DANGEROUS_MODULES:
                    add_risk(_risk(_module_root(module), "sensitive module import", node))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imported = ".%s" % alias.name if not module else "%s.%s" % (module, alias.name)
                if imported not in seen_imports:
                    seen_imports.add(imported)
                    result["imports"].append(
                        {"module": module, "name": alias.name, "line": node.lineno}
                    )
            if _module_root(module) in DANGEROUS_MODULES:
                add_risk(_risk(_module_root(module), "sensitive from-import", node))
        elif isinstance(node, ast.ClassDef):
            result["classes"].append({"name": node.name, "line": node.lineno})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            owner = _class_owner(tree, node)
            qualname = "%s.%s" % (owner, node.name) if owner else node.name
            result["functions"].append(
                {
                    "name": node.name,
                    "qualname": qualname,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "line": node.lineno,
                }
            )
        elif isinstance(node, ast.Call):
            call_name = _name_of_call(node.func)
            if call_name in DANGEROUS_FUNCS:
                add_risk(_risk(call_name, "sensitive builtin call", node, severity="high"))
            if call_name in DANGEROUS_ATTR_CALLS:
                add_risk(_risk(call_name, "sensitive library call", node, severity="medium"))

    result["imports"].sort(key=lambda item: (item.get("line", 0), item.get("module", "")))
    result["classes"].sort(key=lambda item: (item.get("line", 0), item.get("name", "")))
    result["functions"].sort(key=lambda item: (item.get("line", 0), item.get("qualname", "")))
    result["risks"].sort(key=lambda item: (item.get("line") or 0, item.get("name", "")))
    result["summary"] = _summary(result)
    return result


def analyze_file(path, base_dir=None, max_bytes=DEFAULT_MAX_BYTES):
    target, rel = _resolve_path(path, base_dir=base_dir)
    if not os.path.isfile(target):
        raise FileNotFoundError("file not found: %s" % target)
    size = os.path.getsize(target)
    if max_bytes is not None and size > max_bytes:
        return {
            "path": rel,
            "syntax_ok": None,
            "error": {"type": "TooLarge", "message": "file exceeds max_bytes", "bytes": size},
            "imports": [],
            "classes": [],
            "functions": [],
            "risks": [
                {
                    "name": "TooLarge",
                    "reason": "file exceeds max_bytes",
                    "severity": "low",
                }
            ],
            "summary": {"imports": 0, "classes": 0, "functions": 0, "risks": 1},
        }
    with open(target, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    return analyze_source(source, path=rel)


def analyze_python_file(filepath):
    """Compatibility wrapper used by older tools."""
    try:
        result = analyze_file(filepath, base_dir=os.path.dirname(os.path.abspath(filepath)))
    except Exception as exc:
        return {
            "file": filepath,
            "path": os.path.basename(filepath),
            "syntax_ok": None,
            "imports": [],
            "classes": [],
            "functions": [],
            "risks": [],
            "summary": {"imports": 0, "classes": 0, "functions": 0, "risks": 0},
            "status": "error",
            "error": "%s: %s" % (type(exc).__name__, exc),
        }
    result["file"] = filepath
    result["status"] = "ok" if result.get("syntax_ok") is not False else "error"
    return result


def build_parser():
    parser = argparse.ArgumentParser(description="Read-only Python AST analyzer.")
    parser.add_argument("path", help="Python file to inspect")
    parser.add_argument("--base", default=None, help="Allowed base directory")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(json.dumps({"error": "No file provided"}, ensure_ascii=False, indent=2))
        return 2
    args = build_parser().parse_args(argv)
    try:
        result = analyze_file(args.path, base_dir=args.base, max_bytes=args.max_bytes)
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("syntax_ok") is not False else 1


if __name__ == "__main__":
    sys.exit(main())