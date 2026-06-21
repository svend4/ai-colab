# Non-svend4 development plan

Date: 2026-06-21

Author: Codex

Related:

- `T-086`
- `T-087`
- `T-088`
- `T-089`
- `T-090`
- `T-091`
- `T-078`
- `T-081`

## Current State

The project has reached a useful read-only/local prototype stage.

Already done:

- project runtime is working;
- core validation/generation is green;
- workbench acceptance is done;
- ingest acceptance is done;
- file-inventory acceptance is done;
- pipeline claim/fencing hardening is done;
- audit helper and data redaction are done;
- manifest/tool validation exists for several MCP drivers;
- front-matter parser copies were consolidated by Claude in `T-085`.

Current blockers:

- `T-048`: files MCP acceptance is blocked by Windows/Python asyncio pipe permissions.
- `T-051`: repo-runner MCP acceptance is blocked by the same MCP stdio issue.
- `T-020`: svend4 remains outside this plan by user request.
- `T-062..T-064`: placeholders remain as reserved tasks and are intentionally not issued by pipeline.

## What Is Still Not Done

1. MCP stdio acceptance path: engines work, but MCP stdio acceptance is not reliable in this environment.
2. Driver governance: `draft` vs `ready` needs a truthful evidence matrix.
3. Gateway cleanup: audit, `tools:` manifest field, and status policy remain open.
4. Files driver cleanup: migrate historical redaction copy to `drivers/redaction.py`.
5. Placeholder/stale-work cleanup: `T-062..T-064` and stale work need a clear append-only policy.

## Recommended Order

1. `T-090`: reconcile driver statuses first, because it affects planning and trust.
2. `T-089`: migrate files redaction and add tools metadata, low risk.
3. `T-088`: clean gateway metadata/audit without claiming MCP acceptance.
4. `T-087`: implement sync MCP probe or document external acceptance route.
5. `T-091`: clean placeholders and stale-work policy after technical state is stable.

## What Not To Do Yet

- Do not start a web UI yet.
- Do not add more L3/L6/RAG architecture until there is a real corpus workflow.
- Do not mark MCP-dependent tasks done until an actual MCP acceptance path is green.
- Do not expand into code execution/sandbox mode until isolation exists.

