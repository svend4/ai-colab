# Ingest acceptance result

Date: 2026-06-21

Author: Codex

Related:

- `T-057`
- `drivers/workbench/ingest.py`
- `drivers/workbench/test_ingest.py`
- `drivers/workbench/test_search.py`
- `drivers/workbench/test_workbench.py`

## Summary

`T-057` acceptance passed for the non-MCP ingest pipeline path.

## Changes

`drivers/workbench/test_ingest.py` and `drivers/workbench/test_search.py` now use `drivers/test_tmp.py` instead of `tempfile.mkdtemp()`.

Reason: the current Windows/Python runtime can create unusable directories through standard `tempfile.mkdtemp()`. The shared helper creates test directories under the ignored local `tmp-work/` folder using `os.makedirs()`.

## Checks

```text
python drivers\workbench\test_ingest.py
TESTS OK ingested=2 docs=2 risky=1 audit=1
```

```text
python drivers\workbench\test_workbench.py
TESTS OK docs=6 audit=1 ingested=2
```

```text
python drivers\workbench\test_search.py
TESTS OK hits=1 top=a.py
```

CLI with `WORKBENCH_BASE`, `INGEST_SOURCE_BASE`, and `INGEST_MAX_FILES=1`:

```text
python drivers\workbench\ingest.py repo ingest.db repo
{"ingested": 1}

python drivers\workbench\ingest.py dir ingest.db folder
{"ingested": 1}

python drivers\workbench\ingest.py repo ingest.db ..\outside
{"error": "PathAccessError", "message": "path is outside allowed root: ...\\tmp-work\\ingest-cli\\outside"}
```

Project checks:

```text
python tools\validate.py
OK=9 WARN=0 ERROR=0

python tools\drivers_catalog.py --check
OK
```

## Interpretation

The ingest runtime acceptance items in `T-057` are satisfied:

- tests for ingest/workbench/search pass;
- CLI `repo` and `dir` work;
- `WORKBENCH_BASE`, `INGEST_SOURCE_BASE`, and `INGEST_MAX_FILES` are exercised;
- outside-root source path returns JSON `PathAccessError`.

