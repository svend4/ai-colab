#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
files driver (L2, read-only) — T-043.

Безопасный доступ к файлам в разрешённой папке: list / read / search / summarize.
Только чтение, без записи/удаления. Лимиты по `docs/driver-safety-policy.md`:
`max_output_bytes` для read, маскировка секрет-паттернов в выдаче search.
Потом тонко оборачивается в MCP-сервер (stdio) — это «движок» драйвера.

CLI (--base <allowed-root> обязателен: без него команда отказывает, fail-closed):
    python files_driver.py list <dir> --base <allowed-root>
    python files_driver.py read <file> --base <allowed-root> [--max-bytes N]
    python files_driver.py search <pattern> <dir> --base <allowed-root>
    python files_driver.py summarize <dir> --base <allowed-root>
"""
import os
import re
import sys
import json
from pathlib import Path

# Канонический redaction-хелпер (drivers/redaction.py) — общий для драйверов,
# чтобы files/data не держали расходящиеся копии SECRET_RE.
_DRIVERS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _DRIVERS_DIR not in sys.path:
    sys.path.insert(0, _DRIVERS_DIR)
from redaction import redact as redact_text


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

MAX_OUTPUT_BYTES = 1_048_576  # совпадает с max_output_bytes в drivers/files.md
DEFAULT_MAX_FILES = 1_000
DEFAULT_MAX_HITS = 1_000
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "venv",
    ".venv",
    "target",
    "build",
    "dist",
}


class PathAccessError(ValueError):
    pass


def _is_relative_to(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _is_physical(path):
    # На Python 3.12 resolve() после цикла симлинков не досказывает путь и схлопывает «..» по тексту,
    # так что в результате может остаться симлинк. Полностью разрешённый путь симлинков не содержит.
    return not any(part.is_symlink() for part in (path, *path.parents))


def _resolve_path(path_value, base_dir=None):
    # Граница обязательна: без allowed-root движок ничего не отдаёт (fail-closed).
    if base_dir is None or not str(base_dir).strip():
        raise PathAccessError("allowed root is required (fail-closed)")
    base = Path(base_dir).expanduser().resolve()
    # «~» под базой не раскрываем: иначе ответ зависит от учётных записей системы.
    raw_path = Path(path_value)
    try:
        candidate = (raw_path if raw_path.is_absolute() else base / raw_path).resolve()
        inside = _is_relative_to(candidate, base) and _is_physical(candidate)
    except (OSError, RuntimeError):  # симлинк-цикл: до Python 3.13 resolve() кидает RuntimeError
        inside = False
    if not inside:
        # Сообщение печатает то, что передал вызывающий, а не разрешённую цель симлинка.
        raise PathAccessError(f"path is outside allowed root: {path_value}")
    return candidate


def _skip_dir(name, include_hidden=False):
    return name in SKIP_DIRS or (not include_hidden and name.startswith("."))


def _skip_file(name, include_hidden=False):
    return not include_hidden and name.startswith(".")


def _iter_files(root, max_files=DEFAULT_MAX_FILES, include_hidden=False, base_dir=None):
    root_path = _resolve_path(root, base_dir)
    if not root_path.is_dir():
        raise NotADirectoryError(str(root_path))
    # граница — разрешённая папка (base_dir); файл-симлинк наружу не отдаём ни в list, ни в search
    allowed = Path(base_dir).expanduser().resolve()

    count = 0
    for dp, dirs, fns in os.walk(root_path):
        dirs[:] = [name for name in dirs if not _skip_dir(name, include_hidden)]
        for fn in fns:
            if _skip_file(fn, include_hidden):
                continue
            if count >= max_files:
                return
            full_path = Path(dp) / fn
            try:
                inside = _is_relative_to(full_path.resolve(), allowed)
            except (OSError, RuntimeError):  # RuntimeError: цикл симлинков до Python 3.13
                inside = False
            if not inside:
                continue
            rel = full_path.relative_to(root_path).as_posix()
            count += 1
            yield rel, full_path


def list_files(root, max_files=DEFAULT_MAX_FILES, include_hidden=False, base_dir=None):
    out = []
    for rel, _path in _iter_files(root, max_files=max_files, include_hidden=include_hidden, base_dir=base_dir):
        out.append(rel)
    return sorted(out)


def read_file(path, max_bytes=MAX_OUTPUT_BYTES, base_dir=None, redact=True):
    resolved = _resolve_path(path, base_dir)
    if not resolved.is_file():
        raise FileNotFoundError(str(resolved))
    with resolved.open("rb") as f:
        data = f.read(max_bytes + 1)
    truncated = len(data) > max_bytes
    text = data[:max_bytes].decode("utf-8", "replace")
    if redact:
        text = redact_text(text)
    return {"path": str(resolved), "truncated": truncated, "bytes": min(len(data), max_bytes), "text": text}


def search(
    pattern,
    root,
    max_files=DEFAULT_MAX_FILES,
    max_hits=DEFAULT_MAX_HITS,
    include_hidden=False,
    base_dir=None,
    regex=False,
):
    rx = re.compile(pattern) if regex else None
    hits = []
    for rel, p in _iter_files(root, max_files=max_files, include_hidden=include_hidden, base_dir=base_dir):
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if (rx.search(line) if rx else pattern in line):
                        hits.append({"path": rel, "line": i, "text": redact_text(line.rstrip())[:300]})
                        if len(hits) >= max_hits:
                            return hits
        except Exception:
            continue
    return hits


def summarize(root, max_files=DEFAULT_MAX_FILES, include_hidden=False, base_dir=None):
    root_path = _resolve_path(root, base_dir)
    files = list_files(root_path, max_files=max_files, include_hidden=include_hidden, base_dir=base_dir)
    by_ext = {}
    total = 0
    for rel in files:
        p = root_path / rel
        try:
            total += os.path.getsize(p)
        except OSError:
            pass
        ext = os.path.splitext(rel)[1] or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    return {"files": len(files), "total_bytes": total, "by_ext": by_ext, "max_files": max_files}


def _option(args, name, default=None):
    if name not in args:
        return default
    index = args.index(name)
    if index + 1 >= len(args):
        raise ValueError(f"missing value for {name}")
    return args[index + 1]


def _int_option(args, name, default):
    return int(_option(args, name, default))


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        base_dir = _option(a, "--base")
        if cmd in ("list", "read", "search", "summarize") and not (base_dir or "").strip():
            print(json.dumps({"error": "ConfigError", "message": "--base is required: pass the allowed root (fail-closed)"}, ensure_ascii=False))
            return 2
        include_hidden = "--include-hidden" in a
        if cmd == "list" and len(a) > 1:
            print(json.dumps(
                list_files(a[1], max_files=_int_option(a, "--max-files", DEFAULT_MAX_FILES),
                           include_hidden=include_hidden, base_dir=base_dir),
                ensure_ascii=False, indent=2))
            return 0
        if cmd == "read" and len(a) > 1:
            print(json.dumps(
                read_file(a[1], _int_option(a, "--max-bytes", MAX_OUTPUT_BYTES),
                          base_dir=base_dir, redact="--no-redact" not in a),
                ensure_ascii=False, indent=2))
            return 0
        if cmd == "search" and len(a) > 2:
            print(json.dumps(
                search(a[1], a[2], max_files=_int_option(a, "--max-files", DEFAULT_MAX_FILES),
                       max_hits=_int_option(a, "--max-hits", DEFAULT_MAX_HITS),
                       include_hidden=include_hidden, base_dir=base_dir, regex="--regex" in a),
                ensure_ascii=False, indent=2))
            return 0
        if cmd == "summarize" and len(a) > 1:
            print(json.dumps(
                summarize(a[1], max_files=_int_option(a, "--max-files", DEFAULT_MAX_FILES),
                          include_hidden=include_hidden, base_dir=base_dir),
                ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
