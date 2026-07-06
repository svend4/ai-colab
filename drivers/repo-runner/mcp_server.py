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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # drivers/ — общие хелперы
import inventory
from audit import audit  # аудит вызовов: risk=medium (driver-safety-policy, ревью T-078 E)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("repo-runner")
BASE_DIR = os.environ.get("REPO_RUNNER_BASE") or os.getcwd()


def _scan(repo_path: str, max_files: int) -> dict:
    max_files = inventory.clamp_max_files(max_files)
    return inventory.scan_repo(repo_path, max_files=max_files, base_dir=BASE_DIR)


@mcp.tool()
def inspect_repo(repo_path: str, max_files: int = 1000) -> dict:
    """Полный read-only inventory репозитория: структура, языки, package-файлы, тесты, риски. Код не запускается."""
    audit("repo-runner", "inspect_repo", repo_path, max_files=max_files)
    return inventory.limit_output(_scan(repo_path, max_files))


@mcp.tool()
def repo_summary(repo_path: str, max_files: int = 1000) -> dict:
    """Краткая сводка: число файлов, размер, языки, наличие тестов, число рисков."""
    audit("repo-runner", "repo_summary", repo_path, max_files=max_files)
    report = _scan(repo_path, max_files)
    return report.get("summary", report)


@mcp.tool()
def repo_risks(repo_path: str, max_files: int = 1000) -> list:
    """Список потенциально опасных файлов/паттернов (shell, eval/exec, сеть) — только пометка, без запуска."""
    audit("repo-runner", "repo_risks", repo_path, max_files=max_files)
    report = _scan(repo_path, max_files)
    return inventory.limit_output(report.get("risks", []))


if __name__ == "__main__":
    mcp.run()
