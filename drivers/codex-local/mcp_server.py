#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-сервер `codex-local` (read-only detect). Обёртка над codex_local.py.

Отдаёт только безопасные read-only инструменты (наличие + версия Codex).
Делегирование задач Codex — отдельный high-risk слой (решение + песочница).

ВНИМАНИЕ: написано без прогона. Прогнать `python drivers/codex-local/test_codex_local.py`.

Запуск:
    python drivers/codex-local/mcp_server.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codex_local as cl
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("codex-local")


@mcp.tool()
def codex_available() -> dict:
    """codex-local: установлен ли локальный Codex (read-only)."""
    return {"available": cl.available()}


@mcp.tool()
def codex_info() -> dict:
    """codex-local: путь и версия локального Codex (безопасный `--version`)."""
    return cl.info()


if __name__ == "__main__":
    mcp.run()
