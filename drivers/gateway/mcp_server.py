#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-gateway — один сервер отдаёт инструменты всех L2-драйверов разом.

Композиция уже протестированных движков: `files_driver` (T-043), `repo-runner`
inventory (T-024) и `workbench.db` (T-052). Любой ИИ-клиент подключает ОДИН
сервер и получает доступ к файлам, инспекции репозиториев и памяти.

Движки грузятся по явному пути (в drivers/ два разных inventory.py — bare import
коллизирует; тот же приём, что в ingest.py).

Запуск:
    GATEWAY_BASE=<allowed-root> python drivers/gateway/mcp_server.py

Проверка (handshake), на Windows:
    python -c "import asyncio,sys; from mcp import ClientSession,StdioServerParameters; from mcp.client.stdio import stdio_client;
    p=StdioServerParameters(command=sys.executable,args=[r'drivers/gateway/mcp_server.py']);
    async def t():
      async with stdio_client(p) as (r,w):
        async with ClientSession(r,w) as s:
          await s.initialize(); print(sorted(x.name for x in (await s.list_tools()).tools));
    asyncio.run(t())"
"""
import os
import sys
import importlib.util
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVERS = os.path.dirname(HERE)


def _load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DRIVERS, *parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fd = _load("files_driver_mod", "files", "files_driver.py")
inv = _load("rr_inventory", "repo-runner", "inventory.py")
wb = _load("wb_workbench", "workbench", "workbench.py")

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ai-os-bridge")
BASE = os.environ.get("GATEWAY_BASE") or os.getcwd()


# --- files ---
@mcp.tool()
def files_list(directory: str, max_files: int = 1000) -> list:
    """files: рекурсивный список файлов в allowed-root (read-only)."""
    return fd.list_files(directory, max_files=max_files, base_dir=BASE)


@mcp.tool()
def files_read(path: str, max_bytes: int = 1000000) -> dict:
    """files: прочитать файл (read-only, усечение, маскировка секретов)."""
    return fd.read_file(path, max_bytes, base_dir=BASE, redact=True)


@mcp.tool()
def files_search(pattern: str, directory: str, max_hits: int = 1000) -> list:
    """files: поиск строки в файлах (read-only, секреты маскируются)."""
    return fd.search(pattern, directory, max_hits=max_hits, base_dir=BASE, regex=False)


@mcp.tool()
def files_summarize(directory: str) -> dict:
    """files: сводка по папке (файлы, размер, расширения)."""
    return fd.summarize(directory, base_dir=BASE)


# --- repo-runner ---
@mcp.tool()
def repo_inspect(repo_path: str, max_files: int = 1000) -> dict:
    """repo-runner: read-only inventory репозитория (структура/языки/тесты/риски; код не запускается)."""
    return inv.scan_repo(repo_path, max_files=max_files, base_dir=BASE)


# --- workbench memory ---
@mcp.tool()
def memory_query(db: str, type: Optional[str] = None, risk: Optional[str] = None,
                 text: Optional[str] = None, limit: int = 100) -> list:
    """workbench: поиск по памяти (documents) по типу/риску/тексту."""
    conn = wb.init(db, base_dir=BASE)
    try:
        return wb.query_documents(conn, type=type, risk=risk, text=text, limit=limit)
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run()
