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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # drivers/ — общие хелперы
import codex_local as cl
from audit import audit  # аудит вызовов: risk=medium (driver-safety-policy, ревью T-078 E)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("codex-local")


@mcp.tool()
def codex_available() -> dict:
    """codex-local: установлен ли локальный Codex (read-only)."""
    audit("codex-local", "codex_available", None)
    return {"available": cl.available()}


@mcp.tool()
def codex_info() -> dict:
    """codex-local: путь и версия локального Codex (безопасный `--version`)."""
    audit("codex-local", "codex_info", None)
    return cl.info()


if __name__ == "__main__":
    mcp.run()
