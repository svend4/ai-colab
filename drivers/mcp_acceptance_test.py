#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Приёмочный тест драйверов (driver acceptance batch).

Идёт дальше handshake: поднимает каждый MCP-сервер по stdio и реально вызывает
КАЖДЫЙ инструмент (call_tool) на временном фикстуре, проверяя факты, а не только
отсутствие ошибки:
  - files.search находит подстроку; files.read_file маскирует секрет (redaction);
  - repo-runner помечает risk (run.sh); data читает CSV; codex-local не падает;
  - gateway отдаёт files/repo/memory; memory_query возвращает занесённый документ.

Запуск:
    python drivers/mcp_acceptance_test.py            # все серверы
    python drivers/mcp_acceptance_test.py gateway    # только один сервер
Требует пакет mcp (как и mcp_handshake_test.py).
"""
import os
import sys
import json
import asyncio
import shutil

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_SECRET = "AKIA1234567890DEADBEEF"  # должен быть замаскирован в выводе read_file
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir


def build_fixture(base):
    with open(os.path.join(base, "notes.txt"), "w", encoding="utf-8") as f:
        f.write("hello NEEDLE world\nsecond line\n")
    with open(os.path.join(base, "secret.txt"), "w", encoding="utf-8") as f:
        f.write("api_key = '%s'\n" % RAW_SECRET)
    repo = os.path.join(base, "repo")
    os.makedirs(repo, exist_ok=True)
    with open(os.path.join(repo, "app.py"), "w", encoding="utf-8") as f:
        f.write("print('hi')\n")
    with open(os.path.join(repo, "run.sh"), "w", encoding="utf-8") as f:
        f.write("echo hi\n")
    with open(os.path.join(base, "t.csv"), "w", encoding="utf-8") as f:
        f.write("a,b,c\n1,2,3\n4,5,6\n")
    sys.path.insert(0, os.path.join(ROOT, "drivers", "workbench"))
    import workbench as wb
    db = os.path.join(base, "mem.db")
    conn = wb.init(db)
    wb.add_document(conn, "src", "repo/app.py", summary="memory doc one", risk="low")
    conn.close()
    return repo, db


def server_params(rel, base_env):
    env = dict(os.environ)
    env.update(base_env)
    return StdioServerParameters(command=sys.executable,
                                 args=[os.path.join(ROOT, rel)], env=env)


def _text(res):
    parts = []
    for c in (res.content or []):
        t = getattr(c, "text", None)
        if t:
            parts.append(t)
    if not parts and getattr(res, "structuredContent", None) is not None:
        parts.append(json.dumps(res.structuredContent, ensure_ascii=False))
    return "\n".join(parts)


async def run_server(name, params, calls):
    passed, failed, details = 0, 0, []
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for tool, args, contains, absent in calls:
                try:
                    res = await s.call_tool(tool, args)
                    text = _text(res)
                    err = bool(getattr(res, "isError", False))
                    reason = ""
                    if err:
                        reason = "isError"
                    elif contains is not None and contains not in text:
                        reason = "нет ожидаемого %r" % contains
                    elif absent is not None and absent in text:
                        reason = "утечка %r" % absent
                    if reason:
                        failed += 1
                        details.append("  FAIL %s.%s - %s" % (name, tool, reason))
                    else:
                        passed += 1
                        details.append("  ok   %s.%s" % (name, tool))
                except Exception as e:
                    failed += 1
                    details.append("  FAIL %s.%s - %s: %s"
                                   % (name, tool, type(e).__name__, str(e)[:100]))
    return passed, failed, details


async def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    base = make_temp_dir("mcp_accept_")
    total_pass, total_fail, lines = 0, 0, []
    try:
        repo, db = build_fixture(base)
        csv = os.path.join(base, "t.csv")
        notes = os.path.join(base, "notes.txt")
        secret = os.path.join(base, "secret.txt")

        plan = [
            ("files", "drivers/files/mcp_server.py", {"FILES_DRIVER_BASE": base}, [
                ("list_files", {"directory": base}, "notes.txt", None),
                ("read_file", {"path": secret}, None, RAW_SECRET),
                ("search", {"pattern": "NEEDLE", "directory": base}, "NEEDLE", None),
                ("summarize", {"directory": base}, None, None),
            ]),
            ("repo-runner", "drivers/repo-runner/mcp_server.py", {"REPO_RUNNER_BASE": base}, [
                ("inspect_repo", {"repo_path": repo}, "app.py", None),
                ("repo_summary", {"repo_path": repo}, None, None),
                ("repo_risks", {"repo_path": repo}, "run.sh", None),
            ]),
            ("data", "drivers/data/mcp_server.py", {"DATA_DRIVER_BASE": base}, [
                ("list_tables", {"directory": base}, "t.csv", None),
                ("columns", {"path": csv}, "a", None),
                ("head", {"path": csv}, None, None),
                ("summarize", {"path": csv}, None, None),
            ]),
            ("codex-local", "drivers/codex-local/mcp_server.py", {}, [
                ("codex_available", {}, "available", None),
                ("codex_info", {}, None, None),
            ]),
            ("gateway", "drivers/gateway/mcp_server.py", {"GATEWAY_BASE": base}, [
                ("files_list", {"directory": base}, "notes.txt", None),
                ("files_read", {"path": notes}, "NEEDLE", None),
                ("files_search", {"pattern": "NEEDLE", "directory": base}, "NEEDLE", None),
                ("files_summarize", {"directory": base}, None, None),
                ("repo_inspect", {"repo_path": repo}, "app.py", None),
                ("memory_query", {"db": db}, "memory doc one", None),
            ]),
        ]

        for name, rel, env, calls in plan:
            if only and name != only:
                continue
            lines.append("=== %s ===" % name)
            try:
                p, f, det = await run_server(name, server_params(rel, env), calls)
            except Exception as e:
                p, f, det = 0, len(calls), ["  FAIL %s - сервер не поднялся: %s: %s"
                                            % (name, type(e).__name__, str(e)[:100])]
            total_pass += p
            total_fail += f
            lines.extend(det)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("\n".join(lines))
    print("-" * 50)
    print("ACCEPTANCE pass=%d fail=%d" % (total_pass, total_fail))
    print("RESULT", "OK" if total_fail == 0 else "FAIL")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
