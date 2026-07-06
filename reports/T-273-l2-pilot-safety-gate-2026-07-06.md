---
id: T-273-l2-pilot-safety-gate-2026-07-06
type: report
title: "T-273 L2 pilot — W_safety / GATE preflight"
status: proposed
date: 2026-07-06
author: codex
related:
  - T-273
  - PKG-20260706-pilot-t273
  - D-014
  - D-015
  - D-018
  - D-035
---

# T-273 L2 pilot — W_safety / GATE preflight

## 1. Verdict

Status: **GO for read-only route planning and fixture/local-folder inventory only**.

Status: **NO-GO for external execution, external clone/fetch, install/build/test scripts, and any write to real user data**.

This report does not claim `T-273`, does not switch `PKG-20260706-pilot-t273` to `in-swarm`, and does not choose a real private user folder. It closes only the first safety/route gate for the package draft.

## 2. Current package state

- Package: `kotel/packages/PKG-20260706-pilot-t273.md`.
- Status: `draft`.
- Lead: `pending`.
- Risk: `medium`.
- Recommended first route: `files` / `file-inventory`.
- First payload class: small fixture or Stefan-approved local folder.

## 3. Commands checked

### 3.1. file-inventory help

```powershell
python drivers\file-inventory\inventory.py --help
```

Result: OK, exit 0. Supports:

```text
path
--base BASE
--max-files MAX_FILES
--include-hidden
--hash
--max-hash-bytes MAX_HASH_BYTES
--markdown
```

### 3.2. files inventory help

```powershell
python drivers\files\inventory.py --help
```

Result: OK, exit 0. Supports:

```text
path
--max-files MAX_FILES
--include-hidden
--hash
--max-hash-bytes MAX_HASH_BYTES
```

### 3.3. sqlite help

```powershell
python drivers\sqlite\sqlite_driver.py --help
```

Result: help text printed, exit 1. This CLI uses commandless invocation as usage output. Not a pilot blocker, but scripts should not treat `--help` exit code as green for sqlite until normalized.

### 3.4. git-log help

```powershell
python drivers\git-log\git_log.py --help
```

Result: help text printed, exit 1. Same note: usable CLI, but commandless help has non-zero exit.

## 4. Read-only smoke checks

### 4.1. file-inventory markdown smoke

Command:

```powershell
python drivers\file-inventory\inventory.py drivers\file-inventory --max-files 20 --markdown
```

Result: OK. Summary:

```text
Path: drivers/file-inventory
Files: 4
Truncated: False
Files found: fixture-report.json, inventory.py, README.md, test_inventory.py
```

### 4.2. files inventory JSON smoke

Command:

```powershell
python drivers\files\inventory.py drivers\file-inventory --max-files 20
```

Result: OK. Summary:

```text
total_files: 4
total_dirs: 0
total_size_mb: 0.071
extensions: .json=1, .py=2, .md=1
skipped_dirs: __pycache__
errors: 0
```

### 4.3. git-log summary smoke

Command:

```powershell
python drivers\git-log\git_log.py summary .
```

Result: OK. Summary:

```text
repo: New project ai colab
branch: master
total_commits: 420
last_commit: 25600ab docs(consensus): замкнутый контур — полный консенсус Claude+Codex, пилот T-273 ждёт слова Stefan
```

## 5. Driver route recommendation

### 5.1. First route

Use `file-inventory` or `files/inventory` first.

Reason:

1. read-only;
2. no external code execution;
3. small output can be bounded by `--max-files`;
4. works on a fixture/local folder;
5. current smoke passed.

### 5.2. Second route

Use `git-log` only if selected source is a git repository and the goal is metadata/history. `git log` does not run hooks, but still keep repo confined.

### 5.3. Later route

Use `sqlite` only after a concrete local `.db/.sqlite/.sqlite3` path is selected. Queries must be read-only `SELECT`/`WITH` only.

### 5.4. Avoid for first route

Avoid first:

- `data` for JSON/SQLite claims, because its manifest currently records interface drift; CSV/TSV only if used;
- `workbench`, because mode is safe-write;
- `gateway`, because it is a broad composition and may touch memory/workbench paths;
- `codex-local`, because it is a general manual bridge, not a narrow payload driver;
- `repo-runner` on repo URLs, because clone/network must stay out of first pilot.

## 6. Gates before W_build / W_run

Before package moves from `draft` to `in-swarm`:

1. assign `lead`: `claude`, `codex` or `claude+codex`;
2. choose source path: fixture or Stefan-approved local folder;
3. write exact command(s) into package or run report;
4. confirm no external clone/fetch/install/build/test;
5. run `python tools\validate.py`;
6. run `python tools\generate.py --check`;
7. if source is outside repo, confirm it is read-only and selected intentionally by Stefan;
8. if external source appears, use sandbox intake first;
9. if execute appears, stop: D-014 requires separate accepted run decision and human first-run gate.

## 7. Concrete safe next command candidates

Fixture route:

```powershell
python drivers\file-inventory\inventory.py drivers\file-inventory --max-files 20 --markdown
python drivers\files\inventory.py drivers\file-inventory --max-files 20
```

Stefan-approved folder route template:

```powershell
python drivers\file-inventory\inventory.py "<STEFAN_APPROVED_FOLDER>" --max-files 100 --markdown
python drivers\files\inventory.py "<STEFAN_APPROVED_FOLDER>" --max-files 100
```

Git metadata route template:

```powershell
python drivers\git-log\git_log.py summary "<STEFAN_APPROVED_REPO_FOLDER>"
```

## 8. Next decision

Recommended next package decision:

```text
Keep package status draft until lead/source/commands are filled.
Then run read-only W_build only on fixture or Stefan-approved local folder.
Do not use external repo execution in this pilot.
```
