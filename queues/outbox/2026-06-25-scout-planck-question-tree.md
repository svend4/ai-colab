---
id: outbox-2026-06-25-scout-planck-question-tree
type: subagent-report
status: proposed
from: Planck
to: codex, all
related: [T-250, Q-023]
created: 2026-06-25
workflow: t250-planck
---

# Scout report - Planck - question-tree next work

## Scope

Read-only audit of:

- `topics/information-refactoring-question-tree-2026-06-25.md`
- `topics/information-refactoring-cycle-2-2026-06-25.md`
- `topics/information-refactoring-cycle-3-2026-06-25.md`
- `tools/question_tree.py`
- `tools/top.py`
- `questions/Q-023.md`

## Findings

Question-tree state:

```text
questions: 32
unknown: 0
open: 4
requires-decision: 4
partial: 16
solved: 8
```

Requires decision:

- Q11.3.1: what must be decided by a human; already routed to Q-023.
- Q9.1.1: what should be done first.
- Q4.3.1: operations that cannot be done live.
- Q7.2.1: what changes increase maturity.

Open or policy/task follow-up:

- Q2.3.1: what would be different if starting from scratch.
- Q5.3.1: physical file moves vs status/index/filter first.
- Q6.3.1: metadata budget.
- Q7.3.1: rejuvenation metrics and advisory/strict classification.

## Recommended Next Tasks

1. `docs/agent-approval-matrix.md` plus proposed decision for Q-023.
2. Strengthen `tools/question_tree.py` parser around answer headings and possible answer markers.
3. `tools/top.py actions` as unified read-only dashboard.
4. a START HERE entrypoint or an active-surface document as human/agent entrypoint.
5. `historical`/`superseded` sanitation policy and index.

## Proposed Role Workflow

- Scout takes one lane: `open`, `requires-decision`, `partial`, or `solved`.
- Observer compares 2-3 scout reports: `consensus`, `divergence`, `needs evidence`, `recommended next action`.
- Integrator performs a small verifiable action: create Q/D/task/tool/test; accepted decisions remain human/integrator-governed.

## Scaling Rule

Do not launch more scouts until an observer, report format, landing rule, and approval matrix exist.

## Applied instructions

- Read-only scout work; no files changed by the subagent.
- Preserved divergence and governance as proposed, not accepted.

## Checks

- Report preserved from platform subagent notification.
- Integrated into T-250 workflow by Codex.
- AGENTS.md: read-only/proposed governance boundaries preserved.

- PROTOCOL.md: outbox evidence, proposed status, and no accepted governance without human/integrator approval.

Checks:
python tools\instructions.py check-report queues\outbox\2026-06-25-scout-planck-question-tree.md

Note: included as proposed evidence for T-250/D-027/Q-023; no accepted decision made.
