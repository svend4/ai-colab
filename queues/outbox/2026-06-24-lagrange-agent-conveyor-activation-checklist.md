---
id: 2026-06-24-lagrange-agent-conveyor-activation-checklist
type: workflow-checklist
status: historical
owner: lagrange
mode: read-only/outbox-only
date: 2026-06-24
related: 
---

# Lagrange agent conveyor activation checklist

## Summary

This checklist turns the previous Lagrange workflow plan into an operational activation loop for keeping agents busy without colliding with Codex work. The useful operating rule is simple: keep a small read-only fleet active, process landed reports before expanding the fleet, and reserve build or generated-file writes for one integrator at a time.

The current Codex implementation lane is `tasks/T-237.md`, the sandbox Markdown link checker. The parallel tasks below are therefore scoped as outbox-only analysis, review, or synthesis. They must not write code, task sources, generated indexes, runtime logs, git state, or the sandbox link checker implementation.

## Conveyor operating rule

Default active fleet:

- Target 2-4 active read-only or outbox-only agent tasks.
- Target 1 active build task in the shared tree.
- Target 0 parallel writers on generated files.
- Target 0 execute-sandbox or external-code execution tasks unless a human-approved gate exists.

Refill rule:

1. Check whether there are landed outputs waiting for intake.
2. If landed outputs exist, process them before launching more agents.
3. If no landed outputs exist and active read-only tasks are below 2, launch one or two outbox-only agents.
4. If active read-only tasks are 2-4, do not expand unless the next task is clearly independent and Codex has intake bandwidth.
5. If reports are arriving faster than Codex can verify and synthesize them, lower the target and process first.

Stop rule:

- Stop refill when a proposed task needs the result of an unfinished task.
- Stop refill when the task would write to the same files as Codex.
- Stop refill when the task needs generated files or git.
- Stop refill when the report queue has unverified outputs.

## Task templates

### Analyst

Goal: map an area, find existing recommendations, and propose next actions.

Mode: read-only and outbox-only.

Allowed write: one new file in `queues/outbox/`.

Typical read targets: `docs/workflow-conveyor-policy.md`, `docs/top-layer-throughput-methodology.md`, `AGENTS.md`, `PROTOCOL.md`.

Report must include: summary, read evidence, findings, safe next tasks, forbidden overlaps, applied instructions, checks.

### Reviewer

Goal: inspect a completed report or proposed design for contradictions, missing evidence, and unsafe scopes.

Mode: read-only and outbox-only.

Allowed write: one new file in `queues/outbox/`.

Reviewer must not rewrite the source report. It should quote findings by section name and recommend apply, hold, or reject.

### Worker

Goal: implement one claimed build task.

Mode: claim-bound or worktree-bound. This checklist does not authorize worker writes.

Allowed write: only files listed by the Codex integrator for a claimed task.

Worker must not touch `TASKS.md`, `index.json`, `PIPELINE.md`, `logs`, git, or generated files unless the task explicitly says so.

### Synthesis-agent

Goal: combine two or more reports into consensus, near-consensus, divergence, and next tasks.

Mode: read-only and outbox-only unless Codex assigns an isolated stream.

Allowed write: one new file in `queues/outbox/`.

Synthesis-agent must not mark decisions accepted. It can propose consensus and list divergence.

## Safe write scopes and forbidden overlaps

Safe write scopes:

| Scope | Use | Condition |
|---|---|---|
| `queues/outbox/` | agent reports, reviews, synthesis notes | one new file per agent task |
| `topics/` | long discussion messages | only if Codex assigns a topic lane |
| `streams/` | alternative variants | only if Codex assigns a stream lane |

Forbidden overlaps for this loop:

- Do not write `TASKS.md`.
- Do not write `index.json`.
- Do not write `PIPELINE.md`.
- Do not write `logs`.
- Do not write git state.
- Do not edit `tasks/T-237.md`.
- Do not implement the sandbox link checker while Codex owns the T-237 lane.
- Do not change `tools/conveyor.py`, `tools/flow.py`, or `tools/top.py` from this checklist task.

## Land/ship protocol for agent reports

Land protocol:

1. Agent writes exactly one report file in `queues/outbox/`.
2. Report includes `## Applied instructions`.
3. Report includes a `Checks:` marker with exact runnable verification commands.
4. Codex verifies the report with `python tools\instructions.py check-report queues\outbox\2026-06-24-lagrange-agent-conveyor-activation-checklist.md` or the actual report file being processed.
5. Codex classifies the report as analysis, review, synthesis, build proposal, governance proposal, or external-code proposal.

Ship protocol:

1. If the report is analysis-only, Codex can keep it as evidence without changing generated files.
2. If the report proposes build work, Codex creates or claims a separate task before writing code.
3. If the report contains divergence, Codex routes it to synthesis before implementation.
4. If the report touches governance, Codex leaves it proposed unless the human maintainer approves.
5. If the report is accepted for implementation, Codex performs the implementation in a separate claimed build step.

## Next 5 parallel agent tasks

These tasks do not touch the current T-237 implementation lane.

| Task | Agent role | Objective | Allowed write | Verification |
|---|---|---|---|---|
| Conveyor backlog analyst | analyst | Find 10 safe outbox-only tasks from existing docs and reports | one new file in `queues/outbox/` | check-report on that file |
| Lagrange report reviewer | reviewer | Review the previous Lagrange centralization plan for missing activation commands | one new file in `queues/outbox/` | check-report on that file |
| Top-layer command auditor | analyst | Map which top-layer commands already support agent activation and which are only documented | one new file in `queues/outbox/` | check-report on that file |
| Consensus lane mapper | synthesis-agent | Group recent workflow reports into apply-now, hold-for-synthesis, and governance-proposed lanes | one new file in `queues/outbox/` | check-report on that file |
| External-code safety reviewer | reviewer | Review sandbox-related documentation for no-execute assumptions without changing sandbox code | one new file in `queues/outbox/` | check-report on that file |

Each task should use a unique new report filename chosen at launch time. Do not pre-create report names in this checklist.

## Checks

Exact commands to verify this report:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-lagrange-agent-conveyor-activation-checklist.md
git status --short -- queues\outbox\2026-06-24-lagrange-agent-conveyor-activation-checklist.md
```

Expected result:

- `check-report` reports applied-instructions evidence present.
- `git status` shows only this new outbox file for this checklist scope.

## Applied instructions

AGENTS.md evidence: this work writes an automatic-agent result to `queues/outbox/`, does not delete messages, does not rewrite history, does not change final decisions, and leaves governance as proposed.

PROTOCOL.md evidence: this follows the queue/outbox model, keeps one result in one file, avoids editing shared status and generated files, and leaves synthesis or implementation to a separate integrator step.

Read evidence:

- `AGENTS.md`
- `PROTOCOL.md`
- `docs/workflow-conveyor-policy.md`
- `docs/top-layer-throughput-methodology.md`
- `queues/outbox/2026-06-24-lagrange-centralization-information-plan.md`
- `queues/outbox/2026-06-24-codex-lagrange-intake.md`
- `tasks/T-237.md`

Checks:

- `python tools\instructions.py check-report queues\outbox\2026-06-24-lagrange-agent-conveyor-activation-checklist.md`
- `git status --short -- queues\outbox\2026-06-24-lagrange-agent-conveyor-activation-checklist.md`

Low-conflict note: this checklist did not run `generate.py`, did not run `pipeline.py snapshot`, did not write code, did not edit generated files, did not write logs, and did not use git.
