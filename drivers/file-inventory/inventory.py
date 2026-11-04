#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File inventory driver (T-059) — no-deps read-only project file map.

Does not write to the scanned folder, does not execute files, and does not use
network access. Output goes to stdout as JSON or Markdown.

CLI (--base is required: the report stays inside it, and symlinks that lead outside are left out):
    python inventory.py <path> --base <allowed-root>
    python inventory.py <path> --base <allowed-root> --hash
    python inventory.py <path> --base <allowed-root> --markdown
    python inventory.py <path> --max-files 1000 --base <allowed-root>
"""
import argparse
import datetime
import errno
import hashlib
import json
import mimetypes
import os
import stat
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
    "tmp-work",
}

EXECUTABLE_EXTS = {".exe", ".dll", ".msi", ".bat", ".cmd", ".com"}
SHELL_EXTS = {".sh", ".ps1", ".bash", ".zsh", ".fish"}
CODE_EXTS = {".py", ".js", ".ts", ".rs", ".go", ".java", ".c", ".cpp", ".h"}
TEXT_EXTS = {".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".html", ".css", ".sql"}


class PathAccessError(ValueError):
    pass


class ConfigError(ValueError):
    pass


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _is_relative_to(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _is_physical(path):
    # On Python 3.12 resolve() after a symlink loop leaves the tail unresolved and collapses ".."
    # by text, so the result can still name a symlink. A fully resolved path contains none.
    return not any(part.is_symlink() for part in (path, *path.parents))


def _readable_path(path, allowed):
    # A symlink that leads outside the allowed root (or loops) is not read at all:
    # no name, size or hash. Regular paths are returned as they are. An entry that cannot
    # be examined is left out too, since it cannot be shown to be inside.
    try:
        if not stat.S_ISLNK(os.lstat(path).st_mode):
            return path
        real = path.resolve()
        inside = _is_relative_to(real, allowed) and _is_physical(real)
    except (OSError, RuntimeError):  # RuntimeError: symlink loop on Python < 3.13
        return None
    return real if inside else None


def _has_loop(path: Path) -> bool:
    # A symlink loop anywhere in the path, even when a later ".." walks the result back inside.
    try:
        os.path.realpath(path, strict=True)
    except OSError as exc:
        return exc.errno == errno.ELOOP
    return False


def _expand_base(base_dir) -> str:
    # "~" is expanded for the base only. An empty HOME turns it into "/": a refusal, not the root.
    expanded = os.path.expanduser(str(base_dir))
    if expanded == os.sep and str(base_dir).strip() != os.sep:
        raise ConfigError("allowed root must not expand to / (fail-closed)")
    return expanded


def resolve_root(root_path, base_dir=None):
    # The allowed root is required: without it the root would be its own boundary, so the call is refused.
    # A blank base, or "." (what an empty Path("") becomes), is refused too: the cwd must not become
    # the boundary by accident. The CLI turns an explicit "." into an absolute path first.
    if base_dir is None or not str(base_dir).strip() or Path(base_dir).parts == ():
        raise ConfigError("allowed root must be an explicit path, not blank or '.' (fail-closed)")
    # A loop at the base itself: RuntimeError before Python 3.13, an unresolved symlink from 3.13 on.
    try:
        allowed = Path(_expand_base(base_dir)).resolve()
    except (OSError, RuntimeError):
        raise ConfigError("allowed root is not a usable directory (fail-closed)") from None
    if not _is_physical(allowed):
        raise ConfigError("allowed root is not a usable directory (fail-closed)")
    # The boundary is checked before exists(), so an outside path gets the same answer
    # whether it exists or not.
    try:
        # "~" is not expanded under the base: the answer must not depend on system accounts.
        raw = Path(root_path)
        joined = raw if raw.is_absolute() else allowed / raw
        root = joined.resolve()
        inside = _is_relative_to(root, allowed) and _is_physical(root) and not _has_loop(joined)
    except (OSError, RuntimeError):  # RuntimeError: symlink loop on Python < 3.13
        inside = False
    if not inside:
        raise PathAccessError(f"path is outside allowed root: {root_path}")
    if not root.exists():
        raise FileNotFoundError(str(root_path))
    if not root.is_dir():
        raise NotADirectoryError(str(root_path))
    return root


def classify_type(path):
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return "text"
    if ext in CODE_EXTS:
        return "code"
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}:
        return "image"
    if ext == ".pdf":
        return "pdf"
    if ext in {".zip", ".7z", ".rar", ".tar", ".gz"}:
        return "archive"
    if ext in EXECUTABLE_EXTS:
        return "executable"
    return "unknown"


def risk_flags(path, mode):
    ext = path.suffix.lower()
    flags = []
    if ext in EXECUTABLE_EXTS:
        flags.append("executable-extension")
    if ext in SHELL_EXTS:
        flags.append("shell-script")
    if mode & stat.S_IXUSR:
        flags.append("executable-bit")
    if ext in {".pem", ".key", ".env"} or path.name.lower() in {".env", "id_rsa"}:
        flags.append("secret-like-name")
    return flags


# O_NOFOLLOW and dir_fd are not available everywhere (not on Windows); there the path-based check stays.
_SAFE_OPEN = hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd


def _is_hardlink(path):
    # A hard link can name a file outside the root, so it is not reported (fail-closed when it cannot be checked).
    try:
        return os.stat(path).st_nlink > 1
    except FileNotFoundError:
        return False  # a missing target is not a hard link: it is reported as an error entry, with no name
    except OSError:
        return True


def _parent_dirfd(base, physical):
    # Open the file's directory from the base with dir_fd, one component at a time, each with O_NOFOLLOW.
    # A component swapped for a symlink after the check fails with ELOOP. Returns (dir fd, file name);
    # the caller closes the fd.
    try:
        parts = physical.relative_to(base).parts
    except ValueError:
        raise PathAccessError("path is outside allowed root (fail-closed)") from None
    if not parts:
        raise FileNotFoundError(errno.ENOENT, "not a file")
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


def _stat_physical(base, physical, given):
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
        raise FileNotFoundError(str(given))
    return st


def _open_physical(base, physical):
    # Open through the dir_fd chain with O_NOFOLLOW. The type and link count are checked by stat before open(),
    # since open() on a device or tty can already have an effect (O_NOCTTY keeps a tty from becoming controlling).
    # After open() the fd must still be the object that was checked.
    if not _SAFE_OPEN:
        before = os.stat(str(physical))
        _check_regular(before)
        fd = os.open(str(physical), os.O_RDONLY | getattr(os, "O_BINARY", 0))
    else:
        dirfd, name = _parent_dirfd(base, physical)
        try:
            before = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
            _check_regular(before)
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY, dir_fd=dirfd)
        finally:
            os.close(dirfd)
    try:
        st = os.fstat(fd)
        if _SAFE_OPEN and (st.st_dev, st.st_ino) != (before.st_dev, before.st_ino):
            raise PathAccessError("path changed while opening (fail-closed)")
        _check_regular(st)
    except BaseException:
        os.close(fd)
        raise
    return fd


def _check_regular(st):
    # A symlink, directory, device or FIFO is not a file; a hard link can name a file outside the root.
    if not stat.S_ISREG(st.st_mode):
        raise PathAccessError("not a regular file (fail-closed)")
    if st.st_nlink > 1:
        raise PathAccessError("hard-linked file is refused (fail-closed)")


def _sha256_fd(base, physical, max_bytes=DEFAULT_MAX_HASH_BYTES):
    # Hash through the fd from _open_physical, so a swapped or hard-linked file is never read.
    # An unreadable file is not hashed and does not stop the scan; the error names no path.
    try:
        fd = _open_physical(base, physical)
    except (OSError, ValueError):
        return None
    try:
        with os.fdopen(fd, "rb") as f:
            if os.fstat(f.fileno()).st_size > max_bytes:
                return None
            digest = hashlib.sha256()
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def scan(root_path, max_files=DEFAULT_MAX_FILES, include_hidden=False,
         hash_files=False, max_hash_bytes=DEFAULT_MAX_HASH_BYTES, base_dir=None):
    root = resolve_root(root_path, base_dir=base_dir)
    allowed = Path(_expand_base(base_dir)).resolve()
    files = []
    summary = {
        "total_files": 0,
        "total_size_bytes": 0,
        "by_extension": {},
        "by_type": {},
        "risk_flags": {},
    }
    truncated = False

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames
            if name not in SKIP_DIRS and (include_hidden or not name.startswith("."))
            and _readable_path(Path(dirpath) / name, allowed) is not None  # dir symlink outside: never walked
        ]
        for filename in filenames:
            if not include_hidden and filename.startswith("."):
                continue
            path = Path(dirpath) / filename
            target = _readable_path(path, allowed)
            if target is None or _is_hardlink(target):
                continue  # file symlink outside, or a hard link: no name, size or hash
            if len(files) >= max_files:
                truncated = True
                dirnames[:] = []
                break
            rel = path.relative_to(root).as_posix()
            try:
                st = _stat_physical(allowed, target, rel)
            except (OSError, ValueError) as exc:
                files.append({"path": rel, "error": getattr(exc, "strerror", None) or type(exc).__name__})
                continue

            ext = path.suffix.lower() or "(none)"
            kind = classify_type(path)
            mime, _encoding = mimetypes.guess_type(str(path))
            flags = risk_flags(path, st.st_mode)
            item = {
                "path": rel,
                "size_bytes": st.st_size,
                "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                "extension": ext,
                "type": kind,
                "mime": mime or "",
                "risk_flags": flags,
            }
            if hash_files:
                digest = _sha256_fd(allowed, target, max_bytes=max_hash_bytes)
                item["sha256"] = digest
                if digest is None:
                    item["hash_skipped"] = True

            files.append(item)
            summary["total_files"] += 1
            summary["total_size_bytes"] += st.st_size
            summary["by_extension"][ext] = summary["by_extension"].get(ext, 0) + 1
            summary["by_type"][kind] = summary["by_type"].get(kind, 0) + 1
            for flag in flags:
                summary["risk_flags"][flag] = summary["risk_flags"].get(flag, 0) + 1

        if truncated:
            break

    return {
        "path": str(root),
        "mode": "read-only",
        "max_files": max_files,
        "include_hidden": include_hidden,
        "hash_files": hash_files,
        "truncated": truncated,
        "summary": summary,
        "files": files,
    }


def render_markdown(report):
    lines = [
        "# File inventory",
        "",
        f"Path: `{report['path']}`",
        f"Files: {report['summary']['total_files']}",
        f"Truncated: {report['truncated']}",
        "",
        "| Path | Size | Type | MIME | Risk |",
        "|---|---:|---|---|---|",
    ]
    for item in report["files"]:
        if "error" in item:
            lines.append(f"| `{item['path']}` | — | error | — | {item['error']} |")
            continue
        risk = ", ".join(item["risk_flags"]) if item["risk_flags"] else ""
        lines.append("| `%s` | %s | %s | %s | %s |" % (
            item["path"], item["size_bytes"], item["type"], item["mime"], risk
        ))
    return "\n".join(lines) + "\n"


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="inventory.py")
    parser.add_argument("path")
    parser.add_argument("--base", default="", help="allowed root, required: the report stays inside it")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--hash", action="store_true", dest="hash_files")
    parser.add_argument("--max-hash-bytes", type=int, default=DEFAULT_MAX_HASH_BYTES)
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if not args.base.strip():
        print(json.dumps({"error": "ConfigError", "message": "--base is required: pass the allowed root (fail-closed)"}, ensure_ascii=False))
        return 2
    try:
        report = scan(
            args.path,
            max_files=args.max_files,
            include_hidden=args.include_hidden,
            hash_files=args.hash_files,
            max_hash_bytes=args.max_hash_bytes,
            base_dir=os.path.abspath(_expand_base(args.base)),
        )
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1

    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
