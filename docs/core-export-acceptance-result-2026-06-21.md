---
id: core-export-acceptance-result-2026-06-21
type: report
title: Core export acceptance result
status: done
related: T-140, core/engine-manifest.md, docs/pyramid-candidate-map.md
---

# Core export acceptance — result

## What was checked

Stage 4 core-export mechanism was checked as a proposed, non-final L1 export path:

- `core/engine-manifest.md` lists the first candidate file-native agent-coordination engine;
- `tools/promote.py export --to <dir> --manifest core/engine-manifest.md` copies files, not moves them;
- `tools/tests/test_promote_export.py` verifies copy semantics, `EXPORT.md`, missing-file reporting and manifest parsing.

## Fix made

`tools/tests/test_promote_export.py` originally used standard `tempfile.mkdtemp()`. In this Windows runtime,
standard `%TEMP%` can create directories that the same Python process cannot write into. The test now uses
`drivers/test_tmp.py` / repo-local `tmp-work/`, matching the established test convention.

## Verification

Passed:

```powershell
python tools/tests/test_promote_export.py
python tools/tests/test_promote.py
python tools/promote.py export --to tmp-work/core-export-smoke --manifest core/engine-manifest.md
python tools/top.py health
```

The smoke export copied 10 files and reported 0 missing files. Runtime output stays under ignored
`tmp-work/` and is not part of the repository.

## Status

This verifies the mechanism, not the governance decision. `core/engine-manifest.md` remains `proposed`:
Q2 (exact first core-export composition) still belongs to collective review under D-018.
