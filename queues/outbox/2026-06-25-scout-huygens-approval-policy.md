---
id: outbox-2026-06-25-scout-huygens-approval-policy
type: subagent-report
status: proposed
from: Huygens
to: codex, all
related: [T-250, Q-023, D-027]
created: 2026-06-25
workflow: t250-huygens
---

# Scout report - Huygens - approval policy audit

## Scope

Read-only audit of existing governance, workflow, conveyor, launch and sandbox policies for Q-023.

## Existing Rules Found

- PROTOCOL: do not edit the same file blindly, write separate messages, do not delete/rewrite others, collect summary separately.
- AGENTS/PROTOCOL: automatic agents leave `proposed`; `accepted` is human or explicitly human-appointed collector.
- Workflow model: orchestrator decomposes, subagents run in parallel, synthesizer returns structured result; analysis/read-only has no contention; build goes through worktree or serialized commit.
- Conveyor model: DAG, cap 2-4 read-only in-flight, max one shared-tree build, PARK/SHIP/DISCARD, parse-gate GOOD/PARTIAL/BAD, commit lock/worktree for writes.
- Handoff: `top.py subagent-handoff` prints package, `flow.py launch-plan` prepares lane/prompt, external launcher starts worker, integrator checks/merges/commits.
- 3:1 sandbox policy accepted: up to 3 read-only researchers, supervisor/observer synthesizes, write only in sandbox, merge-to-main after review/approval.
- Top-agent manual: safe default read-only, execute prohibited until sandbox + accepted decision; proposed T/Q/D allowed, accepted/execute not allowed.

## Gaps

- Q-023 needs one governance answer for role -> action -> human approval.
- Rules are spread across AGENTS/PROTOCOL/workflow/top-layer docs.
- Need to separate functional role from person/agent id: Codex may be scout, integrator or main-agent depending on task.
- Need thresholds: advisory -> strict, who closes consensus, what belongs only in sandbox, worktree, and stream.
- Existing `docs/agent-roles-matrix.md` should be extended or cross-linked, not contradicted.

## Proposed Matrix Summary

| Role | Without confirmation | Sandbox/worktree/stream only | Human required |
|---|---|---|---|
| scout | read-only analysis, links, short report | outbox/topic report | canonical writes, accepted, execute/network |
| observer | compare reports, consensus/divergence, risk notes | stream/topic synthesis | accepted consensus |
| integrator | scoped edits, tests, evidence, synthesis, task closure, selective commit own files | Level 1 for hot/shared/foreign work | mixed/foreign commit without ownership, governance accepted |
| main-agent | orchestration, handoff, target/cap, proposed T/Q/D, safe commit | conveyor build/worktree, stream for variants | accepted decisions, execute, external/network/high-risk |
| human | final authority | may appoint integrator/collector | n/a |
| script/tool | deterministic checks, indexes, diagnostics, advisory reports | generated/output files in explicit scope | decisions, scope expansion, external execute |

## Proposed vs Human Decision

Can be proposed now:

- `docs/agent-approval-matrix.md`
- role definitions
- action tiers
- evidence requirements
- AGENTS -> functional roles mapping
- default governance proposed-only

Requires human:

- accept matrix;
- appoint non-human collector/integrator with `accepted` authority;
- approve execute/network/high-risk;
- approve auto-archive/mass history changes;
- decide who closes consensus;
- decide when advisory check becomes strict.

## Applied instructions

- Read-only scout work; no files changed by the subagent.
- Governance remains proposed.

## Checks

- Report preserved from platform subagent notification.
- Integrated into T-250 workflow by Codex.
- AGENTS.md: read-only/proposed governance boundaries preserved.

- PROTOCOL.md: outbox evidence, proposed status, and no accepted governance without human/integrator approval.

Checks:
python tools\instructions.py check-report queues\outbox\2026-06-25-scout-huygens-approval-policy.md

Note: included as proposed evidence for T-250/D-027/Q-023; no accepted decision made.
