#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git-log driver (L2, read-only) — история git репозитория.

Безопасный read-only доступ к метаданным git: последние коммиты, статистика по авторам,
история файла, краткая сводка. Только чтение: вызывается строго фиксированный whitelist
`git log/rev-list/branch` (никаких пользовательских git-подкоманд), репозиторий ограничен
allowed-root, есть таймаут и лимит вывода. Код репозитория НЕ запускается (git log не
исполняет hooks). Потом тонко оборачивается в MCP-сервер.

CLI:
    python git_log.py recent <repo> [--n N]
    python git_log.py authors <repo>
    python git_log.py file <repo> <path> [--n N]
    python git_log.py summary <repo>
"""
import os
import sys
import json
import subprocess
from collections import Counter
from pathlib import Path

DEFAULT_LIMIT = 20
MAX_LIMIT = 1000
TIMEOUT = 15
SEP = "\x1f"


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


class PathAccessError(ValueError):
    pass


class NotARepoError(ValueError):
    pass


def _resolve_repo(repo, base_dir=None):
    if base_dir is None:
        p = Path(repo).expanduser().resolve()
    else:
        base = Path(base_dir).expanduser().resolve()
        raw = Path(repo).expanduser()
        p = (raw if raw.is_absolute() else base / raw).resolve()
        try:
            p.relative_to(base)
        except ValueError:
            raise PathAccessError("repo path is outside allowed root: %s" % p)
    if not (p / ".git").exists():
        raise NotARepoError("not a git repository: %s" % p)
    return p


def _git(repo_path, args, timeout=TIMEOUT):
    """Запуск read-only git-команды. args — только из доверенного whitelist вызывающего.

    `stdin=DEVNULL` обязателен: когда драйвер работает как MCP-сервер (subprocess под
    pipe-stdio), без этого `git` наследует stdin-пайп asyncio-сервера и на Windows
    возникает дедлок overlapped I/O — `tools/call` виснет (in-process путь не затронут).
    """
    proc = subprocess.run(
        ["git", "-C", str(repo_path)] + args,
        stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (args[0], (proc.stderr or "").strip()[:200]))
    return proc.stdout


def _clamp(n):
    return max(1, min(int(n), MAX_LIMIT))


def _parse_commits(out):
    rows = []
    for line in out.splitlines():
        parts = line.split(SEP)
        if len(parts) == 4:
            rows.append({"hash": parts[0], "author": parts[1], "date": parts[2], "subject": parts[3]})
    return rows


_FMT = "--pretty=format:%h" + SEP + "%an" + SEP + "%ad" + SEP + "%s"


def recent_commits(repo, n=DEFAULT_LIMIT, base_dir=None):
    p = _resolve_repo(repo, base_dir)
    out = _git(p, ["log", "--no-color", "-n", str(_clamp(n)), _FMT, "--date=short"])
    return _parse_commits(out)


def author_stats(repo, base_dir=None, max_commits=5000):
    p = _resolve_repo(repo, base_dir)
    out = _git(p, ["log", "--no-color", "-n", str(_clamp(max_commits)), "--pretty=format:%an"])
    counts = Counter(line.strip() for line in out.splitlines() if line.strip())
    return [{"author": a, "commits": c} for a, c in counts.most_common()]


def file_history(repo, path, n=DEFAULT_LIMIT, base_dir=None):
    p = _resolve_repo(repo, base_dir)
    # path — pathspec после `--`, git трактует его как путь, не как команду
    out = _git(p, ["log", "--no-color", "-n", str(_clamp(n)), _FMT, "--date=short", "--", path])
    return _parse_commits(out)


def summary(repo, base_dir=None):
    p = _resolve_repo(repo, base_dir)
    total = _git(p, ["rev-list", "--count", "HEAD"]).strip()
    branch = _git(p, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    authors = author_stats(p, base_dir=base_dir)
    last = recent_commits(p, n=1, base_dir=base_dir)
    return {
        "repo": p.name,
        "branch": branch,
        "total_commits": int(total) if total.isdigit() else None,
        "authors": len(authors),
        "top_authors": authors[:5],
        "last_commit": last[0] if last else None,
    }


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        base_dir = a[a.index("--base") + 1] if "--base" in a else None
        n = int(a[a.index("--n") + 1]) if "--n" in a else DEFAULT_LIMIT
        if cmd == "recent":
            print(json.dumps(recent_commits(a[1], n=n, base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "authors":
            print(json.dumps(author_stats(a[1], base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "file" and len(a) > 2:
            print(json.dumps(file_history(a[1], a[2], n=n, base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
        if cmd == "summary":
            print(json.dumps(summary(a[1], base_dir=base_dir), ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
