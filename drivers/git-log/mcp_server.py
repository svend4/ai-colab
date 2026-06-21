#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-сервер `git-log` (read-only) — история git. Обёртка над git_log.py.

Только read-only метаданные git (коммиты/авторы/история файла/сводка); код репозитория
НЕ запускается. Зона ограничена `GIT_LOG_BASE` (allowed-root). risk: medium → вызовы аудируются.

Запуск:
    GIT_LOG_BASE=<allowed-root> python drivers/git-log/mcp_server.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # drivers/ — общие хелперы
import git_log as gl
from audit import audit  # аудит вызовов: risk=medium (policy, D-015)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("git-log")
BASE = os.environ.get("GIT_LOG_BASE") or os.getcwd()


@mcp.tool()
def recent_commits(repo: str, n: int = 20) -> list:
    """git-log: последние n коммитов (hash/author/date/subject), read-only."""
    audit("git-log", "recent_commits", repo, n=n)
    return gl.recent_commits(repo, n=n, base_dir=BASE)


@mcp.tool()
def author_stats(repo: str) -> list:
    """git-log: число коммитов по авторам (по убыванию), read-only."""
    audit("git-log", "author_stats", repo)
    return gl.author_stats(repo, base_dir=BASE)


@mcp.tool()
def file_history(repo: str, path: str, n: int = 20) -> list:
    """git-log: история коммитов, затрагивающих файл, read-only."""
    audit("git-log", "file_history", repo, path=path, n=n)
    return gl.file_history(repo, path, n=n, base_dir=BASE)


@mcp.tool()
def repo_summary(repo: str) -> dict:
    """git-log: сводка — ветка, всего коммитов, число авторов, топ-авторы, последний коммит."""
    audit("git-log", "repo_summary", repo)
    return gl.summary(repo, base_dir=BASE)


if __name__ == "__main__":
    mcp.run()
