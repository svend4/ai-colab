---
id: 2026-06-24-codex-agent-workflow-loop
type: report
agent: codex
status: proposed
workflow_id: W-2026-06-24-lagrange-centralization
related: docs/workflow-conveyor-policy.md, docs/top-layer-throughput-methodology.md, tools/flow.py, tools/conveyor.py
---
# Agent workflow loop — Codex orchestration note

## Purpose

This note turns the user request into a repeatable workflow loop instead of a one-off chat instruction.

The intended loop is:

```text
1. Codex/orchestrator formulates a bounded task.
2. Sub-agent receives the task with scope, allowed writes, expected report, and checks.
3. Workflow is registered in `tools/conveyor.py` as in-flight.
4. Sub-agent writes or returns an outbox report.
5. Codex lands the result with `conveyor.py land <workflow-id> --output <path>`.
6. Codex verifies the report: instructions evidence, links, checks, generated indexes, risks.
7. Codex synthesizes/apply/creates next task.
8. Codex ships or dismisses workflow and refills the conveyor.
```

This matches the existing repository policy in `docs/workflow-conveyor-policy.md` and `docs/top-layer-throughput-methodology.md`.

## Current launched workflow

- Workflow id: `W-2026-06-24-lagrange-centralization`
- Platform sub-agent id: `019ef962-96cf-7272-856c-631bc2b1fca1`
- Platform nickname returned by tool: `Poincare`
- Assigned repo role/name: `Lagrange`
- Kind: `read-only-report`
- State registered with: `python tools/conveyor.py launch W-2026-06-24-lagrange-centralization "lagrange centralization workflow plan" --kind read-only-report --depends none`
- Expected output path if the agent writes a file: `queues/outbox/2026-06-24-lagrange-centralization-information-plan.md`

## Task given to Lagrange

Lagrange must analyze centralization of information in this repo and produce a workflow-oriented plan.

Required output sections:

1. Current workflow loop: task setter, execution surface, report path, synthesizer, next-loop trigger.
2. One-task format for agents: task id, owner, scope, allowed writes, checks, expected report, handoff next.
3. Agent report format: what was done, files read/changed, checks, what to apply, what not to apply, next suggestions.
4. Codex application protocol: read, verify, synthesize, create/claim next task, optionally ask another agent.
5. Conflict prevention: disjoint write scopes, read-only exploration, outbox-only reports, no generated files unless main integrator.
6. Three-loop example: Lagrange analysis -> Codex implementation -> Lagrange review/next map.

## How Codex should process the result

When Lagrange returns:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-lagrange-centralization-information-plan.md
python tools\result_intake.py classify queues\outbox\2026-06-24-lagrange-centralization-information-plan.md --json
python tools\conveyor.py land W-2026-06-24-lagrange-centralization --output queues\outbox\2026-06-24-lagrange-centralization-information-plan.md
```

Then Codex should synthesize:

- consensus with existing `docs/workflow-conveyor-policy.md` and `docs/top-layer-throughput-methodology.md`;
- divergences as proposed follow-up tasks, not hidden edits;
- implementation candidates with separate write scopes.

After application:

```powershell
python tools\conveyor.py ship W-2026-06-24-lagrange-centralization
python tools\conveyor.py status --json
```

## Suggested next workflow queue

These are good parallel follow-ups with non-overlapping write scopes:

| Workflow | Owner | Scope | Output |
|---|---|---|---|
| `W-backlog-scan` | Lagrange/reviewer | read-only documentation, task, question, and outbox surfaces | ranked launchable backlog |
| `W-command-surface` | Codex/worker | `docs/top-layer-command-groups.md`, maybe `tools/top.py` | fewer commands, better grouped buttons |
| `W-result-contract` | reviewer | `queues/outbox`, `tools/result_intake.py` docs | stricter report schema |
| `W-sandbox-intake-chain` | worker | `tools/sandbox.py`, sandbox validators | one read-only intake chain |
| `W-synthesis-gate` | conductor | documentation, streams, and synthesis tools only | consensus/disagreement gate |

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: this is an outbox note, not a silent rewrite of mainline decisions.
- `docs/workflow-conveyor-policy.md`: used launch/land/ship conveyor model and non-zero in-flight principle.
- `docs/top-layer-throughput-methodology.md`: used SENSE -> INTAKE -> TRIAGE -> VERIFY -> SYNTHESIZE -> DECIDE -> COMMIT -> FEEDBACK loop.
- Safety: Lagrange task was scoped as read-only/low-conflict; only optional write is one outbox report.
- Checks:
  - `python tools\flow.py launch-plan lagrange T-237 "read-only centralization workflow review; do not edit code; write outbox report only" --json` -> OK
  - `python tools\top.py conveyor --json` -> showed target 2, in-flight 0 before launch, REFILL/IDLE actions
  - `python tools\conveyor.py launch W-2026-06-24-lagrange-centralization "lagrange centralization workflow plan" --kind read-only-report --depends none` -> OK