---
id: 2026-06-24-t242-kotel-cli-help-guard
type: implementation-report
status: proposed
owner: codex
date: 2026-06-24
related: T-242, topics/kotel-system-critique-2026-06-24.md, topics/kotel-system-critique-2026-06-24-action-plan.md
---

# T-242 — Kotel critique stage 1

Implemented the first practical stage after `topics/kotel-system-critique-2026-06-24.md`: safe CLI probing for the first criticized tools plus a staged action plan.

## What changed

- Added/used `tools/_cli.py` as the shared minimal CLI helper:
  - `help_guard(doc, argv)` for safe `--help` / `-h` with exit 0;
  - `die(msg, code)` for stderr-only errors.
- Applied `help_guard()` to:
  - `tools/conveyor.py`;
  - `tools/dispatch.py`;
  - `tools/reconcile_state.py`.
- Converted their second descriptive blocks into `HELP` so `--help` prints useful CLI instructions, not only the D-card.
- Updated `tools/test_cli.py` to verify real tool help behavior.
- Added `topics/kotel-system-critique-2026-06-24-action-plan.md` with the ordered technical plan.

## Verified symptom before fix

Before the fix:

- `python tools/conveyor.py --help` returned a nonzero result and printed only the D-card.
- `python tools/dispatch.py --help` ran the normal dispatcher output instead of help.
- `python tools/reconcile_state.py --help` ran the default report path and wrote reconcile reports into `queues/outbox/`.

Those accidental reconcile reports were not deleted. They are evidence of the bug described by the critique: help probing could mutate repository state.

## Current behavior after fix

- `python tools/conveyor.py --help` exits 0 and prints conveyor CLI usage.
- `python tools/dispatch.py --help` exits 0 and prints dispatcher CLI usage.
- `python tools/reconcile_state.py --help` exits 0 and prints reconciliation CLI usage.
- `tools/test_cli.py` checks that those help calls do not modify `queues/outbox/`.

## Ordered recommendations

1. Stage A — safe help probing: complete for the first three criticized tools.
2. Stage B — CLI inventory: list raw `sys.argv` tools, tools with `help_guard`, and tools requiring `argparse`.
3. Stage C — JSON purity: smoke-test JSON commands so stdout stays machine-clean.
4. Stage D — deterministic protocol layer: add machine-readable blocked/escalation/report fields instead of relying only on intuition.
5. Stage E — queue state index: keep `queues/outbox/` as evidence, but add processed/unprocessed/shipped state over it.
6. Stage F — split the critique into several small proposed/accepted decisions instead of accepting one mixed mega-document.

## Applied instructions

- Used `cauldron-synthesis`: did not delete disagreements and did not rewrite the original critique document.
- Ran `tools/synthesis_helper.py` as instructed by the skill; it found no formal multi-variant topic for this critique, so a separate action-plan document was created.
- Followed `AGENTS.md`: wrote a separate report in `queues/outbox/`, did not delete other agents' material, did not mark decisions accepted.
- Followed `PROTOCOL.md`: T-242 was claimed through pipeline and will be closed through `pipeline.py done`.
- File edits were limited to the first-stage CLI guard and tests.

Checks:

```
python tools\synthesis_helper.py topics --json -> OK
python tools\synthesis_helper.py report kotel-system-critique-2026-06-24 -> expected: no formal variants found
python -m py_compile tools\_cli.py tools\test_cli.py tools\conveyor.py tools\dispatch.py tools\reconcile_state.py -> OK
python tools\conveyor.py --help -> OK, exit 0, useful CLI text
python tools\dispatch.py --help -> OK, exit 0, useful CLI text
python tools\reconcile_state.py --help -> OK, exit 0, useful CLI text
python tools\test_cli.py -> OK
python tools\test_conveyor.py -> OK
python tools\test_dispatch.py -> OK
python tools\test_reconcile_state.py -> OK
python tools\test_reconcile_fix.py -> OK
```

## Next task proposal

Create the next task for CLI inventory and JSON purity:

- scan tools for raw `sys.argv` entrypoints;
- classify them as `argparse`, `help_guard`, `manual-help`, or `unsafe`;
- produce a machine-readable report;
- start with read-only inventory before changing more tools.