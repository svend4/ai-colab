# MCP sync probe result

Date: 2026-06-21

Author: Codex

Related:

- `T-087`
- `T-048`
- `T-051`
- `T-081`
- `drivers/mcp_sync_probe.py`

## Summary

`T-087` succeeded: a synchronous MCP stdio probe now works without `asyncio.create_subprocess_exec`.

This avoids the Windows/Python runtime failure documented in `docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md`.

## Implementation

Added:

- `drivers/mcp_sync_probe.py`

The script uses:

- `subprocess.Popen(..., stdin=PIPE, stdout=PIPE, stderr=PIPE)`;
- line-delimited JSON-RPC, matching the installed `mcp.server.stdio` transport;
- `initialize`;
- `notifications/initialized`;
- `tools/list`.

Important correction: this MCP package's stdio transport does not use `Content-Length` framing. It reads and writes one JSON-RPC message per line.

## Checks

```text
python drivers\mcp_sync_probe.py data codex-local --timeout 60
OK data tools=4 ['columns', 'head', 'list_tables', 'summarize']
OK codex-local tools=2 ['codex_available', 'codex_info']
RESULT OK
```

```text
python drivers\mcp_sync_probe.py files repo-runner gateway --timeout 90
OK files tools=4 ['list_files', 'read_file', 'search', 'summarize']
OK repo-runner tools=3 ['inspect_repo', 'repo_risks', 'repo_summary']
OK gateway tools=6 ['files_list', 'files_read', 'files_search', 'files_summarize', 'memory_query', 'repo_inspect']
RESULT OK
```

## Interpretation

The stdio subprocess blocker is narrower than previously thought:

- `asyncio` subprocess pipes are still broken in this environment;
- synchronous subprocess stdio works;
- MCP initialize/tools-list can be tested locally through `drivers/mcp_sync_probe.py`.

This does not automatically close `T-048` or `T-051`, because those require call_tool acceptance, not only tools/list. It does provide the base needed for a future sync call_tool acceptance script.

