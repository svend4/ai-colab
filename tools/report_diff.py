#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report diff (T-127) — compare two Markdown knowledge reports.

This is intentionally small and stdlib-only. It extracts stable metrics from reports produced by
`tools/knowledge.py report`: corpus name, document count, type distribution and query hit count.

    python tools/report_diff.py reports/a.md reports/b.md [--out reports/diff.md]
"""
import os
import re
import sys
from _ioutil import configure_output
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_SUFFIXES = {".md", ".markdown"}

configure_output()

def _is_relative_to(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False

def resolve_md(path_value):
    root = Path(ROOT).resolve()
    raw = Path(path_value).expanduser()
    resolved = (raw if raw.is_absolute() else root / raw).resolve()
    if not _is_relative_to(resolved, root):
        raise ValueError("path is outside repo root: %s" % resolved)
    if resolved.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("unsupported markdown suffix: %s" % resolved.suffix)
    return resolved

def _parse_type_table(text):
    out = {}
    marker = "## Состав по типам"
    if marker not in text:
        return out
    tail = text.split(marker, 1)[1]
    block = tail.split("\n## ", 1)[0]
    for line in block.splitlines():
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|", line)
        if not m:
            continue
        key = m.group(1).strip()
        if key in {"Тип", "---"}:
            continue
        out[key] = int(m.group(2))
    return out

def parse_report(path_value):
    path = resolve_md(path_value)
    text = path.read_text(encoding="utf-8", errors="replace")
    header = re.search(r"^# Knowledge report —\s*(.+)$", text, re.M)
    docs = re.search(r"занесено документов:\s*\*\*(\d+)\*\*", text)
    query = re.search(r"^## Запрос:.+?—\s*(?:показано\s*)?(\d+)\s+совпад", text, re.M)
    return {
        "path": str(path.relative_to(Path(ROOT).resolve())).replace("\\", "/"),
        "corpus": header.group(1).strip() if header else "?",
        "documents": int(docs.group(1)) if docs else 0,
        "query_hits": int(query.group(1)) if query else None,
        "types": _parse_type_table(text),
    }

def render(a, b):
    keys = sorted(set(a["types"]) | set(b["types"]))
    out = [
        "# Knowledge report diff",
        "",
        "| Metric | A | B | Delta |",
        "|---|---:|---:|---:|",
        "| documents | %d | %d | %+d |" % (a["documents"], b["documents"], b["documents"] - a["documents"]),
    ]
    if a["query_hits"] is not None or b["query_hits"] is not None:
        av = a["query_hits"] if a["query_hits"] is not None else 0
        bv = b["query_hits"] if b["query_hits"] is not None else 0
        out.append("| shown_query_hits | %d | %d | %+d |" % (av, bv, bv - av))
    out += [
        "",
        "## Reports",
        "",
        "- A: `%s` (`%s`)" % (a["path"], a["corpus"]),
        "- B: `%s` (`%s`)" % (b["path"], b["corpus"]),
        "",
        "## Type Distribution",
        "",
        "| Type | A | B | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key in keys:
        av = a["types"].get(key, 0)
        bv = b["types"].get(key, 0)
        out.append("| %s | %d | %d | %+d |" % (key, av, bv, bv - av))
    out += [
        "",
        "## Interpretation",
        "",
        "This diff is mechanical. It shows scale and type changes. Query hits are the displayed top-N hits from each report, not a full corpus-wide total. Quality still needs human/agent review of the actual hits and summaries.",
    ]
    return "\n".join(out)

def _arg_value(args, name, default=None):
    if name not in args:
        return default
    pos = args.index(name) + 1
    if pos >= len(args):
        raise ValueError("missing value for %s" % name)
    return args[pos]

def write_out(text, out_path):
    path = resolve_md(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
    return path

def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    try:
        a = parse_report(args[0])
        b = parse_report(args[1])
        text = render(a, b)
        out_path = _arg_value(args, "--out")
        if out_path:
            write_out(text, out_path)
        print(text)
        return 0
    except Exception as exc:
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1

if __name__ == "__main__":
    sys.exit(main())