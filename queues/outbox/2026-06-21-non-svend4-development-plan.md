---
status: historical
---
# Outbox: non-svend4 development plan

Date: 2026-06-21

Author: Codex

Task: `T-086`

## Result

Created a practical continuation plan excluding `svend4`.

New pool tasks:

- `T-087`: synchronous MCP stdio probe / workaround;
- `T-088`: gateway audit/tools/status cleanup;
- `T-089`: files driver shared redaction + tools manifest;
- `T-090`: driver status reconciliation (`draft`/`ready`);
- `T-091`: placeholder and stale-work cleanup.

Opinion: the next development phase should focus on trust and operability, not more architecture. The main technical risks are MCP stdio acceptance and driver status truthfulness.

