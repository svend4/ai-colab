# Pipeline reconciliation cleanup — task-neutral report

Codex performed a small pipeline reconciliation cleanup after checking the ready/not-ready state. This report is intentionally task-neutral because two numeric ids (`T-223`, then `T-226`) were concurrently materialized by other streams while the cleanup was in progress.

## Changes

- `T-194` was closed as retired placeholder: it was an empty reservation without real work.
- `queues/done/T-194.done.md` was added as the done marker for that retired placeholder.
- `T-202` was moved from stale `doing` to explicit `blocked`: the old selective-add commit scope is unsafe in a dirty multi-agent tree.
- Added `docs/pipeline-reconciliation-current-blockers-2026-06-24.md`.
- Recorded id-collision evidence in `queues/outbox/2026-06-24-t223-id-collision.md` and `queues/outbox/2026-06-24-t226-id-collision.md`.

## What was not changed

- `T-020` remains blocked: external source is still needed.
- `T-174` remains blocked: async stdio runtime gap is not fixed.
- `T-208` remains blocked: execute-runner remains human/governance gated.
- `tasks/T-223.md` and `tasks/T-226.md` belong to other streams and were not overwritten after the collisions were detected.
- `queues/claimed/T-202.claim.md` was not deleted; it is a stale foreign claim trace and should be handled only by an explicit claim cleanup policy/integrator.

## Methodological note

This is a concrete example of why the project needs atomic next-id/claim or per-stream task namespaces. The cleanup itself was valid, but the task-id carrier was not stable under parallel agent writes.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; docs/stale-work-cleanup-policy-2026-06-21.md; docs/state-reconciliation-layer.md; docs/instruction-assurance.md; tasks/T-194.md; tasks/T-202.md; queues/done/T-194.done.md; Checks.

Checks:
- python tools/generate.py -> OK after each synchronization pass
- python tools/pipeline.py snapshot -> OK after each synchronization pass
- python tools/validate.py -> OK
- python tools/generate.py --check -> OK after final synchronization
- python tools/drift_check.py -> OK after final synchronization
- python tools/instructions.py check-report queues/outbox/2026-06-24-pipeline-reconciliation-cleanup-report.md -> OK after report evidence update