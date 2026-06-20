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
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import files_driver as fd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("files")


@mcp.tool()
def list_files(directory: str) -> list:
    """Рекурсивный список файлов в разрешённой папке (read-only)."""
    return fd.list_files(directory)


@mcp.tool()
def read_file(path: str, max_bytes: int = 1000000) -> dict:
    """Прочитать файл (read-only) с усечением по max_bytes; возвращает text/bytes/truncated."""
    return fd.read_file(path, max_bytes)


@mcp.tool()
def search(pattern: str, directory: str) -> list:
    """Найти regex-паттерн в файлах папки. Секрет-значения (API_KEY=… и т.п.) маскируются."""
    return fd.search(pattern, directory)


@mcp.tool()
def summarize(directory: str) -> dict:
    """Сводка по папке: число файлов, общий размер, разбивка по расширениям."""
    return fd.summarize(directory)


if __name__ == "__main__":
    mcp.run()
