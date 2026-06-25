---
id: 2026-06-24-codex-agent-hierarchy-operating-model
type: methodology
status: historical
owner: codex
date: 2026-06-24
related: 
---

# Codex operating model: agent hierarchy and orchestration

## Summary

The practical limit is not how many agents can be started. The practical limit is how many reports Codex can verify, synthesize, route, and convert into safe changes without losing evidence or overwriting work.

For the current repository, the recommended working mode is:

- 1 Codex integrator at the top;
- 2-4 active read-only or outbox-only workflows by default;
- 1 shared-tree build writer at a time;
- optional cells of 3 worker agents plus 1 observer/synthesizer for larger read-only analysis;
- human approval for governance acceptance, external-code execution, and risky merges.

## Maximums

Methodological ceiling from the current project discussion:

```text
up to 16 concurrent agent tasks per workflow run
up to 1000 agents across the lifetime of a workflow run
up to 4096 fan-out items in a parallel/pipeline stage
only 1 nested workflow layer by default
M parallel workflow runs can multiply concurrency, but synthesis becomes the bottleneck
```

This is a planning ceiling, not the recommended operating mode for this repository today.

Practical current ceiling:

| Mode | Recommended now | Why |
|---|---:|---|
| Shared-tree build writers | 1 | avoids code and generated-file conflicts |
| Read-only/outbox-only agents | 2-4 | Codex can still process landed reports |
| First observer cell | 3 workers + 1 observer | useful for evidence synthesis |
| Two observer cells | 6 workers + 2 observers | only if all write to separate outbox files |
| Three observer cells | 9 workers + 3 observers | only for documentation/search/synthesis waves |
| Nine observer cells | 27 workers + 9 observers | only for read-only corpus mapping with automated intake |

## 3 workers + 1 observer cell

A safe cell has four roles:

| Role | Writes | Responsibility |
|---|---|---|
| Worker A | one outbox file | collect evidence for one subtopic |
| Worker B | one outbox file | collect evidence for another subtopic |
| Worker C | one outbox file | collect evidence or run read-only verification |
| Observer | one synthesis outbox file | compare the three reports and send Codex consensus, divergence, risk, and next actions |

Workers do not decide. The observer does not accept decisions. Codex verifies and routes. A human approves governance/external execution where required.

## Multi-cell topology

### 1 cell

```text
Codex
  Observer-1
    Worker-1A
    Worker-1B
    Worker-1C
```

Use for one complex topic, such as sandbox intake or unused advice.

### 2 cells

```text
Codex
  Observer-1: sandbox and external-code
    3 workers
  Observer-2: documentation/advice activation
    3 workers
```

Use when the topics are independent and all outputs are outbox-only.

### 3 cells

```text
Codex
  Observer-1: code/tooling evidence
  Observer-2: documentation/synthesis evidence
  Observer-3: governance/risk evidence
```

Use when Codex has enough time to process landed reports and can run `check-report`, `result_intake`, and synthesis before launching more work.

### 9 cells

This is not recommended for normal development. It is only reasonable for read-only corpus mapping where every worker writes exactly one report and observers produce compact synthesis. Without automated intake and ranking, 9 cells will overload Codex.

## Evidence chain

Every worker report should contain:

- source paths read;
- commands run;
- findings;
- risk level;
- exact next action;
- exact forbidden files;
- `Checks:` marker;
- `## Applied instructions` with AGENTS.md and PROTOCOL.md evidence.

Every observer report should contain:

- which worker reports were compared;
- consensus items;
- divergence items;
- missing evidence;
- proposed action lane: apply now, synthesize more, ask human, block;
- one recommended next Codex action.

Codex then runs:

```powershell
python tools\instructions.py check-report <report-file>
python tools\result_intake.py classify <report-file> --json
python tools\conveyor.py land <workflow-id> --output <report-file>
python tools\conveyor.py ship <workflow-id>
```

## Anti-overload rules

Do not spawn more agents when:

- there are unprocessed landed reports;
- more than one build worker would edit the shared tree;
- a proposed task writes generated files;
- the next task depends on unfinished agent output;
- the report queue contains ambiguous references that fail `check-report`;
- external-code execution or governance acceptance is involved without human approval;
- Codex cannot summarize the last reports in a few concrete next actions.

## Current run example

Current active conveyor structure:

- Codex: implemented and closed T-237.
- Lagrange: produced agent conveyor activation checklist; landed and shipped.
- Halley: produced next agent work queue; landed and shipped.
- Faraday: in-flight observer hierarchy methodology.
- Mill: in-flight sandbox intake chain map.
- Ptolemy: in-flight unused advice audit.

This is a controlled overfill above target 2 because Faraday, Mill, and Ptolemy are read-only/outbox-only and have disjoint write scopes.

## Recommended next step

When Faraday, Mill, and Ptolemy land:

1. Verify all three reports with `check-report`.
2. Classify them with `result_intake.py`.
3. Ask one observer/synthesis agent to compare the three reports if they disagree.
4. Codex chooses one build task only.
5. Keep remaining ideas in outbox or turn them into tasks later.

Checks:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-codex-agent-hierarchy-operating-model.md
python tools\conveyor.py status --json
```

## Applied instructions

Applied instructions evidence:

AGENTS.md and PROTOCOL.md were followed. This is a new outbox methodology report. It does not delete messages, does not rewrite history, does not change accepted decisions, does not edit generated files, and does not commit git state.