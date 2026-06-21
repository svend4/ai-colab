# Files MCP acceptance blocked

Date: 2026-06-21

Author: Codex

Related:

- `T-048`
- `T-081`
- `drivers/files/test_files.py`
- `drivers/files/test_inventory.py`
- `drivers/mcp_acceptance_test.py`

## What Changed

During `T-048` acceptance, the files driver unit tests first failed because Python's `tempfile.mkdtemp()` created directories that the same Python process could not write into in this Windows runtime.

Confirmed behavior:

- Python can write directly in the project workspace.
- Python can write into a directory created ahead of time with `os.makedirs()`.
- Python fails when a test directory is created through `tempfile.mkdtemp()` / `TemporaryDirectory()` in this environment.

To avoid this runtime-specific temp bug, I added:

- `drivers/test_tmp.py`

and updated:

- `drivers/files/test_files.py`
- `drivers/files/test_inventory.py`
- `drivers/mcp_acceptance_test.py`

The helper creates test directories under `tmp-work/` with `os.makedirs()`.

## Passed

After the temp workaround:

```text
python drivers\files\test_files.py
TESTS OK files=5 hits=1
```

```text
python drivers\files\test_inventory.py
PASS: empty directory
PASS: basic inventory and kinds
PASS: hidden and common dirs skipped
PASS: hash and truncation
PASS: cli json

All tests passed!
```

## Still Blocked

The MCP stdio acceptance still fails before any files tool call:

```text
python drivers\mcp_acceptance_test.py files
=== files ===
  FAIL files - сервер не поднялся: PermissionError: [WinError 5] Отказано в доступе
ACCEPTANCE pass=0 fail=4
RESULT FAIL
```

`python drivers\mcp_handshake_test.py` now fails at the same lower-level point:

```text
asyncio.windows_utils.pipe -> _winapi.CreateFile -> PermissionError: [WinError 5]
```

## Interpretation

`T-048` cannot be closed honestly.

The files engine and inventory tests pass. The remaining blocker is the Windows/MCP stdio subprocess layer: the MCP client cannot create the async pipe needed to launch the server.

## Next Step

Work `T-081`:

- isolate whether the failure is caused by the current Python runtime, the MCP package, Windows permissions, antivirus/controlled-folder access, or inherited sandbox policy;
- compare with a plain `subprocess.Popen(..., stdin=PIPE, stdout=PIPE)` probe;
- if plain subprocess works, narrow to `asyncio`/`anyio`/MCP stdio;
- if subprocess pipes fail generally, treat this as an external runtime permissions blocker.

