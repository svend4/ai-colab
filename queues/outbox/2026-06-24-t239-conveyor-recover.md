---
id: 2026-06-24-t239-conveyor-recover
type: implementation-report
status: done
owner: codex
date: 2026-06-24
related:
  - tasks/T-239.md
  - tools/conveyor.py
  - tools/test_conveyor.py
  - queues/outbox/2026-06-24-agent-cell-synthesis.md
  - queues/outbox/2026-06-24-unused-advice-audit.md
---

# T-239 conveyor recover advisory

## Summary

Implemented a read-only `recover` command for `tools/conveyor.py`. It diagnoses reset, hang, missing output, stale heartbeat, UI mismatch, and outbox/conveyor drift without mutating the conveyor ledger.

The command is intentionally advisory-only. It prints findings and suggested commands, but it does not automatically run `land`, `ship`, `dismiss`, `tick`, or agent launch operations.

## Changes

- Added `recover(...)` and `render_recover(...)` to `tools/conveyor.py`.
- Added CLI support: `python tools\conveyor.py recover [--json] [--limit N]`.
- Extended `tools/test_conveyor.py` with recovery diagnostics coverage.
- Created task source `tasks/T-239.md`.

## What Recover Detects

- `landed-without-output`: landed workflow has no machine-readable output path.
- `missing-output-path`: landed workflow references an output file that does not exist.
- `stale-heartbeat`: orchestrator heartbeat is older than the configured idle threshold.
- `refill-deficit`: in-flight count is below target.
- `unreferenced-outbox-reports`: outbox reports that are not referenced by workflow outputs.

## Why This Matters

Recent workflow failures were not code failures. They were orchestration-state failures: UI indicators disappeared, agent sessions completed without visible status, and durable output had to be reconciled manually.

`recover` makes that reconciliation visible and repeatable.

## Checks

Checks:

```powershell
python -m py_compile tools\conveyor.py tools\test_conveyor.py
python tools\test_conveyor.py
python tools\conveyor.py recover --json --limit 5
python tools\conveyor.py recover --limit 3
python tools\instructions.py check-report queues\outbox\2026-06-24-t239-conveyor-recover.md
python tools\validate.py
python tools\generate.py --check
```

Results before task close:

- py_compile: OK.
- `tools/test_conveyor.py`: OK.
- `conveyor.py recover --json`: OK, returned `conveyor_recover.v1` and `mutates: false`.
- `conveyor.py recover --limit 3`: OK, printed text diagnostics.

## Applied instructions

Applied instructions evidence:

AGENTS.md and PROTOCOL.md were followed. The implementation was done through a claimed task, no agent report was overwritten, no accepted decision was changed, and no execute mode was enabled.