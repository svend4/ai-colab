---
id: 2026-06-24-observer-hierarchy-methodology
type: methodology
status: historical
owner: codex
date: 2026-06-24
related: 
---

# Observer hierarchy methodology

## Summary

The repository already has the pieces for an agent hierarchy, but the useful ceiling is not the number of agents that can be started. The useful ceiling is the number of outputs that the top layer can intake, verify, synthesize, route, and turn into safe repository changes without losing evidence.

The practical model is:

```text
Codex integrator
  observer/synthesizer layer
    worker agents
```

Workers gather evidence and produce scoped reports. Observers compare several worker reports and reduce them to consensus, disagreement, missing evidence, risk, and recommended next action. Codex remains the integrator: it checks reports, applies only safe changes, opens follow-up tasks, and keeps final decision rights out of the worker layer.

For the current repository, the safe default is 2-4 active read-only or outbox-only workflows, one shared-tree build writer, and one observer cell when the topic becomes too wide for Codex to synthesize directly.

## Theoretical vs practical maximum

The theoretical ceiling from `docs/agent-capacity-methodology.md` is high:

```text
up to 16 concurrent agent tasks per workflow run
up to 1000 agents across one workflow run lifetime
up to 4096 fan-out items in one parallel or pipeline stage
only one nested workflow layer by default
parallel workflow runs multiply concurrency, but share CPU and top-layer processing
```

Those numbers are planning ceilings, not operating targets. `docs/workflow-conveyor-policy.md` and `docs/top-layer-throughput-methodology.md` both point to the same practical limit: top-layer processing and commit bandwidth bind before the platform ceilings. If agents return faster than Codex can process, the system creates `landed` backlog, duplicate reports, stale assumptions, and unmerged half-decisions.

Recommended practical ceilings for the current repository:

| Work type | Practical ceiling now | Reason |
|---|---:|---|
| Shared-tree code writer | 1 | avoids `index.lock`, generated-file churn, and overwriting other agents |
| Read-only/outbox-only workflows | 2-4 | Codex can still read and process returned outputs |
| One observer cell | 3 workers + 1 observer | good balance between evidence breadth and synthesis cost |
| Two observer cells | 6 workers + 2 observers | safe only when topics are independent and write scopes are separate |
| Three observer cells | 9 workers + 3 observers | useful for large read-only documentation or corpus analysis |
| Nine observer cells | 27 workers + 9 observers | only for read-only mapping with automated intake and strict report contracts |

The correct scaling question is not "how many agents can run?" but "how many agent reports can be converted into verified, non-conflicting repository progress per hour?"

## Recommended current topology

Current recommended topology:

```text
Codex integrator
  Observer cell A: one complex topic
    Worker A1
    Worker A2
    Worker A3
```

Use this shape when:

- the task is broad but read-only or outbox-only;
- several independent perspectives improve the evidence base;
- the result can be reduced into one compact observer report;
- Codex can process the observer result before launching the next wide wave.

Do not use this shape when:

- workers need to edit the same code files;
- the output requires immediate accepted governance;
- external code execution is needed;
- there are already unprocessed `landed` reports;
- the task is small enough for one direct Codex pass.

For build work, keep the topology narrower:

```text
Codex integrator
  one build worker or Codex itself
```

If multiple build variants are needed, route them through isolated streams or worktrees, then merge only one verified result.

## 3 workers + 1 observer cell

A cell has four roles:

| Role | Allowed output | Responsibility |
|---|---|---|
| Worker A | one scoped outbox report | collect evidence for subtopic A |
| Worker B | one scoped outbox report | collect evidence for subtopic B |
| Worker C | one scoped outbox report | collect evidence for subtopic C or verify claims |
| Observer | one synthesis outbox report | compare the three reports and reduce them to action |

Worker report contract:

```text
Task:
Scope:
Files read:
Commands run:
Findings:
Risks:
Recommended next action:
Forbidden changes:
Checks:
## Applied instructions
```

Observer report contract:

```text
Compared reports:
Consensus:
Disagreements:
Missing evidence:
Risk classification:
Recommended Codex action:
Do not apply yet:
Checks:
## Applied instructions
```

The observer should not decide that a policy is accepted or that code should be merged. The observer reduces cognitive load. Codex still verifies, applies, routes, or asks the human.

## Multi-cell topology

### One cell

```text
Codex
  Observer-1
    Worker-1A
    Worker-1B
    Worker-1C
```

Use for one complex theme, such as sandbox intake, unused advice activation, or documentation drift.

### Two cells

```text
Codex
  Observer-1: sandbox and external-code evidence
    3 workers
  Observer-2: documentation and instruction activation
    3 workers
```

Use only when both cells are independent and all writes are separate outbox files.

### Three cells

```text
Codex
  Observer-1: code and tool evidence
  Observer-2: documentation and navigation evidence
  Observer-3: governance and risk evidence
```

This is the highest reasonable current topology for one Codex integrator in this repository. It can work for read-only analysis, but only if Codex does not also try to perform a large build task at the same time.

### More than three cells

More than three cells should be treated as a special read-only corpus operation. It needs strict report templates, automatic intake, and a very small observer output. Without that, the top layer becomes the bottleneck and good advice stays unused.

## Evidence chain

The evidence chain must be durable and machine-checkable:

```text
worker prompt
  -> worker outbox report
  -> observer synthesis report
  -> Codex check-report and classification
  -> Codex synthesis or implementation
  -> validation and tests
  -> task/report/done marker or proposed decision
```

Each step must keep file paths and commands explicit. A useful agent report is not just an opinion. It is a small evidence package that another agent can verify without reading the whole chat.

Recommended evidence fields:

- exact files read;
- exact commands run;
- assumptions;
- what was not checked;
- result classification: read-only-report, variant, docs-change, build-change, governance, external-code;
- next action and risk;
- `Checks:` marker;
- `## Applied instructions`.

For this repository, a report is not ready for synthesis until this command passes:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-observer-hierarchy-methodology.md
```

## Decision rights

Decision rights should be explicit:

| Actor | Can decide | Cannot decide |
|---|---|---|
| Worker | what evidence it found inside scope | acceptance, merge, governance, external execution |
| Observer | consensus and disagreement summary | final acceptance or code integration |
| Codex | safe local application, validation, next task routing | human-only governance acceptance |
| Human maintainer | governance, risk acceptance, external execution, final direction | none inside project authority |

The main rule from `AGENTS.md` and `PROTOCOL.md` is that agents can propose and summarize, but accepted decisions require a human or an explicitly appointed collector. This prevents a wide lower layer from silently turning proposals into policy.

## Anti-overload rules

Stop launching more agents when any of these is true:

- `tools/conveyor.py status --json` reports `landed` outputs waiting for processing;
- a landed workflow has no output path;
- Codex cannot summarize the last returned reports in one concrete next action each;
- two workers would edit the same shared files;
- generated indexes are stale;
- a build task needs the same files as an in-flight analysis;
- the next decision is governance or external execution;
- `validate.py` or `generate.py --check` is not clean;
- worker reports fail `instructions.py check-report`.

Operational rule:

```text
REFILL only when intake is clean.
PROCESS before scale-up.
SYNTHESIZE before implementation when reports overlap.
One shared-tree build writer at a time.
```

## Concrete commands or pseudo-commands using existing tools

Read-only status and capacity:

```powershell
python tools\conveyor.py status --json
python tools\conveyor.py regulate --json
python tools\conveyor.py plan 9 --span 3
python tools\top.py conveyor --json
```

Prepare an external sub-agent handoff:

```powershell
python tools\flow.py launch-plan lagrange T-REVIEW "observer hierarchy read-only report" --json
```

Register a workflow when the orchestrator is allowed to write runtime logs:

```powershell
python tools\conveyor.py launch W-YYYY-MM-DD-topic "observer hierarchy review" --kind read-only-report --depends none
python tools\conveyor.py land W-YYYY-MM-DD-topic --output queues\outbox\2026-06-24-observer-hierarchy-methodology.md
python tools\conveyor.py ship W-YYYY-MM-DD-topic
```

Verify a returned report:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-observer-hierarchy-methodology.md
python tools\result_intake.py classify queues\outbox\2026-06-24-observer-hierarchy-methodology.md --json
python tools\validate.py
python tools\generate.py --check
```

For a 3 workers + 1 observer cell, use pseudo-IDs like this:

```text
W-topic-A-worker-1 -> outbox report A
W-topic-A-worker-2 -> outbox report B
W-topic-A-worker-3 -> outbox report C
W-topic-A-observer -> synthesis of A/B/C
Codex -> check, classify, apply or route
```

Do not put all four roles into one shared code edit. The cell is useful because worker outputs are independent and the observer output is a compact synthesis.

## Checks

Performed recovery checks:

```powershell
git status --short --untracked-files=all
python tools\conveyor.py status --json
Test-Path queues\outbox\2026-06-24-observer-hierarchy-methodology.md
```

Result before writing this file:

```text
target=2
n_inflight=0
n_landed=0
deficit=2
healthy=false
target report was missing
```

Expected verification after writing:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-observer-hierarchy-methodology.md
python tools\result_intake.py classify queues\outbox\2026-06-24-observer-hierarchy-methodology.md --json
```

## Applied instructions

AGENTS.md evidence:

- worked by `PROTOCOL.md`;
- did not delete messages;
- did not rewrite discussion history;
- did not change accepted decisions;
- used `queues/outbox/` for an automatic work result;
- kept the result as `status: proposed`.

PROTOCOL.md evidence:

- used the queue model where `queues/outbox/` stores agent-prepared results before they are integrated into main files;
- preserved append-only collaboration style by adding a new report instead of editing other agents' files;
- did not edit `STATUS.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `PROTOCOL.md`, or `AGENTS.md`;
- treated Git commit as a later integration step, not part of this outbox-only recovery run;
- kept the hierarchy compatible with streams, sandbox, and the four-level workspace pyramid.

Checks:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-observer-hierarchy-methodology.md
```
