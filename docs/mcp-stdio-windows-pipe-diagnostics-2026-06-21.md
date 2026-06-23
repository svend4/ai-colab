# MCP stdio Windows pipe diagnostics

Date: 2026-06-21

Author: Codex

Related:

- `T-048`
- `T-081`
- `docs/files-mcp-acceptance-blocked-2026-06-21.md`

## Result

The MCP stdio failure is not a general inability to start subprocesses.

Plain subprocess pipes work:

```text
python -c "import subprocess, sys; p=subprocess.Popen([sys.executable,'-c','print(123)'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True); print(p.communicate()); print('returncode', p.returncode)"

('123\n', '')
returncode 0
```

Asyncio subprocess pipes fail:

```text
asyncio.create_subprocess_exec(...)
asyncio.windows_utils.pipe -> _winapi.CreateFile -> PermissionError: [WinError 5]
```

Switching to `asyncio.WindowsSelectorEventLoopPolicy()` does not solve it:

```text
NotImplementedError
```

## Interpretation

The current Windows/Python runtime can run ordinary subprocesses, but cannot create the overlapped pipes used by `asyncio.create_subprocess_exec`.

The MCP Python stdio client uses this asyncio subprocess path, so MCP stdio handshake and acceptance fail before the server tools are called.

This means `T-048` cannot be closed in this runtime even though the files driver engine and inventory tests pass.

## Workarounds

Short-term:

- continue non-MCP work (`T-059`, code cleanup, manifest consistency, docs, validation);
- run MCP stdio acceptance from a different local environment where `asyncio.create_subprocess_exec(..., stdout=PIPE, stderr=PIPE)` succeeds;
- or implement a separate synchronous subprocess-based MCP smoke client using `subprocess.Popen`, if the project wants in-repo MCP checks independent from asyncio pipes.

Do not mark MCP-dependent acceptance tasks done until one of those paths is green.


## Update 2026-06-23 — T-174 monitor

Added `drivers/mcp_async_stdio_monitor.py` as the periodic retest command for this blocker.

Checked command:

```powershell
python drivers\mcp_async_stdio_monitor.py gateway --force-acceptance --out reports\mcp-async-stdio-monitor-forced-2026-06-23.md --json
```

Result:

```text
async-pipe-probe: PermissionError [WinError 5]
legacy async gateway acceptance: ACCEPTANCE pass=0 fail=6, RESULT FAIL
sync gateway acceptance: SYNC ACCEPTANCE pass=6 fail=0, RESULT OK
classification: async_state=blocked-before-mcp, sync_state=sync-ok
```

Interpretation is unchanged: the current runtime still fails before MCP server logic is reached.
Regular gateway acceptance remains the sync `tools/call` path; retest async after Python/Windows/`mcp`
runtime changes.