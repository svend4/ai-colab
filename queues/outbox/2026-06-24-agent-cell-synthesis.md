---
id: 2026-06-24-agent-cell-synthesis
type: synthesis-report
status: historical
owner: codex
date: 2026-06-24
mode: read-only-outbox-only
related: 
---

# Agent cell synthesis

## 1. Summary

This report synthesizes one completed 3-worker cell:

- `queues/outbox/2026-06-24-observer-hierarchy-methodology.md`
- `queues/outbox/2026-06-24-sandbox-intake-chain-map.md`
- `queues/outbox/2026-06-24-unused-advice-audit.md`

The three reports are compatible. They all point to the same control-plane bottleneck: the project can launch more agents than Codex can safely intake, verify, synthesize, route, and apply. Scaling should therefore improve the upper layer before increasing the worker fleet.

Recommended next Codex action: add a read-only/advisory conveyor recovery task for reset, hang, UI indicator mismatch, missing output, and in-flight workflow reconciliation. This should be implemented before larger fan-out because it protects the agent workflow itself.

This report does not accept governance decisions, does not enable execute, and does not promote sandbox or draft code.

## 2. Compared reports

`queues/outbox/2026-06-24-observer-hierarchy-methodology.md` defines the agent hierarchy: workers gather scoped evidence, observers synthesize, Codex integrates, and the human approves governance or risky decisions. It recommends 2-4 read-only/outbox workflows by default, one shared-tree build writer, and optional 3 workers + 1 observer cells.

`queues/outbox/2026-06-24-sandbox-intake-chain-map.md` maps the current sandbox intake chain after T-235 through T-238. It proposes a unified read-only intake result that combines inventory, Python AST/static scan, manifest validation, Markdown link checking, draft-code review, and a route recommendation without execute.

`queues/outbox/2026-06-24-unused-advice-audit.md` audits useful advice that exists but is not fully activated. It identifies the strongest next activation candidates: conveyor recovery, friction next action, instruction evidence hardening, draft-code sandbox advice, and observer-cell synthesis.

Supporting context:

- `queues/outbox/2026-06-24-codex-agent-hierarchy-operating-model.md`
- `docs/workflow-conveyor-policy.md`
- `docs/top-layer-throughput-methodology.md`
- `AGENTS.md`
- `PROTOCOL.md`

## 3. Consensus

The reports agree on these points:

1. The real limit is upper-layer processing, not worker launch capacity.
2. Workers should write scoped outbox reports, not directly accept decisions.
3. Observers should reduce multiple reports into consensus, divergence, missing evidence, risks, and one proposed Codex action.
4. Codex should verify outputs with `tools/instructions.py check-report`, classify them with `tools/result_intake.py`, and only then apply or route work.
5. There should be only one shared-tree build writer at a time.
6. Sandbox and draft-code material must remain no-execute by default.
7. Reset, hang, UI mismatch, missing outputs, and stale in-flight workflows are now recurring operational problems, not isolated accidents.
8. Advice already exists in docs and tools, but some advice needs activation as commands, gates, templates, or standard workflow steps.
9. Future scale should use cells: 3 worker reports -> 1 observer synthesis -> Codex verification/application.
10. More agents should not be launched when landed outputs are unprocessed or when report evidence fails.

## 4. Divergence / tension

The main tension is priority:

- The sandbox report recommends a unified sandbox intake orchestrator as the next build task.
- The unused-advice report recommends conveyor recovery first because it fixes the immediate reset/hang failure mode.
- The hierarchy report recommends synthesis discipline first, then one chosen Codex action.

Resolution proposed here: do conveyor recovery first. The sandbox orchestrator is useful, but it depends on reliable workflow state. If agents finish work and the system loses or mislabels in-flight/landed state, more intake automation will still leave Codex with unclear operational state.

Second tension: automation depth.

- Sandbox intake wants a richer normalized JSON result.
- Advice activation wants small command groups and gates.
- Hierarchy wants human/Codex decision rights preserved.

Resolution proposed here: keep the next step read-only/advisory. The recovery command should diagnose and print exact next commands. It should not auto-land, auto-ship, auto-dismiss, commit, or enable execute.

## Консенсус

The consensus is that worker scale must be controlled by upper-layer throughput. The three reports are compatible on the need for scoped outbox outputs, observer synthesis, Codex verification, human-gated governance, no-execute sandbox handling, and one shared-tree build writer.

The strongest shared operational point is that agent-cell output should be converted into one compact synthesis before new build work begins. This report is that synthesis step for the current cell.

## Разногласия

The reports differ mainly on the next implementation priority. The sandbox report points to a sandbox intake orchestrator. The unused-advice audit points to conveyor recovery. The hierarchy report points to synthesis discipline and controlled scaling.

This synthesis recommends conveyor recovery first because it protects the workflow substrate used by all other agent-cell work. The sandbox orchestrator remains important, but it should wait behind the recovery layer.

## Двойная перепроверка

First check: compared the three worker reports against AGENTS.md, PROTOCOL.md, docs/workflow-conveyor-policy.md, and docs/top-layer-throughput-methodology.md.

Second check: verified that the recommendation stays advisory, does not accept governance, does not enable execute, and does not promote sandbox or draft code.
## 5. Missing evidence

Missing or incomplete evidence before stronger automation:

- No measured throughput data yet: average report verification time, synthesis time, landed wait time, or retry rate.
- No durable event log of reset/hang/recovery incidents.
- No automated grouping from three worker outputs to one observer synthesis.
- No strict schema for worker and observer reports beyond `check-report` conventions.
- No proof that result classification is stable; one worker already noted that methodology reports may be classified as `external-code` because of sandbox vocabulary.
- No final decision that `conveyor recover` should become an accepted command; this synthesis only proposes it.
- No execute sandbox approval, and none is implied.

## 6. Risk and safety gates

Safety gates to preserve:

- Keep recovery read-only/advisory until it has tests and repeated manual confirmation.
- Do not edit `TASKS.md`, `index.json`, `PIPELINE.md`, `logs`, generated files, or git from this synthesis report.
- Do not auto-dismiss workflows unless an explicit operator action chooses that path.
- Do not auto-land or auto-ship a workflow whose output file is missing.
- Do not execute sandbox, draft, or external code.
- Do not promote draft code into `tools/`, `drivers/`, `core/`, or `portals/` without a separate claimed task and tests.
- Do not turn proposed governance into accepted governance without the human or explicitly assigned collector.
- Do not increase conveyor target while landed outputs are waiting or evidence checks fail.

Minimum processing gate for each worker or observer output:

```powershell
python tools\instructions.py check-report <existing-report-path>
python tools\result_intake.py classify <existing-report-path> --json
```

## 7. Next Codex action

Choose exactly one next task: implement a read-only/advisory conveyor recovery workflow.

Concrete task shape:

- Update existing `tools/conveyor.py` with a future command named `recover`.
- The command should inspect current conveyor state, output paths, missing files, stale in-flight workflows, and landed workflows without output.
- It should print a recovery plan, not perform destructive actions.
- It should recommend one of: wait, check output, land with output, ship after synthesis, dismiss with reason, or relaunch with a duplicate guard.
- Add tests for no workflows, healthy in-flight, missing output, output exists but not landed, stale in-flight, and landed without output.
- Add one short outbox or docs report after implementation explaining the recovery contract.

Why this one first:

- It addresses the exact recent failure mode: reset/hang/UI indicator mismatch.
- It benefits all future agent cells, not only sandbox work.
- It activates already documented advice from `docs/workflow-conveyor-policy.md` and `docs/top-layer-throughput-methodology.md`.
- It reduces Codex cognitive load before increasing worker count.
- It is safer than execute-related work because it can remain read-only/advisory.

Future proposal label: conveyor recover advisory command. This is a future proposal, not an accepted governance decision.

## 8. Secondary backlog

These should wait until conveyor recovery is implemented or explicitly deprioritized:

1. Future proposal: sandbox intake chain orchestrator that emits one normalized no-execute result from inventory, schema, links, and Python AST checks.
2. Future proposal: observer-cell synthesis template/check that verifies consensus, divergence, missing evidence, risks, and one next action.
3. Future proposal: friction next action command that expands current friction warnings into a short task-specific checklist.
4. Future proposal: draft-code sandbox advice rule that suggests `sandbox/drafts/` when agents are asked for prototype code.
5. Future proposal: stricter applied-instructions gate for service/governance reports.

## 9. Checks

Exact commands for this synthesis and follow-up verification:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-agent-cell-synthesis.md
python tools\result_intake.py classify queues\outbox\2026-06-24-agent-cell-synthesis.md --json
python tools\conveyor.py status --json
python tools\validate.py
python tools\generate.py --check
```

Exact commands to process the three worker reports if not already landed or shipped by the main operator:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-observer-hierarchy-methodology.md
python tools\instructions.py check-report queues\outbox\2026-06-24-sandbox-intake-chain-map.md
python tools\instructions.py check-report queues\outbox\2026-06-24-unused-advice-audit.md
python tools\result_intake.py classify queues\outbox\2026-06-24-observer-hierarchy-methodology.md --json
python tools\result_intake.py classify queues\outbox\2026-06-24-sandbox-intake-chain-map.md --json
python tools\result_intake.py classify queues\outbox\2026-06-24-unused-advice-audit.md --json
```

## Applied instructions

AGENTS.md evidence:

- worked by `PROTOCOL.md`;
- did not delete other messages;
- did not rewrite history;
- did not change accepted decisions;
- wrote the automatic work result into `queues/outbox/`;
- kept this report as `status: proposed`;
- did not edit code, tasks, generated files, logs, or git.

PROTOCOL.md evidence:

- followed the queue model where `queues/outbox/` stores prepared agent results before integration into main files;
- used append-only collaboration by creating a new synthesis report instead of editing the three worker reports;
- treated the observer role as synthesis only, not final decision authority;
- preserved Git commit as a later integration step, not part of this read-only/outbox-only run;
- separated sandbox and draft-code evidence from execute or promotion.

Checks:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-agent-cell-synthesis.md
```
