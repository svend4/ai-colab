---
id: 2026-06-24-t241-top-conveyor-recover
type: implementation-report
status: historical
owner: codex
date: 2026-06-24
related: T-241, T-239, queues/outbox/2026-06-24-conveyor-recover-adoption-review.md, queues/outbox/2026-06-24-top-conveyor-recover-integration-review.md, queues/outbox/2026-06-24-top-conveyor-recover-ux-review.md
---

# T-241 — top-layer conveyor recover

Implemented a top-layer read-only wrapper for workflow conveyor recovery diagnostics.

## What changed

- Added `python tools/top.py conveyor-recover [--json] [--limit N]`.
- Added the `conveyor-recover` entry to `tools/top.py buttons` with `effect: read-only`.
- Added focused coverage in `tools/test_top.py` for:
  - button discoverability;
  - parser support;
  - wrapper command construction;
  - absence of conveyor mutators in the wrapper command.

## Behavior

For agents:

```powershell
python tools/top.py conveyor-recover --json --limit 2
```

This prints clean JSON directly from `tools/conveyor.py recover`, including `schema: conveyor_recover.v1` and `mutates: false`.

For humans:

```powershell
python tools/top.py conveyor-recover --limit 2
```

This prints a top-layer advisory header and the underlying recover diagnostics. The header explicitly states that no automatic `land`, `ship`, `dismiss`, `launch`, `tick`, or Git changes are made.

## Agent review applied

Cicero recommended a thin wrapper around `tools/conveyor.py recover`, separate from `top.py conveyor`, with JSON passthrough and no repair actions. Applied.

Nietzsche recommended human wording that makes read-only/no-Git/no-mutator boundaries visible before the findings. Applied in the text-mode header.

The UX report did not have front matter, so I did not rewrite it. It was still processed as workflow evidence and shipped through `tools/conveyor.py`.

## Applied instructions

- Followed `AGENTS.md`: agent reports are in `queues/outbox/`, no deletion of other messages, no accepted decisions made by Codex.
- Followed `PROTOCOL.md`: task was claimed and will be closed through `pipeline.py done` with this report.
- Kept T-241 low-risk and read-only at runtime: the new top command delegates only to `tools/conveyor.py recover`.
- Applied Cicero and Nietzsche reports before closing the task.
- Did not run Git mutating commands and did not create a commit.

Checks:

```
python -m py_compile tools\top.py tools\test_top.py -> OK
python tools\test_top.py -> OK
python tools\top.py buttons --json -> OK, includes conveyor-recover effect read-only
python tools\top.py conveyor-recover --json --limit 2 -> OK, clean JSON, mutates false
python tools\top.py conveyor-recover --limit 2 -> OK, read-only advisory header
python tools\instructions.py check-report queues\outbox\2026-06-24-top-conveyor-recover-integration-review.md -> OK, advisory only
python tools\instructions.py check-report queues\outbox\2026-06-24-top-conveyor-recover-ux-review.md -> OK, advisory only
python tools\result_intake.py classify queues\outbox\2026-06-24-top-conveyor-recover-integration-review.md --json -> OK, build-change high confidence
python tools\result_intake.py classify queues\outbox\2026-06-24-top-conveyor-recover-ux-review.md --json -> OK, docs-change medium confidence
python tools\conveyor.py land W-2026-06-24-cicero-top-recover-review --output queues\outbox\2026-06-24-top-conveyor-recover-integration-review.md -> OK
python tools\conveyor.py ship W-2026-06-24-cicero-top-recover-review -> OK
python tools\conveyor.py land W-2026-06-24-nietzsche-top-recover-ux --output queues\outbox\2026-06-24-top-conveyor-recover-ux-review.md -> OK
python tools\conveyor.py ship W-2026-06-24-nietzsche-top-recover-ux -> OK
```

## Next recommended work

Now that `conveyor-recover` is available in the top layer, the next practical improvement is a sandbox cleanup/revision task for the high-risk result reported by `python tools/sandbox_intake_chain.py sandbox --text`: resolve historical markdown-link errors or move obsolete sandbox references into a clearly archived lane.