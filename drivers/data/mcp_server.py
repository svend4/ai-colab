#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-сервер `data` (read-only) — табличные файлы CSV/TSV. Обёртка над data_driver.py.

ВНИМАНИЕ: написано без прогона (исполнение было недоступно). Перед использованием
прогнать `python drivers/data/test_data.py` и handshake-тест (как у files).

Запуск:
    DATA_DRIVER_BASE=<allowed-root> python drivers/data/mcp_server.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_driver as dd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("data")
BASE = os.environ.get("DATA_DRIVER_BASE") or os.getcwd()


@mcp.tool()
def list_tables(directory: str) -> list:
    """data: список CSV/TSV в allowed-root (read-only)."""
    return dd.list_tables(directory, base_dir=BASE)


@mcp.tool()
def columns(path: str) -> list:
    """data: заголовки таблицы."""
    return dd.columns(path, base_dir=BASE)


@mcp.tool()
def head(path: str, n: int = 10) -> list:
    """data: первые n строк таблицы (read-only)."""
    return dd.head(path, n=n, base_dir=BASE)


@mcp.tool()
def summarize(path: str) -> dict:
    """data: сводка таблицы — строки, колонки, заполненность по колонкам."""
    return dd.summarize(path, base_dir=BASE)


if __name__ == "__main__":
    mcp.run()
