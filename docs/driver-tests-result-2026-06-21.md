# Driver tests result

Дата: 2026-06-21

Источник: `queues/inbox/2026-06-21-driver-acceptance-output.txt`, присланный пользователем из Windows PowerShell.

Примечание: исходный `.txt` записан смешанной кодировкой: первая строка UTF-8, далее UTF-16LE chunks от PowerShell/Tee-Object. Для этого документа вывод декодирован и нормализован вручную.

Связано:

- `T-039`
- `T-048`
- `T-051`
- `T-055`
- `T-057`
- `T-059`
- `T-074`
- `docs/driver-acceptance-batch-2026-06-21.md`

## Summary

Batch B / driver tests пройден.

Пройденные группы:

- `files tests`;
- `repo-runner tests`;
- `workbench tests`;
- `workbench-db tests`;
- `file-inventory tests`.

Не найдено:

- `TIMEOUT`;
- traceback;
- явный fail.

В этом файле не было вывода Batch C (`pipeline ready_sorted no-write`), поэтому Batch C пока не считается закрытым.

## Decoded output

```text
Driver acceptance output 2026-06-21

===== files tests =====
TESTS OK files=5 hits=1
PASS: empty directory
PASS: basic inventory and kinds
PASS: hidden and common dirs skipped
PASS: hash and truncation
PASS: cli json

All tests passed!
===== repo-runner tests =====
PASS: empty repo
PASS: python repo
PASS: risk patterns
PASS: nonexistent path
PASS: max files and allowed root

All tests passed!
===== workbench tests =====
TESTS OK docs=6 audit=1 ingested=2
TESTS OK ingested=2 docs=2 risky=1 audit=1
TESTS OK hits=1 top=a.py
===== workbench-db tests =====
Workbench DB initialized: C:\Users\stefan\AppData\Local\Temp\tmpibtknj9o\test.db (schema v1)
PASS: init
Workbench DB initialized: C:\Users\stefan\AppData\Local\Temp\tmpwvz6_yj8\test.db (schema v1)
PASS: insert_and_search
Workbench DB initialized: C:\Users\stefan\AppData\Local\Temp\tmp7qsbf3g1\test.db (schema v1)
PASS: list_by_risk
Workbench DB initialized: C:\Users\stefan\AppData\Local\Temp\tmpkll05hds\test.db (schema v1)
PASS: audit_log
Workbench DB initialized: C:\Users\stefan\AppData\Local\Temp\tmpymvxy3w_\test.db (schema v1)
PASS: driver_stats

All tests passed!
===== file-inventory tests =====
TESTS OK files=2
```

## Interpretation

### T-048

`files` unit tests passed:

- `test_files.py`;
- `test_inventory.py`.

Remaining before full `T-048` acceptance:

- files MCP initialize/tools-list/call;
- `generate.py --check`, if still required by the task text.

### T-051

`repo-runner` inventory tests passed.

Remaining before full `T-051` acceptance:

- repo-runner MCP initialize/tools-list/repo_summary;
- `generate.py --check`, if still required by the task text.

### T-055

`workbench` tests and `workbench-db` tests passed at unit/integration level.

Remaining before full `T-055` acceptance:

- CLI `init/list/audit` with `WORKBENCH_BASE`;
- `generate.py --check`, if still required by the task text.

### T-057

`workbench` ingest/search tests passed at unit/integration level.

Remaining before full `T-057` acceptance:

- CLI `repo` and `dir`;
- checks with `WORKBENCH_BASE`, `INGEST_SOURCE_BASE`, `INGEST_MAX_FILES`;
- `generate.py --check`, if still required by the task text.

### T-059

`file-inventory` tests passed.

Remaining before full `T-059` acceptance:

- demo scan of current project or fixture report;
- final generator/check pass, if required.

## Next

Run Batch C from `docs/driver-acceptance-batch-2026-06-21.md`:

```powershell
Invoke-Timed "pipeline ready_sorted no-write" {
  param($repo)
  Set-Location -LiteralPath $repo
  python -c "import tools.pipeline as p; print([t['id'] for t in p.ready_sorted(p.collect_tasks())])"
} 30 @($repo)

Invoke-Timed "pipeline status" {
  param($repo)
  Set-Location -LiteralPath $repo
  python tools\pipeline.py status
} 30 @($repo)
```

Expected:

- `ready_sorted` prints `[]`;
- `pipeline status` shows `T-020` as `doing without active claim`;
- `T-062`, `T-063`, `T-064` are `placeholder task`.

