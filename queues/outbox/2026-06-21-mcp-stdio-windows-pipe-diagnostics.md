# Outbox: MCP stdio Windows pipe diagnostics

Date: 2026-06-21

Author: Codex

Task: `T-081`

## Result

`T-081` isolated the blocker:

- plain `subprocess.Popen(..., stdout=PIPE, stderr=PIPE)` works;
- `asyncio.create_subprocess_exec(..., stdout=PIPE, stderr=PIPE)` fails with `PermissionError [WinError 5]`;
- `WindowsSelectorEventLoopPolicy` does not help (`NotImplementedError`);
- MCP stdio uses the failing asyncio subprocess path.

Conclusion: MCP stdio acceptance is blocked by the current Windows/Python runtime pipe permissions, not by the `files` driver logic.

Next practical work: continue non-MCP tasks or run MCP acceptance in a different environment where asyncio subprocess pipes work.

