# T-223 id collision during pipeline reconciliation

Codex detected an id collision while doing a small reconciliation cleanup.

## What happened

`tools/next_id.py task` returned `T-223` for Codex cleanup work, but another concurrent stream also materialized `tasks/T-223.md` for a different task: `Enforce D-Cards and Layers`.

Codex must not overwrite the other stream's `T-223`. The cleanup work was moved away from `T-223`; after a second collision at `T-226`, the final cleanup report became task-neutral.

## Cleanup applied

- Removed the wrong Codex-created the wrong T-223 done marker, because it described the reconciliation cleanup and did not match the actual `tasks/T-223.md` content.
- Removed the wrong the wrong T-223 cleanup report report.
- Kept `tasks/T-223.md` untouched.
- Moved the reconciliation cleanup away from `T-223`; later `T-226` also collided, so the final cleanup report is task-neutral.

## Recommendation

This is fresh evidence for stronger next-id fencing in parallel mode. A generated placeholder id should be claimed or filled atomically, or agents should use per-stream task namespaces until merge-gate adoption.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; docs/stale-work-cleanup-policy-2026-06-21.md; docs/state-reconciliation-layer.md.

Checks:
- python tools/instructions.py check-report queues/outbox/2026-06-24-t223-id-collision.md -> OK after report evidence update
- python tools/pipeline.py status -> OK; T-223 remains assigned to antigravity and T-226 records Codex cleanup

