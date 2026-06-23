---
type: report
tool: drivers/mcp_async_stdio_monitor.py
date: 2026-06-23
server: gateway
---

# MCP async stdio monitor

## Verdict

- async_state: `blocked-before-mcp`
- sync_state: `sync-ok`
- recommendation: Keep sync acceptance as the regular gate; retest async after Python/Windows/mcp runtime changes.

## Probe

```text
winerror-5: PermissionError: [WinError 5] Отказано в доступе
```

## sync-acceptance

- command: `C:\Users\stefan\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe C:\Users\stefan\Documents\New project ai colab\drivers\mcp_sync_acceptance.py gateway`
- status: `ok`
- returncode: `0`

```text
=== gateway ===
  ok   gateway.files_list
  ok   gateway.files_read
  ok   gateway.files_search
  ok   gateway.files_summarize
  ok   gateway.repo_inspect
  ok   gateway.memory_query
--------------------------------------------------
SYNC ACCEPTANCE pass=6 fail=0
RESULT OK
```

