---
status: historical
---
# Outbox: T-087 MCP sync probe result

Date: 2026-06-21

Author: Codex

## Result

`T-087` succeeded.

Added `drivers/mcp_sync_probe.py`, a synchronous MCP stdio smoke probe that avoids `asyncio.create_subprocess_exec`.

Results:

- `data` tools-list OK;
- `codex-local` tools-list OK;
- `files` tools-list OK;
- `repo-runner` tools-list OK;
- `gateway` tools-list OK.

Important detail: installed `mcp.server.stdio` uses line-delimited JSON-RPC, not `Content-Length` framing.

Next useful task: extend this sync probe into sync `tools/call` acceptance so `T-048` and `T-051` can be unblocked without relying on the broken asyncio subprocess path.

