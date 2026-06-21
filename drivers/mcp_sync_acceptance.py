#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Синхронная MCP `tools/call`-приёмка драйверов (шаг 2/4 плана разработки).

Переносимая между средами альтернатива `drivers/mcp_acceptance_test.py`: вместо
async stdio-клиента (который на части Windows-сред падает `WinError 5`) использует
синхронный `SyncMcpClient` (subprocess.Popen + JSON-RPC) из `drivers/mcp_sync_probe.py`
(T-087, Codex) и расширяет его до реального вызова каждого инструмента.

Делает по каждому серверу: initialize → tools/list → `tools/call` по каждому инструменту
с реальными аргументами против `data/fixtures` (внутри allowed-root = repo root) и проверяет,
что вызов вернул результат без ошибки.

Лежит в `drivers/` (а не `tools/`) намеренно: при запуске из `tools/` локальный
`tools/queue.py` затеняет stdlib `queue`, на котором держится `mcp_sync_probe`.

Запуск:
    python drivers/mcp_sync_acceptance.py                 # все 5 серверов
    python drivers/mcp_sync_acceptance.py gateway         # только gateway
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from mcp_sync_probe import SyncMcpClient  # noqa: E402  (реюз клиента Codex, T-087; та же папка drivers/)

FX = "data/fixtures"
CSV = "data/fixtures/sample-table.csv"
DOC = "data/fixtures/README.md"
TMP_DB = "logs/_sync_acc.db"

# server -> [(tool, arguments), ...]; пути относительны allowed-root (= repo root)
CALLS = {
    "files": [
        ("list_files", {"directory": FX}),
        ("read_file", {"path": DOC}),
        ("search", {"pattern": "sample", "directory": FX}),
        ("summarize", {"directory": FX}),
    ],
    "repo-runner": [
        ("inspect_repo", {"repo_path": FX}),
        ("repo_summary", {"repo_path": FX}),
        ("repo_risks", {"repo_path": FX}),
    ],
    "data": [
        ("list_tables", {"directory": FX}),
        ("columns", {"path": CSV}),
        ("head", {"path": CSV}),
        ("summarize", {"path": CSV}),
    ],
    "codex-local": [
        ("codex_available", {}),
        ("codex_info", {}),
    ],
    "gateway": [
        ("files_list", {"directory": FX}),
        ("files_read", {"path": DOC}),
        ("files_search", {"pattern": "sample", "directory": FX}),
        ("files_summarize", {"directory": FX}),
        ("repo_inspect", {"repo_path": FX}),
        ("memory_query", {"db": TMP_DB}),
    ],
}


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _is_ok(result):
    # FastMCP: успешный вызов → dict с content и без isError; ошибка → isError True.
    return isinstance(result, dict) and not result.get("isError")


def accept(server, timeout):
    client = SyncMcpClient(server, timeout=timeout)
    passed = failed = 0
    try:
        client.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-sync-acceptance", "version": "0.1"},
        })
        client.notify("notifications/initialized", {})
        print("=== %s ===" % server)
        for tool, args in CALLS[server]:
            try:
                res = client.request("tools/call", {"name": tool, "arguments": args})
                if _is_ok(res):
                    print("  ok   %s.%s" % (server, tool))
                    passed += 1
                else:
                    print("  FAIL %s.%s — isError/result: %s" % (server, tool, str(res)[:120]))
                    failed += 1
            except Exception as exc:
                print("  FAIL %s.%s — %s: %s" % (server, tool, type(exc).__name__, str(exc)[:120]))
                failed += 1
    finally:
        client.close()
    return passed, failed


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("servers", nargs="*", default=list(CALLS.keys()))
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args(argv)

    total_p = total_f = 0
    for server in args.servers:
        if server not in CALLS:
            print("FAIL %s: unknown server" % server)
            total_f += 1
            continue
        try:
            p, f = accept(server, timeout=args.timeout)
        except Exception as exc:
            print("FAIL %s - сервер не поднялся: %s: %s" % (server, type(exc).__name__, str(exc)[:160]))
            p, f = 0, len(CALLS[server])
        total_p += p
        total_f += f

    dbp = os.path.join(ROOT, TMP_DB)
    if os.path.exists(dbp):
        try:
            os.remove(dbp)
        except OSError:
            pass

    print("-" * 50)
    print("SYNC ACCEPTANCE pass=%d fail=%d" % (total_p, total_f))
    print("RESULT", "OK" if total_f == 0 else "FAIL")
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
