#!/usr/bin/env python3
"""
Files inventory driver - read-only scanner for local folders.

It does not write, rename, delete, move, or execute files. The script only
collects metadata and prints JSON to stdout.

Usage: python inventory.py <dir> --base <allowed-root> [--hash] [--include-hidden]
--base is required. The scan stays inside it, and symlinks that lead outside are skipped.
"""

import argparse
import errno
import hashlib
import json
import os
import stat
import sys
from pathlib import Path


DEFAULT_MAX_FILES = 1000
DEFAULT_MAX_HASH_BYTES = 10 * 1024 * 1024
# O_NOFOLLOW and dir_fd are not available everywhere (not on Windows); there the path-based check stays.
_SAFE_OPEN = hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd

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


def _has_loop(path: Path) -> bool:
    # A symlink loop anywhere in the path, even when a later ".." walks the result back inside.
    try:
        os.path.realpath(path, strict=True)
    except OSError as exc:
        return exc.errno == errno.ELOOP
    return False


def _expand_base(base_dir: str) -> str:
    # "~" is expanded for the CLI only. An empty HOME turns it into "/": a refusal, not the root.
    expanded = os.path.expanduser(str(base_dir))
    if expanded == os.sep and str(base_dir).strip() != os.sep:
        raise ValueError("allowed root must not expand to / (fail-closed)")
    return expanded


def _resolve_base(base_dir) -> Path:
    # The allowed root is required: without it nothing is reported, and the root is never its own boundary.
    # A blank base and "." (what Path("") gives) are refused too.
    if base_dir is None or not str(base_dir).strip() or Path(base_dir).parts == ():
        raise ValueError("base_dir must be an explicit path, not blank or '.' (fail-closed)")
    try:
        resolved = Path(_expand_base(base_dir)).resolve()
    except (OSError, RuntimeError):  # a loop at the base itself: RuntimeError before Python 3.13
        raise ValueError("allowed root is not a usable directory (fail-closed)") from None
    if not _is_physical(resolved):  # Python 3.13 does not raise on a loop, it leaves the symlink in place
        raise ValueError("allowed root is not a usable directory (fail-closed)")
    return resolved


def _inside_root(path: Path, allowed: Path):
    # The physical path inside the allowed root, or None. A symlink that leads outside, a loop and a
    # missing path are not reported at all: no name, size or hash.
    try:
        real = path.resolve()
        if _is_relative_to(real, allowed) and _is_physical(real):
            return real
    except (OSError, RuntimeError):  # RuntimeError: symlink loop on Python < 3.13
        pass
    return None


def _is_hardlink(path: Path) -> bool:
    # A hard link (several names for one inode) can reach a file outside the root, so such files are not reported.
    try:
        return os.stat(path).st_nlink > 1
    except OSError:
        return True  # cannot check: not reported (fail-closed)


def _parent_dirfd(base: Path, physical: Path):
    # Open the file's directory from the base with dir_fd, one component at a time, each with O_NOFOLLOW.
    # A component swapped for a symlink after the check fails with ELOOP. Returns (dir fd, file name);
    # the caller closes the fd.
    try:
        parts = physical.relative_to(base).parts
    except ValueError:
        raise ValueError("path is outside allowed root (fail-closed)") from None
    if not parts:
        raise ValueError("not a file (fail-closed)")
    dirfd = os.open(str(base), os.O_RDONLY)
    try:
        for name in parts[:-1]:
            nextfd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
            os.close(dirfd)
            dirfd = nextfd
    except BaseException:
        os.close(dirfd)
        raise
    return dirfd, parts[-1]


def _stat_physical(base: Path, physical: Path, given: str):
    # Size and type without opening the file for reading, so an unreadable file is still counted, as before.
    if not _SAFE_OPEN:
        st = os.stat(str(physical))
    else:
        dirfd, name = _parent_dirfd(base, physical)
        try:
            st = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
        finally:
            os.close(dirfd)
    if stat.S_ISLNK(st.st_mode):  # swapped for a symlink after the check: not a file
        raise FileNotFoundError(errno.ENOENT, "not a file", str(given))
    return st


def _open_physical(base: Path, physical: Path) -> int:
    # Open through the dir_fd chain with O_NOFOLLOW. O_NONBLOCK stops a FIFO from blocking the open;
    # fstat then refuses it, and so it refuses a hard link (st_nlink > 1).
    if not _SAFE_OPEN:
        fd = os.open(str(physical), os.O_RDONLY | getattr(os, "O_BINARY", 0))
    else:
        dirfd, name = _parent_dirfd(base, physical)
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirfd)
        finally:
            os.close(dirfd)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ValueError("not a regular file (fail-closed)")
        if st.st_nlink > 1:
            raise ValueError("hard-linked file is refused (fail-closed)")
    except BaseException:
        os.close(fd)
        raise
    return fd


def _sha256_physical(base: Path, physical: Path, max_bytes: int):
    # Hash through the fd from _open_physical, so a swapped or hard-linked file is never read.
    try:
        fd = _open_physical(base, physical)
    except (OSError, ValueError):
        return None
    try:
        with os.fdopen(fd, "rb") as f:
            if os.fstat(f.fileno()).st_size > max_bytes:
                return None
            h = hashlib.sha256()
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def inventory(root_path: str, max_files: int = DEFAULT_MAX_FILES, include_hidden: bool = False,
              hash_files: bool = False, max_hash_bytes: int = DEFAULT_MAX_HASH_BYTES,
              base_dir=None) -> dict:
    try:
        allowed = _resolve_base(base_dir)
    except ValueError as exc:
        return {"error": "ConfigError", "message": str(exc)}
    # The boundary is checked before exists(), so an outside path gets the same answer
    # whether it exists or not. A symlink loop that cannot be resolved counts as outside.
    try:
        raw = Path(root_path)
        root = raw.resolve()
        inside = _is_relative_to(root, allowed) and _is_physical(root) and not _has_loop(raw)
    except (OSError, RuntimeError):  # RuntimeError: symlink loop on Python < 3.13
        inside = False
    if not inside:
        return {"error": "path is outside allowed root", "path": str(root_path)}
    # Errors name the path as passed, not the resolved target of a symlink.
    if not root.exists():
        return {"error": "path not found", "path": str(root_path)}
    if not root.is_dir():
        return {"error": "not a directory", "path": str(root_path)}

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
            if _inside_root(Path(dirpath) / dirname, allowed) is None:
                continue  # a directory symlink leading outside: no name and no count
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
            real = _inside_root(path, allowed)
            if real is None or _is_hardlink(real):
                continue  # outside, a loop, or a hard link: no name and no count
            if total_files >= max_files:
                truncated = True
                dirnames[:] = []
                break

            rel = path.relative_to(root).as_posix()
            suffix = path.suffix.lower() or "<none>"
            kind = file_kind(path)
            try:
                size = _stat_physical(allowed, real, rel).st_size
            except (OSError, ValueError) as exc:
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
                digest = _sha256_physical(allowed, real, max_hash_bytes)
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
    try:
        base_dir = os.path.abspath(_expand_base(args.base))
    except ValueError as exc:
        print(json.dumps({"error": "ConfigError", "message": str(exc)}, ensure_ascii=False))
        return 2
    report = inventory(
        args.path,
        max_files=args.max_files,
        include_hidden=args.include_hidden,
        hash_files=args.hash_files,
        max_hash_bytes=args.max_hash_bytes,
        base_dir=base_dir,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if "error" in report else 0


if __name__ == "__main__":
    sys.exit(main())
