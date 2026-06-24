---
id: 2026-06-24-conveyor-recover-adoption-review
type: workflow-review
status: proposed
agent: codex
created: 2026-06-24
related:
  - queues/outbox/2026-06-24-t239-conveyor-recover.md
  - queues/outbox/2026-06-24-unused-advice-audit.md
  - docs/top-layer-command-groups.md
  - docs/friction-playbook.md
  - docs/workflow-conveyor-policy.md
  - tools/top.py
  - tools/advice.py
  - tools/friction.py
  - tools/conveyor.py
  - AGENTS.md
  - PROTOCOL.md
---

# Conveyor recover adoption review

## Summary

`tools/conveyor.py recover` should be activated in the top layer, but only as a read-only advisory diagnostic. It should not automatically run `land`, `ship`, `dismiss`, `tick`, `launch`, or any Git operation.

The command exists because the recent failures were orchestration-state failures: reset, hang, missing output, stale heartbeat, UI indicator mismatch, and outbox/conveyor drift. These failures need a visible recovery checklist before the next workflow loop, but they do not justify automatic repair yet.

Best current direction: expose recover as a top-layer button and friction/advice recommendation, while keeping the actual state-changing commands explicit and human/Codex-reviewed.

## Current activation paths

Existing direct command:

```powershell
python tools\conveyor.py recover --json --limit 5
python tools\conveyor.py recover --limit 3
```

Existing top-layer path:

```powershell
python tools\top.py conveyor --json
python tools\top.py process-landed --json
```

Current limitation: `tools/top.py conveyor` calls `tools/conveyor.py status`, not `recover`. It can show REFILL/PROCESS/IDLE state, but it does not yet expose reset/hang/UI-mismatch diagnostics as a first-class top-layer action.

Existing advice/friction path:

```powershell
python tools\top.py advice codex --parallel --hot-files
python tools\top.py friction
python tools\friction.py recipe F-003
python tools\friction.py recipe F-014
```

`tools/friction.py` already has relevant archetypes:

- `F-003` for shell/Python runtime hangs;
- `F-014` for too many separate commands and the need for top-level buttons.

However, there is no dedicated friction recipe for conveyor reset/recover yet. `queues/outbox/2026-06-24-unused-advice-audit.md` already identified this as an unused-advice activation gap.

Existing policy path:

- `docs/workflow-conveyor-policy.md` defines the conveyor as a flow, not a batch, and says the supervisor should signal REFILL/PROCESS/IDLE.
- The same policy says the supervisor observes and signals; launching and state-changing decisions stay with the orchestrator.
- `docs/top-layer-command-groups.md` says the top layer should group repeated commands as buttons while preserving safety boundaries.
- `docs/friction-playbook.md` says repeated manual problems should first become read-only detectors, then only later become automation if the recipe is stable.

## Should recover be a top.py button now

Yes, but narrowly.

Recommended shape:

```powershell
python tools\top.py conveyor-recover --json
python tools\top.py conveyor-recover --limit 5
```

The top command should be a thin wrapper around:

```powershell
python tools\conveyor.py recover --json --limit 5
```

It should also appear in:

- `tools/top.py buttons`;
- `docs/top-layer-command-groups.md`;
- `tools/advice.py` when conveyor/friction symptoms indicate reset, stale heartbeat, missing output, or UI mismatch;
- `docs/friction-playbook.md` as the first command under a new "if workflow indicator/reset mismatch happens" recipe.

Do not make `top.py conveyor` silently run recover every time yet. That would blur the current difference between routine status and recovery audit. For now, keep:

- `top.py conveyor` = normal supervisor status;
- `top.py conveyor-recover` = explicit recovery diagnostic after reset/hang/UI mismatch.

This keeps the top layer ergonomic without making every normal conveyor check heavier or noisier.

## Risks of too much automation

Automatic recovery can corrupt the meaning of the workflow ledger if it starts mutating state from weak evidence.

Specific risks:

- A missing UI indicator does not prove the agent is dead.
- A missing output file does not prove the workflow failed; the output can arrive later.
- Auto-`dismiss` could discard useful late results.
- Auto-`land` could attach the wrong outbox file to the wrong workflow.
- Auto-`ship` could mark unreviewed results as processed.
- Auto-`tick` could hide a real stale-orchestrator problem.
- Auto-launch on every deficit could overfill the top layer while Codex is already the bottleneck.

Therefore `recover` should remain advisory. It should print findings, suggested commands, and evidence paths. Codex or a human should then choose whether to run `land`, `ship`, `dismiss`, `tick`, or launch another workflow.

## One recommended next action

Create one small build task:

```text
Add a read-only top-layer wrapper for conveyor recovery.
```

Scope:

- add `conveyor-recover` subcommand to `tools/top.py`;
- add one button entry to `tools/top.py buttons`;
- add a short section to `docs/top-layer-command-groups.md`;
- add one friction recipe or advice activation path for conveyor reset/hang/UI mismatch;
- keep all behavior read-only/advisory;
- do not auto-run `land`, `ship`, `dismiss`, `tick`, `launch`, `generate`, or Git.

Acceptance checks:

```powershell
python tools\top.py conveyor-recover --json
python tools\top.py conveyor-recover --limit 3
python tools\top.py buttons --json
python tools\friction.py list
python tools\validate.py
python tools\generate.py --check
```

## Exact checks

Checks:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-conveyor-recover-adoption-review.md
python tools\result_intake.py classify queues\outbox\2026-06-24-conveyor-recover-adoption-review.md --json
python tools\validate.py
python tools\generate.py --check
```

Additional manual verification targets for the future build task:

```powershell
python tools\conveyor.py recover --json --limit 5
python tools\top.py conveyor --json
python tools\top.py process-landed --json
python tools\top.py advice codex --parallel --hot-files
python tools\friction.py recipe F-003
python tools\friction.py recipe F-014
```

## Applied instructions

Applied instructions evidence:

- `AGENTS.md` says all agents must work by `PROTOCOL.md`, must not delete other messages, must not rewrite discussion history, and should use `queues/outbox/` for automatic work results. This review writes only `queues/outbox/2026-06-24-conveyor-recover-adoption-review.md` and does not edit code, generated files, logs, tasks, or Git.
- `PROTOCOL.md` defines `queues/outbox/` as the place for prepared agent results that have not yet been moved into main files. This report is `status: proposed`; it does not change an accepted decision.
- `PROTOCOL.md` says the main agent or human should move important content from outbox into canonical files. This report therefore recommends a later build task instead of directly editing `tools/top.py`, `docs/top-layer-command-groups.md`, `tools/advice.py`, or `tools/friction.py`.
- `docs/workflow-conveyor-policy.md` separates observe/signal from launch/mutation. This report keeps `recover` advisory-only and rejects automatic state mutation.
- `docs/friction-playbook.md` says repeated manual problems should first become read-only detectors and only later become automation. This report follows that ladder: first top-layer visibility, later mutation only if evidence stabilizes.

Checks:

- Read targets reviewed: `queues/outbox/2026-06-24-t239-conveyor-recover.md`, `queues/outbox/2026-06-24-unused-advice-audit.md`, `docs/top-layer-command-groups.md`, `docs/friction-playbook.md`, `docs/workflow-conveyor-policy.md`, `tools/top.py`, `tools/advice.py`, `tools/friction.py`, `tools/conveyor.py`, `AGENTS.md`, `PROTOCOL.md`.
- No code, task, index, pipeline, log, generated, or Git write was intentionally made for this review.
