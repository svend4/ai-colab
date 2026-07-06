---
id: T-273-l2-inventory-wbuild-fixture-2026-07-06
type: report
title: "T-273 L2 inventory — W_build fixture and swarm feedback"
status: proposed
date: 2026-07-06
author: codex
related:
  - T-273
  - PKG-20260706-pilot-t273
  - T-276
  - D-014
  - D-018
  - D-035
---

# T-273 L2 inventory — W_build fixture and swarm feedback

## 1. Verdict

Status: **W_build fixture-ready**.

This report records the first bounded implementation step after `W_safety`: a local fixture run of `tools/l2_inventory.py` against `drivers/file-inventory`, plus swarm feedback and the code guard added from that feedback.

This does **not** run a real external source, does **not** execute external code, does **not** claim `T-273`, and does **not** move `PKG-20260706-pilot-t273` from `draft` to `in-swarm`.

## 2. Swarm assignment and results

### 2.1. Newton — safety verifier

Task: read-only review of `tools/l2_inventory.py` against the pilot boundary.

Result:

- confirmed no external execution, no network, no subprocess, no install/build/test of source code;
- confirmed the tool reads files and writes only the SQLite index target;
- found safety gaps:
  - `--db` could be placed inside `--source`;
  - a careless `--db` could overwrite tables in an existing SQLite file;
  - symlink/reparse-point files could make source confinement weaker;
  - tests did not cover the “db inside source” case.

Applied response:

- added `resolve_db_path()` to reject `--db` inside `--source`;
- added `_is_reparse_or_symlink()` and skip logic for directories/files in the walk;
- added a regression test for `db inside source` rejection.

### 2.2. Copernicus — test worker

Task: verify `tools/tests/test_l2_inventory.py` after removing the Windows `tempfile` failure pattern.

Result:

- confirmed the test no longer uses `tempfile.TemporaryDirectory`;
- found `NameError: db_abs is not defined` in `stats()` after a previous broad replacement.

Applied response:

- fixed `stats()` to return `Path(db_path).resolve()` while keeping `db_abs` only in `build()`;
- reran the standalone test successfully.

### 2.3. Halley — strategic dispatcher

Task: read-only strategic refill while the pilot ran.

Result:

- recommended not to start a new broad layer before completing `W_run -> W_verify x2 -> W_report`;
- defined the upper-layer role as intake, verify, refill and routing into `accepted evidence`, `divergence-detail`, `new task candidate`, or `human decision`;
- suggested the next swarm: one run worker, two independent verifiers, one scribe.

## 3. Code changes made by Codex

### 3.1. `tools/l2_inventory.py`

Changed:

- `resolve_db_path(db_path, source_root)` resolves the DB path and rejects DB placement inside the read-only source.
- `_is_reparse_or_symlink(path)` skips symlink/reparse-point entries before reading metadata/content.
- `build()` now uses a resolved `db_abs` for DB creation and report output.
- `stats()` remains a pure reader and resolves its own displayed DB path without using `db_abs`.

Reason:

The first pilot must prove that the middle layer can process information without writing back into the source. A read-only promise in documentation is not enough; the tool must enforce the most obvious boundary mechanically.

### 3.2. `tools/tests/test_l2_inventory.py`

Changed:

- project-local `_make_project_tmp()` uses repository `tmp-work/`, not the broken Windows stdlib temp path;
- added `test_db_inside_source_rejected()`;
- standalone `run()` now checks the same negative case.

Reason:

This project repeatedly hit Windows `TEMP` permission failures. Tests for pilot tools should use the project-safe temp pattern so agents can rerun them reliably.

## 4. Checks run

### 4.1. Syntax

```powershell
python -m py_compile tools\l2_inventory.py tools\tests\test_l2_inventory.py
```

Result: OK.

### 4.2. Standalone test

```powershell
python tools\tests\test_l2_inventory.py
```

Result:

```text
OK test_l2_inventory: build(5 файлов, 4 текст в ФТС) · stats · query(термины/redact/бинарь) · missing→None
```

### 4.3. Pytest form

```powershell
python -m pytest tools\tests\test_l2_inventory.py -q
```

Result: not available in this Python environment:

```text
No module named pytest
```

This is not a tool failure, but the pilot report should keep it visible.

### 4.4. Fixture build

```powershell
python tools\l2_inventory.py build --source drivers\file-inventory --db tmp-work\t273\fixture-l2-inventory.db --max-text-bytes 204800 --json
```

Result summary:

```text
engine: fts5
total_files: 4
total_size_bytes: 74341
text_indexed: 4
by_extension: .py=2, .json=1, .md=1
```

### 4.5. Fixture stats

```powershell
python tools\l2_inventory.py stats --db tmp-work\t273\fixture-l2-inventory.db --json
```

Result: OK, same counters as build.

### 4.6. Fixture query

```powershell
python tools\l2_inventory.py query --db tmp-work\t273\fixture-l2-inventory.db inventory --limit 5 --json
```

Result: OK, 4 hits: `test_inventory.py`, `inventory.py`, `README.md`, `fixture-report.json`.

### 4.7. Negative DB placement guard

```powershell
python tools\l2_inventory.py build --source drivers\file-inventory --db drivers\file-inventory\inside-source.db --json
```

Result: expected failure:

```text
PathAccessError: --db inside --source запрещён: $WORKSPACE/drivers/file-inventory/inside-source.db
```

Follow-up check:

```powershell
Test-Path drivers\file-inventory\inside-source.db
```

Result: `False`.

## 5. Remaining risks

1. Existing SQLite overwrite risk remains if a user explicitly passes an unrelated existing DB outside source. For the pilot, use only a new DB path under `tmp-work/t273/`.
2. Symlink/reparse-point skipping is implemented, but not deeply regression-tested on Windows because creating such links may require privileges.
3. Real source `W_run` is still not executed. It needs an explicit source path and bounded command.
4. `pytest` is absent in the current runtime; standalone test is the current reliable check.

## 6. Next swarm package

Recommended next controlled swarm:

| Node | Role | Task | Output |
|---|---|---|---|
| W_run | worker | build L2 index on Stefan-approved local source with DB under `tmp-work/t273/` | run log + DB path |
| W_verify_safety | explorer | verify no source writes, no external execution, no secrets in snippets | safety verdict |
| W_verify_utility | explorer | verify counters, sample queries and usefulness for T-276 materializer | utility verdict |
| W_report | scribe | write final `T-273` pilot report and propose next tasks | report + task candidates |

Until the source is selected, the safe next command remains fixture-only.

## 7. Bounded W_run gate update

After Socrates reviewed the draft state, real `W_run` remained **NO-GO** because `--max-files` was only partially inserted. Codex then completed the bounded scan support.

Additional changes:

- `tools/l2_inventory.py` now exposes CLI `--max-files` for `build`.
- `build()` and `stats()` now report `built_at`, `max_text_bytes`, `max_files`, `limit_hit`, `skipped_dirs`, `skipped_symlink_or_reparse`, `skipped_outside_root`, and `read_errors`.
- `tools/tests/test_l2_inventory.py` now includes a bounded scan regression test.

Additional checks:

```powershell
python -m py_compile tools\l2_inventory.py tools\tests\test_l2_inventory.py
python tools\tests\test_l2_inventory.py
python tools\l2_inventory.py build --source drivers\file-inventory --db tmp-work\t273\fixture-l2-inventory-bounded.db --max-files 2 --max-text-bytes 204800 --json
python tools\l2_inventory.py stats --db tmp-work\t273\fixture-l2-inventory-bounded.db --json
python tools\l2_inventory.py query --db tmp-work\t273\fixture-l2-inventory-bounded.db inventory --limit 5 --json
```

Bounded build result summary:

```text
max_files: 2
limit_hit: true
total_files: 2
text_indexed: 2
skipped_dirs: 1
skipped_symlink_or_reparse: 0
read_errors: 0
```

Updated verdict: **GO for next gated W_run only if source is explicit and the command includes `--max-files` plus DB under `tmp-work/t273/`**.

Recommended real-source template:

```powershell
python tools\l2_inventory.py build --source "<STEFAN_APPROVED_FOLDER>" --db tmp-work\t273\real-l2-inventory.db --max-files 100 --max-text-bytes 204800 --json
python tools\l2_inventory.py stats --db tmp-work\t273\real-l2-inventory.db --json
python tools\l2_inventory.py query --db tmp-work\t273\real-l2-inventory.db "<safe-term>" --limit 5 --json
```