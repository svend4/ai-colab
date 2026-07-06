---
id: PKG-20260706-codex-delegation-refill
type: package
title: "Delegation refill: governance/process/tooling scouts"
status: agreed
orchestrator: codex
lead: codex
prepared_by: codex
risk: low
mode: read-only-scouts
goal: "Refill the orchestration loop with narrow read-only scout assignments and a Codex integration review."
tasks: []
related:
  - D-017
  - D-018
  - D-022
  - D-035
  - orchestrator-cycle-proposal-2026-07-06
  - closed-loop-agent-cauldron-conveyor
input_zones:
  - AGENTS.md
  - PROTOCOL.md
  - docs/
  - reports/
  - tools/
output_zones:
  - reports/delegation-gap-review-2026-07-06.md
  - queues/outbox/2026-07-06-delegation-refill-codex.md
  - kotel/packages/PKG-20260706-codex-delegation-refill.md
agreed_by: []
posted_at: 2026-07-06
review_deadline: 2026-07-07
veto_by: []
review_state: open
deadline: 2026-07-07
---

# PKG-20260706-codex-delegation-refill

## 1. Purpose

1.1. User feedback: Codex underuses agents/subagents and too often performs integration work alone.

1.2. This package converts that feedback into three narrow read-only scout assignments plus one integration step.

1.3. This package does not claim that live subagents are already running. In the current Codex tool surface, no direct `agent()` or `workflow()` launcher is callable from this chat. Therefore this package is `ready-for-launch` operational material, not a fake `in-flight` conveyor entry.

1.4. If an external launcher, Codex background thread, Claude workflow, or human-operated agent is available, it can run any role below and return the result to the requested `queues/outbox/` file.

## 2. Delegation Rules

2.1. All roles are read-only unless a human or lead-agent explicitly upgrades the package.

2.2. No role may set `accepted` decisions, edit final decisions, delete files, or commit directly.

2.3. If a role finds a disagreement, it must preserve both sides and route it through cauldron/divergence, not overwrite the mainline.

2.4. Output must be short, structured, and evidence-backed with `file:line` references.

2.5. Codex/lead-agent remains responsible for checking the result before any canonical change.

## 3. Agent A: governance-scout

3.1. Mode: read-only.

3.2. Output target:

```text
queues/outbox/2026-07-06-governance-scout-orchestration-audit.md
```

3.3. Task:

```text
Context: the user requires more active use of subagents and a delegation conveyor.

Read:
- AGENTS.md
- PROTOCOL.md
- docs/orchestrator-cycle-proposal-2026-07-06.md
- docs/closed-loop-agent-cauldron-conveyor.md
- reports/concurrent-work-synthesis-2026-07-06.md
- reports/orchestrator-cycle-proposal-review-codex-2026-07-06.md
- docs/agent-capacity-methodology.md
- docs/workflow-conveyor-policy.md

Return:
1. Where the repo already says agents should work in parallel.
2. Five concrete gaps blocking active delegation.
3. Five minimal policy/process changes needed.
4. Files to touch if implemented.

Use file:line references. Do not mark decisions accepted. Everything is proposed.
```

## 4. Agent B: tooling-scout

4.1. Mode: read-only.

4.2. Output target:

```text
queues/outbox/2026-07-06-tooling-scout-handoff-gap.md
```

4.3. Task:

```text
Inspect:
- tools/top.py
- tools/flow.py
- tools/conveyor.py
- tools/package_gate.py
- tools/agenda_gen.py
- tools/zone_overlap.py
- tools/cauldron_task_materializer.py

Return:
1. Which commands already support package/handoff/conveyor work.
2. Which commands only print advice and do not mutate state.
3. What is missing for a safe package-aware subagent launch flow.
4. A minimal CLI proposal, e.g. `python tools/top.py package-handoff <PKG> <role> --json`.
5. Risks if conveyor `launch` is used when no real external worker is running.
```

## 5. Agent C: process-scout

5.1. Mode: read-only.

5.2. Output target:

```text
queues/outbox/2026-07-06-process-scout-idle-conveyor.md
```

5.3. Task:

```text
Inspect:
- logs/conveyor.json if present
- kotel/agenda.md
- kotel/packages/
- queues/outbox/ recent orchestration reports
- reports/delegation-gap-review-2026-07-06.md if it already exists

Return:
1. Why the conveyor can become idle even when policy says it should be refilled.
2. Which status signals should trigger delegation.
3. What a lead-agent should do while waiting for workers.
4. How to avoid fake in-flight entries.
5. A short checklist for every future Codex turn.
```

## 6. Integrator Step

6.1. Codex must synthesize returned reports, not accept them blindly.

6.2. If all scouts agree, Codex may create a ratify-build package or a low-risk tooling task.

6.3. If scouts disagree, Codex must create a divergence note or stream packet and route it to cauldron.

6.4. Minimum processing commands after any scout result lands:

```powershell
python tools\top.py process-landed --topic delegation-refill
python tools\top.py cauldron-lanes delegation-refill --json
python tools\package_gate.py check kotel\packages\PKG-20260706-codex-delegation-refill.md
python tools\validate.py
```

## 7. Current Codex Integration Note

7.1. Codex performed the first integration review directly because no callable live subagent runtime was available in this chat.

7.2. The review is recorded in:

```text
reports/delegation-gap-review-2026-07-06.md
```

7.3. This package remains useful because another agent can now run A/B/C independently and compare its result with Codex's integration review.