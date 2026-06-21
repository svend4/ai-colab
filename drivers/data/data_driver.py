#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data driver (L2, read-only) — табличные файлы CSV/TSV.

Безопасный доступ к таблицам в allowed-root: list_tables / columns / head /
summarize. Только чтение, чистая stdlib (`csv`). Лимиты строк и `base_dir`-
confinement (как в files_driver). Потом тонко оборачивается в MCP-сервер.

CLI:
    python data_driver.py list <dir>
    python data_driver.py columns <file>
    python data_driver.py head <file> [--n N]
    python data_driver.py summarize <file>
"""
import os
import sys
import csv
import json
from pathlib import Path

# Канонический redaction-хелпер (drivers/redaction.py) — общий для драйверов,
# чтобы не плодить копии SECRET_RE (ревью T-078, находка L).
_DRIVERS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _DRIVERS_DIR not in sys.path:
    sys.path.insert(0, _DRIVERS_DIR)
from redaction import redact

DEFAULT_MAX_ROWS = 1000
MAX_OUTPUT_BYTES = 1_048_576  # совпадает с max_output_bytes в drivers/data.md
TABLE_EXT = {".csv", ".tsv"}


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


class PathAccessError(ValueError):
    pass


def _resolve(path_value, base_dir=None):
    if base_dir is None:
        return Path(path_value).expanduser().resolve()
    base = Path(base_dir).expanduser().resolve()
    raw = Path(path_value).expanduser()
    candidate = (raw if raw.is_absolute() else base / raw).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise PathAccessError("path is outside allowed root: %s" % candidate)
    return candidate


def _delim(path):
    return "\t" if str(path).lower().endswith(".tsv") else ","


def list_tables(directory, base_dir=None):
    root = _resolve(directory, base_dir)
    out = []
    for dp, _dirs, fns in os.walk(root):
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in TABLE_EXT:
                out.append((Path(dp) / fn).relative_to(root).as_posix())
    return sorted(out)


def columns(path, base_dir=None):
    p = _resolve(path, base_dir)
    with p.open(encoding="utf-8", newline="") as f:
        return next(csv.reader(f, delimiter=_delim(p)), [])


def head(path, n=10, base_dir=None, max_bytes=MAX_OUTPUT_BYTES):
    p = _resolve(path, base_dir)
    n = max(0, min(int(n), DEFAULT_MAX_ROWS))
    rows = []
    used = 0
    with p.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=_delim(p))
        for i, row in enumerate(reader):
            if i >= n:
                break
            # маскировка секретов в значениях ячеек + байтовый лимит выдачи
            # (CSV — типичный носитель PII/секретов; safety-policy, ревью T-078 находка F)
            red = {k: redact(v) for k, v in row.items()}
            size = sum(len(str(k)) + len(str(v)) for k, v in red.items())
            if rows and used + size > max_bytes:
                break
            rows.append(red)
            used += size
    return rows


def summarize(path, base_dir=None, max_rows=DEFAULT_MAX_ROWS):
    p = _resolve(path, base_dir)
    cols = columns(p, base_dir=base_dir)
    nrows = 0
    non_empty = {c: 0 for c in cols}
    with p.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=_delim(p))
        for row in reader:
            if nrows >= max_rows:
                break
            nrows += 1
            for c in cols:
                if (row.get(c) or "").strip():
                    non_empty[c] += 1
    return {"path": str(p), "rows": nrows, "columns": cols, "non_empty": non_empty}


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        base_dir = a[a.index("--base") + 1] if "--base" in a else None
        if cmd == "list":
            print(json.dumps(list_tables(a[1], base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "columns":
            print(json.dumps(columns(a[1], base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "head":
            n = int(a[a.index("--n") + 1]) if "--n" in a else 10
            print(json.dumps(head(a[1], n=n, base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "summarize":
            print(json.dumps(summarize(a[1], base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
