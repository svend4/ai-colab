# T-226 id collision during pipeline reconciliation

Codex detected a second id collision while reconciling the pipeline state.

## What happened

After `T-223` collided with another stream, Codex moved the reconciliation cleanup to `T-226`. A concurrent stream then materialized `tasks/T-226.md` for a different task: `Metadata Soft-Check`, owned/executed by antigravity.

Codex must not overwrite that stream's `T-226`. The reconciliation cleanup is therefore recorded in a task-neutral report: `queues/outbox/2026-06-24-pipeline-reconciliation-cleanup-report.md`.

## Cleanup applied

- Kept `tasks/T-226.md` and `queues/done/T-226.done.md` as antigravity's metadata soft-check work.
- Removed/superseded the misleading Codex cleanup report that used the `T-226` suffix.
- Left the actual reconciliation changes in their real source files: `tasks/T-194.md`, `tasks/T-202.md`, `queues/done/T-194.done.md`, and `docs/pipeline-reconciliation-current-blockers-2026-06-24.md`.

## Recommendation

The current `tools/next_id.py` flow is not safe enough for high-concurrency task creation. A future fix should either atomically reserve+fill+claim a task id, or allocate per-stream task namespaces and merge them through an adoption gate.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; docs/stale-work-cleanup-policy-2026-06-21.md; docs/state-reconciliation-layer.md; docs/instruction-assurance.md; Checks.

Checks:
- python tools/instructions.py check-report queues/outbox/2026-06-24-t226-id-collision.md -> OK after report evidence update
- python tools/pipeline.py status -> OK after final synchronization