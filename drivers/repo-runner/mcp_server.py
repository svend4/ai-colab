#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-сервер `repo-runner` (read-only inventory) — T-049.

Тонкая обёртка над движком `inventory.scan_repo` в настоящий MCP-сервер (FastMCP,
stdio). Только инспекция репозитория: структура, языки, пакеты, тесты, риски.
**Код НЕ запускается** — это read-only L2-драйвер (запуск кода — отдельный слой и
решение по D-010 + песочница).

Запуск:
    python drivers/repo-runner/mcp_server.py

Подключение (Codex `~/.codex/config.toml`):
    [mcp_servers.repo-runner]
    command = "python"
    args = ["<repo>/drivers/repo-runner/mcp_server.py"]

Ограничение зоны:
    REPO_RUNNER_BASE=<allowed-root> python drivers/repo-runner/mcp_server.py

Если REPO_RUNNER_BASE не задан, allowed-root равен текущей рабочей папке процесса.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inventory
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("repo-runner")
BASE_DIR = os.environ.get("REPO_RUNNER_BASE") or os.getcwd()


@mcp.tool()
def inspect_repo(repo_path: str, max_files: int = 1000) -> dict:
    """Полный read-only inventory репозитория: структура, языки, package-файлы, тесты, риски. Код не запускается."""
    return inventory.scan_repo(repo_path, max_files=max_files, base_dir=BASE_DIR)


@mcp.tool()
def repo_summary(repo_path: str, max_files: int = 1000) -> dict:
    """Краткая сводка: число файлов, размер, языки, наличие тестов, число рисков."""
    report = inventory.scan_repo(repo_path, max_files=max_files, base_dir=BASE_DIR)
    return report.get("summary", report)


@mcp.tool()
def repo_risks(repo_path: str, max_files: int = 1000) -> list:
    """Список потенциально опасных файлов/паттернов (shell, eval/exec, сеть) — только пометка, без запуска."""
    report = inventory.scan_repo(repo_path, max_files=max_files, base_dir=BASE_DIR)
    return report.get("risks", [])


if __name__ == "__main__":
    mcp.run()
