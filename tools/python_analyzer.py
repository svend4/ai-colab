#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.python_analyzer
# TYPE: active-script
# DOMAIN: core.code-analysis
# DEPTH_LEVEL: 1
# SUMMARY: Read-only AST-анализ Python-файлов: imports, classes, functions и риск-сигналы без import/exec.
# ==========================================
"""python_analyzer.py — read-only semantic analyzer for Python source files.

Uses the standard-library `ast` module only. It reads source text and parses it;
it never imports, executes, evaluates, or loads target code as a module.

CLI:
    python tools/python_analyzer.py <file.py> [--base <allowed-root>] [--json]
"""
import ast
import json
import os
import sys
from pathlib import Path

RISK_IMPORTS = {
    "os": ("medium", "operating-system access"),
    "sys": ("medium", "interpreter/process access"),
    "subprocess": ("high", "process execution"),
    "socket": ("medium", "network socket access"),
    "requests": ("medium", "network HTTP access"),
    "urllib": ("medium", "network URL access"),
}

RISK_CALLS = {
    "eval": ("high", "dynamic evaluation"),
    "exec": ("high", "dynamic execution"),
    "os.system": ("high", "shell command execution"),
    "subprocess.call": ("high", "subprocess execution"),
    "subprocess.run": ("high", "subprocess execution"),
    "subprocess.Popen": ("high", "subprocess execution"),
}


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _is_relative_to(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _resolve_file(path, base_dir=None):
    if base_dir is None:
        return Path(path).expanduser().resolve()
    base = Path(base_dir).expanduser().resolve()
    raw = Path(path).expanduser()
    target = (raw if raw.is_absolute() else base / raw).resolve()
    if not _is_relative_to(target, base):
        raise ValueError("path is outside allowed root: %s" % target)
    return target


def _rel(path, base_dir=None):
    if base_dir is None:
        return str(path)
    try:
        return str(path.relative_to(Path(base_dir).expanduser().resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _call_name(node.value)
        return (left + "." if left else "") + node.attr
    return ""


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []
        self.risks = []
        self._class_stack = []

    def _risk(self, kind, name, severity, reason, line):
        self.risks.append({
            "kind": kind,
            "name": name,
            "severity": severity,
            "reason": reason,
            "line": line,
        })

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name.split(".", 1)[0]
            self.imports.append({"module": alias.name, "as": alias.asname or "", "line": node.lineno})
            if module in RISK_IMPORTS:
                severity, reason = RISK_IMPORTS[module]
                self._risk("import", module, severity, reason, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = "." * node.level + (node.module or "")
        root = (node.module or "").split(".", 1)[0]
        names = [alias.name for alias in node.names]
        self.imports.append({"module": module, "names": names, "line": node.lineno})
        if root in RISK_IMPORTS:
            severity, reason = RISK_IMPORTS[root]
            self._risk("import", root, severity, reason, node.lineno)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.classes.append({"name": node.name, "line": node.lineno, "methods": methods})
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def _visit_function(self, node, async_function=False):
        qualname = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
        self.functions.append({
            "name": node.name,
            "qualname": qualname,
            "line": node.lineno,
            "async": async_function,
            "kind": "method" if self._class_stack else "function",
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._visit_function(node, async_function=False)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node, async_function=True)

    def visit_Call(self, node):
        name = _call_name(node.func)
        if name in RISK_CALLS:
            severity, reason = RISK_CALLS[name]
            self._risk("call", name, severity, reason, node.lineno)
        self.generic_visit(node)


def analyze_source(text, path="<memory>"):
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        return {
            "path": path,
            "syntax_ok": False,
            "error": {"type": "SyntaxError", "message": exc.msg, "line": exc.lineno},
            "imports": [],
            "classes": [],
            "functions": [],
            "risks": [{"kind": "syntax", "name": "SyntaxError", "severity": "high", "reason": exc.msg, "line": exc.lineno}],
            "summary": {"imports": 0, "classes": 0, "functions": 0, "risks": 1},
        }
    analyzer = Analyzer()
    analyzer.visit(tree)
    return {
        "path": path,
        "syntax_ok": True,
        "imports": analyzer.imports,
        "classes": analyzer.classes,
        "functions": analyzer.functions,
        "risks": analyzer.risks,
        "summary": {
            "imports": len(analyzer.imports),
            "classes": len(analyzer.classes),
            "functions": len(analyzer.functions),
            "risks": len(analyzer.risks),
        },
    }


def analyze_file(path, base_dir=None, max_bytes=200000):
    target = _resolve_file(path, base_dir=base_dir)
    if not target.is_file():
        raise FileNotFoundError(str(target))
    size = target.stat().st_size
    if size > max_bytes:
        return {
            "path": _rel(target, base_dir),
            "syntax_ok": None,
            "skipped": "file too large",
            "imports": [],
            "classes": [],
            "functions": [],
            "risks": [],
            "summary": {"imports": 0, "classes": 0, "functions": 0, "risks": 0},
        }
    text = target.read_text(encoding="utf-8", errors="replace")
    result = analyze_source(text, path=_rel(target, base_dir))
    return result


def render(result):
    lines = []
    lines.append("# Python analysis")
    lines.append("")
    lines.append("path: %s" % result.get("path"))
    lines.append("syntax_ok: %s" % result.get("syntax_ok"))
    lines.append("imports: %d" % len(result.get("imports", [])))
    lines.append("classes: %d" % len(result.get("classes", [])))
    lines.append("functions: %d" % len(result.get("functions", [])))
    lines.append("risks: %d" % len(result.get("risks", [])))
    if result.get("classes"):
        lines.append("")
        lines.append("## Classes")
        for item in result["classes"]:
            lines.append("- %s:%s methods=%s" % (item["name"], item["line"], ",".join(item.get("methods", []))))
    if result.get("functions"):
        lines.append("")
        lines.append("## Functions")
        for item in result["functions"]:
            lines.append("- %s:%s (%s)" % (item["qualname"], item["line"], item["kind"]))
    if result.get("risks"):
        lines.append("")
        lines.append("## Risks")
        for item in result["risks"]:
            lines.append("- [%s] %s:%s — %s" % (item["severity"], item["name"], item.get("line"), item["reason"]))
    return "\n".join(lines)


def main(argv=None):
    configure_output()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0 if argv else 2
    json_out = "--json" in argv
    base_dir = None
    args = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            i += 1
        elif arg == "--base":
            if i + 1 >= len(argv):
                print("ОШИБКА: --base требует путь")
                return 2
            base_dir = argv[i + 1]
            i += 2
        elif arg.startswith("-"):
            print("ОШИБКА: неизвестный аргумент: %s" % arg)
            return 2
        else:
            args.append(arg)
            i += 1
    if len(args) != 1:
        print("Нужен ровно один Python-файл")
        return 2
    try:
        result = analyze_file(args[0], base_dir=base_dir)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    if json_out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())