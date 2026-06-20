#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
files driver (L2, read-only) — T-043.

Безопасный доступ к файлам в разрешённой папке: list / read / search / summarize.
Только чтение, без записи/удаления. Лимиты по `docs/driver-safety-policy.md`:
`max_output_bytes` для read, маскировка секрет-паттернов в выдаче search.
Потом тонко оборачивается в MCP-сервер (stdio) — это «движок» драйвера.

CLI:
    python files_driver.py list <dir>
    python files_driver.py read <file> [--max-bytes N]
    python files_driver.py search <pattern> <dir>
    python files_driver.py summarize <dir>
"""
import os
import re
import sys
import json


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

MAX_OUTPUT_BYTES = 1_000_000
SECRET_RE = re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd)\b(\s*[=:]\s*)(\S+)")


def _redact(line):
    return SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + "***", line)


def list_files(root):
    out = []
    for dp, _dirs, fns in os.walk(root):
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/")
            out.append(rel)
    return sorted(out)


def read_file(path, max_bytes=MAX_OUTPUT_BYTES):
    with open(path, "rb") as f:
        data = f.read(max_bytes + 1)
    truncated = len(data) > max_bytes
    text = data[:max_bytes].decode("utf-8", "replace")
    return {"path": path, "truncated": truncated, "bytes": min(len(data), max_bytes), "text": text}


def search(pattern, root):
    rx = re.compile(pattern)
    hits = []
    for rel in list_files(root):
        p = os.path.join(root, rel)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if rx.search(line):
                        hits.append({"path": rel, "line": i, "text": _redact(line.rstrip())[:300]})
        except Exception:
            continue
    return hits


def summarize(root):
    files = list_files(root)
    by_ext = {}
    total = 0
    for rel in files:
        p = os.path.join(root, rel)
        try:
            total += os.path.getsize(p)
        except OSError:
            pass
        ext = os.path.splitext(rel)[1] or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    return {"files": len(files), "total_bytes": total, "by_ext": by_ext}


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    if cmd == "list" and len(a) > 1:
        print(json.dumps(list_files(a[1]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "read" and len(a) > 1:
        mb = int(a[a.index("--max-bytes") + 1]) if "--max-bytes" in a else MAX_OUTPUT_BYTES
        print(json.dumps(read_file(a[1], mb), ensure_ascii=False, indent=2))
        return 0
    if cmd == "search" and len(a) > 2:
        print(json.dumps(search(a[1], a[2]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "summarize" and len(a) > 1:
        print(json.dumps(summarize(a[1]), ensure_ascii=False, indent=2))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
