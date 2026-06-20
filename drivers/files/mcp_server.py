#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-сервер `files` (read-only) — T-046.

Настоящий MCP-сервер (stdio, FastMCP) поверх движка `files_driver.py`. Любой
ИИ-клиент (Codex/Claude/Cursor) подключается и видит 4 инструмента — это первый
живой L2-драйвер, «прозрачная прослойка» из задачи Max.

Запуск как MCP-сервер:
    python drivers/files/mcp_server.py

Подключение (пример для Codex `~/.codex/config.toml`):
    [mcp_servers.files]
    command = "python"
    args = ["<repo>/drivers/files/mcp_server.py"]

Ограничение зоны:
    FILES_DRIVER_BASE=<allowed-root> python drivers/files/mcp_server.py

Если FILES_DRIVER_BASE не задан, allowed-root равен текущей рабочей папке процесса.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import files_driver as fd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("files")
BASE_DIR = os.environ.get("FILES_DRIVER_BASE") or os.getcwd()


@mcp.tool()
def list_files(directory: str, max_files: int = 1000, include_hidden: bool = False) -> list:
    """Рекурсивный список файлов в разрешённой папке (read-only)."""
    return fd.list_files(directory, max_files=max_files, include_hidden=include_hidden, base_dir=BASE_DIR)


@mcp.tool()
def read_file(path: str, max_bytes: int = 1000000) -> dict:
    """Прочитать файл (read-only) внутри allowed-root с усечением и redaction по умолчанию."""
    return fd.read_file(path, max_bytes, base_dir=BASE_DIR, redact=True)


@mcp.tool()
def search(
    pattern: str,
    directory: str,
    max_files: int = 1000,
    max_hits: int = 1000,
    include_hidden: bool = False,
) -> list:
    """Найти строку в файлах allowed-root. MCP-surface использует безопасный substring-search."""
    return fd.search(pattern, directory, max_files=max_files, max_hits=max_hits,
                     include_hidden=include_hidden, base_dir=BASE_DIR, regex=False)


@mcp.tool()
def summarize(directory: str, max_files: int = 1000, include_hidden: bool = False) -> dict:
    """Сводка по папке: число файлов, общий размер, разбивка по расширениям."""
    return fd.summarize(directory, max_files=max_files, include_hidden=include_hidden, base_dir=BASE_DIR)


if __name__ == "__main__":
    mcp.run()
