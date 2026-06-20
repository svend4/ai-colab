#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handshake-тест новых MCP-серверов: data, codex-local, gateway.

Поднимает каждый сервер по stdio, делает initialize + tools/list и печатает
число инструментов. Запуск:  python drivers/mcp_handshake_test.py
"""
import os
import sys
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVERS = {
    "data": "drivers/data/mcp_server.py",
    "codex-local": "drivers/codex-local/mcp_server.py",
    "gateway": "drivers/gateway/mcp_server.py",
}


async def check(rel):
    params = StdioServerParameters(command=sys.executable, args=[os.path.join(ROOT, rel)])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tl = await s.list_tools()
            return sorted(t.name for t in tl.tools)


async def main():
    ok = True
    for name, rel in SERVERS.items():
        try:
            names = await check(rel)
            print("OK %s tools=%d %s" % (name, len(names), names))
        except Exception as e:
            ok = False
            print("FAIL %s: %s %s" % (name, type(e).__name__, str(e)[:150]))
    print("RESULT", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
