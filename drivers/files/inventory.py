#!/usr/bin/env python3
"""
Files inventory driver - read-only scanner for local folders.

It does not write, rename, delete, move, or execute files. The script only
collects metadata and prints JSON to stdout.

Usage: python inventory.py <dir> --base <allowed-root> [--hash] [--include-hidden]
--base is required. The scan stays inside it, and symlinks that lead outside are skipped.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


DEFAULT_MAX_FILES = 1000
DEFAULT_MAX_HASH_BYTES = 10 * 1024 * 1024

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

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".rst",
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".html",
    ".css",
    ".sql",
    ".ps1",
    ".sh",
}


def sha256_file(path: Path, max_bytes: int):
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > max_bytes:
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def file_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return "text"
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}:
        return "image"
    if suffix in {".pdf"}:
        return "pdf"
    if suffix in {".doc", ".docx", ".odt", ".rtf"}:
        return "document"
    if suffix in {".xls", ".xlsx", ".ods"}:
        return "spreadsheet"
    if suffix in {".zip", ".7z", ".rar", ".tar", ".gz"}:
        return "archive"
    return "unknown"


def should_skip_dir(name: str, include_hidden: bool) -> bool:
    if name in SKIP_DIRS:
        return True
    if not include_hidden and name.startswith("."):
        return True
    return False


def should_skip_file(name: str, include_hidden: bool) -> bool:
    if not include_hidden and name.startswith("."):
        return True
    return False


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _is_physical(path: Path) -> bool:
    # On Python 3.12 resolve() after a symlink loop leaves the tail unresolved and collapses ".."
    # by text, so the result can still name a symlink. A fully resolved path contains none.
    return not any(part.is_symlink() for part in (path, *path.parents))


def _inside_root(path: Path, allowed: Path) -> bool:
    # A symlink that leads outside the allowed root is not reported at all: no name, size or hash.
    try:
        real = path.resolve()
        return _is_relative_to(real, allowed) and _is_physical(real)
    except (OSError, RuntimeError):  # RuntimeError: symlink loop on Python < 3.13
        return False


def inventory(root_path: str, max_files: int = DEFAULT_MAX_FILES, include_hidden: bool = False,
              hash_files: bool = False, max_hash_bytes: int = DEFAULT_MAX_HASH_BYTES,
              base_dir=None) -> dict:
    if base_dir is not None and (not str(base_dir).strip() or Path(base_dir).parts == ()):
        return {"error": "ConfigError", "message": "base_dir must be an explicit path, not blank or '.' (fail-closed)"}
    # The boundary is checked before exists(), so an outside path gets the same answer
    # whether it exists or not. A symlink loop that cannot be resolved counts as outside.
    try:
        root = Path(root_path).resolve()
        allowed = Path(base_dir).resolve() if base_dir is not None else root
        inside = _is_relative_to(root, allowed) and _is_physical(root)
    except (OSError, RuntimeError):  # RuntimeError: symlink loop on Python < 3.13
        inside = False
    if not inside:
        return {"error": "path is outside allowed root", "path": str(root_path)}
    if not root.exists():
        return {"error": "path not found", "path": str(root)}
    if not root.is_dir():
        return {"error": "not a directory", "path": str(root)}

    items = []
    extensions = {}
    kinds = {}
    skipped_dirs = []
    errors = []
    total_files = 0
    total_dirs = 0
    total_size = 0
    truncated = False

    for dirpath, dirnames, filenames in os.walk(root):
        kept_dirs = []
        for dirname in dirnames:
            if not _inside_root(Path(dirpath) / dirname, allowed):
                continue  # каталог-симлинк наружу: ни имени, ни счёта
            if should_skip_dir(dirname, include_hidden):
                skipped_dirs.append(str((Path(dirpath) / dirname).relative_to(root)))
            else:
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        total_dirs += len(dirnames)

        for filename in filenames:
            if should_skip_file(filename, include_hidden):
                continue
            path = Path(dirpath) / filename
            if not _inside_root(path, allowed):
                continue
            if total_files >= max_files:
                truncated = True
                dirnames[:] = []
                break

            rel = path.relative_to(root).as_posix()
            suffix = path.suffix.lower() or "<none>"
            kind = file_kind(path)
            try:
                stat = path.stat()
                size = stat.st_size
            except OSError as exc:
                errors.append({"path": rel, "error": str(exc)})
                size = 0

            total_files += 1
            total_size += size
            extensions[suffix] = extensions.get(suffix, 0) + 1
            kinds[kind] = kinds.get(kind, 0) + 1

            entry = {
                "path": rel,
                "name": filename,
                "extension": suffix,
                "kind": kind,
                "size_bytes": size,
            }
            if hash_files:
                digest = sha256_file(path, max_hash_bytes)
                if digest:
                    entry["sha256"] = digest
                else:
                    entry["sha256"] = None
                    entry["hash_skipped"] = True
            items.append(entry)

    largest = sorted(items, key=lambda item: item["size_bytes"], reverse=True)[:10]
    return {
        "path": str(root),
        "mode": "read-only",
        "max_files": max_files,
        "include_hidden": include_hidden,
        "hash_files": hash_files,
        "truncated": truncated,
        "summary": {
            "total_files": total_files,
            "total_dirs": total_dirs,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 3),
            "extensions": extensions,
            "kinds": kinds,
            "skipped_dirs": len(skipped_dirs),
            "errors": len(errors),
        },
        "largest_files": largest,
        "files": items,
        "skipped_dirs": skipped_dirs[:100],
        "errors": errors,
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="inventory.py")
    parser.add_argument("path", help="Directory to scan")
    parser.add_argument("--base", default="", help="allowed root, required: the scan stays inside it")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--hash", action="store_true", dest="hash_files")
    parser.add_argument("--max-hash-bytes", type=int, default=DEFAULT_MAX_HASH_BYTES)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if not args.base.strip():
        print(json.dumps({"error": "ConfigError", "message": "--base is required: pass the allowed root (fail-closed)"}, ensure_ascii=False))
        return 2
    if args.max_files <= 0:
        print(json.dumps({"error": "--max-files must be positive"}))
        return 2
    if args.max_hash_bytes <= 0:
        print(json.dumps({"error": "--max-hash-bytes must be positive"}))
        return 2
    report = inventory(
        args.path,
        max_files=args.max_files,
        include_hidden=args.include_hidden,
        hash_files=args.hash_files,
        max_hash_bytes=args.max_hash_bytes,
        base_dir=os.path.abspath(os.path.expanduser(args.base)),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if "error" in report else 0


if __name__ == "__main__":
    sys.exit(main())
