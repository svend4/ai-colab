#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP-сервер `sqlite` (read-only) — инспекция и запрос SQLite-БД. Обёртка над sqlite_driver.py.

Только чтение: БД открывается `mode=ro` на уровне СУБД; `query` принимает лишь одиночный
SELECT/WITH. Зона ограничена `SQLITE_DRIVER_BASE` (allowed-root). risk: medium → аудит вызовов.

Запуск:
    SQLITE_DRIVER_BASE=<allowed-root> python drivers/sqlite/mcp_server.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # drivers/ — общие хелперы
import sqlite_driver as sd
from audit import audit  # аудит вызовов: risk=medium (policy, D-015)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sqlite")
BASE = os.environ.get("SQLITE_DRIVER_BASE") or os.getcwd()


@mcp.tool()
def list_tables(db: str) -> list:
    """sqlite: список таблиц/представлений БД (read-only)."""
    audit("sqlite", "list_tables", db)
    return sd.list_tables(db, base_dir=BASE)


@mcp.tool()
def table_schema(db: str, table: str) -> list:
    """sqlite: схема таблицы (колонки/типы/pk), read-only."""
    audit("sqlite", "table_schema", db, table=table)
    return sd.table_schema(db, table, base_dir=BASE)


@mcp.tool()
def table_head(db: str, table: str, n: int = 100) -> list:
    """sqlite: первые n строк таблицы (read-only, redaction секретов)."""
    audit("sqlite", "table_head", db, table=table, n=n)
    return sd.table_head(db, table, n=n, base_dir=BASE)


@mcp.tool()
def query(db: str, sql: str) -> list:
    """sqlite: одиночный read-only SELECT/WITH (mode=ro, лимит строк, redaction)."""
    audit("sqlite", "query", db)
    return sd.query(db, sql, base_dir=BASE)


if __name__ == "__main__":
    mcp.run()
