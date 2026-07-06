---
id: delegation-gap-review-2026-07-06
type: report
title: "Delegation gap review: why agents are underused and how to refill the loop"
status: proposed
date: 2026-07-06
author: codex
related:
  - PKG-20260706-codex-delegation-refill
  - orchestrator-cycle-proposal-2026-07-06
  - closed-loop-agent-cauldron-conveyor
  - workflow-conveyor-policy
  - workflow-orchestration-policy
---

# Delegation gap review

## 1. Short answer

1.1. The user is right: the repository already says lead agents should delegate more work to subagents/workflows. The current failure mode is not lack of policy; it is weak activation.

1.2. The accepted policy says the strategic layer should not do mass work by hand: `docs/orchestrator-cycle-proposal-2026-07-06.md:29-33`, `docs/orchestrator-cycle-proposal-2026-07-06.md:54-66`.

1.3. The proposed closed-loop runbook says the missing part explicitly: all elements exist, but there is no single mandatory loop binding workflow result -> task/decision/new workflow/archive: `docs/closed-loop-agent-cauldron-conveyor.md:104`.

1.4. In this Codex chat, there is no directly callable live `agent()` or `workflow()` tool. Available local tooling can prepare handoff prompts (`tools/flow.py`) and track conveyor state (`tools/conveyor.py`), but actual worker launch is external: `docs/closed-loop-agent-cauldron-conveyor.md:272-282`.

## 2. Where parallel agent work is already written

2.1. `AGENTS.md:23` registers `subagent-worker` as service workflow executor.

2.2. `AGENTS.md:40` says `subagent-worker` acts only inside swarm tasks and does not decide alone.

2.3. `PROTOCOL.md:200-223` routes D-022 parallel work into Level-1 worktrees/streams instead of shared-tree collision.

2.4. `docs/orchestrator-cycle-proposal-2026-07-06.md:29-33` says main agents formulate/coordinate while mass work is done by subagents in workflows.

2.5. `docs/orchestrator-cycle-proposal-2026-07-06.md:72-79` defines the 8-tick package -> swarm -> verification -> integration -> demonstration -> new tasks -> ratification loop.

2.6. `docs/closed-loop-agent-cauldron-conveyor.md:25-34` defines the full strategic question -> fan-out -> synthesis -> cauldron -> next-cycle loop.

2.7. `docs/closed-loop-agent-cauldron-conveyor.md:122-132` assigns launch/handoff to lead agents and conveyor supervision to coordinators.

2.8. `docs/closed-loop-agent-cauldron-conveyor.md:262-270` says independent read-only nodes can run in parallel and follow-ups become new nodes.

2.9. `docs/workflow-conveyor-policy.md:12-16` explains that the conveyor exists to overlap several workflow windows and prevent the orchestrator from waiting idly.

## 3. Five gaps blocking active delegation

3.1. Gap 1: handoff is not package-aware. `tools/flow.py` can generate a worker prompt, but it expects a single `<agent> <task>` pair and encourages `pipeline.py claim`; it does not read `kotel/packages/PKG-*.md` roles.

3.2. Gap 2: no local live launcher. `docs/closed-loop-agent-cauldron-conveyor.md:282` says the real launch is external. In this chat, I can create packages and prompts, but I cannot honestly mark a worker as running unless an external thread/workflow is actually started.

3.3. Gap 3: conveyor has only runtime states for launched work. It can show `REFILL`, `PROCESS`, and `IDLE`, but it lacks a first-class `ready-for-launch` package queue. Using `launch` for a not-yet-started brief would create fake in-flight state.

3.4. Gap 4: the lead-agent cycle does not force delegation before solo work. `python tools/top.py cycle codex` prints a safe individual work cycle, but not a mandatory "can this be split into scout roles?" step.

3.5. Gap 5: returned worker reports are not automatically materialized into the next action. The docs point to `process-landed`, `cauldron-lanes`, and `cauldron_task_materializer`, but the loop still relies on the lead-agent remembering to process and refill.

## 4. Five minimal changes

4.1. Add a package-aware handoff command:

```powershell
python tools\top.py package-handoff kotel\packages\PKG-20260706-codex-delegation-refill.md governance-scout --json
```

It should read the package role, print the exact prompt, and never auto-claim a canonical T-id unless the package maps that role to a task.

4.2. Add a `ready` lane to conveyor reporting, or add a read-only `package_queue.py` that reports packages with `status: agreed` and role outputs missing. Do not overload `inflight`.

4.3. Extend `top.py cycle <agent>` with an early gate:

```text
Can this task be split into read-only scouts? If yes, create/update a PKG and do not do all work solo.
```

4.4. Make `package_gate.py check --all` and `agenda_gen.py` part of `top.py status` or `top.py health` as advisory output, so stale packages are visible.

4.5. Add a "landed output processor" checklist to `top.py process-landed`: classify output, verify evidence, synthesize consensus/divergence, create follow-up T/Q/D candidates, then ship/dismiss.

## 5. Files to touch if implementing

5.1. Documentation:

- `docs/orchestrator-cycle-proposal-2026-07-06.md` for the accepted cycle summary if human wants wording tightened.
- `docs/closed-loop-agent-cauldron-conveyor.md` for the proposed runbook and "ready-for-launch vs in-flight" distinction.
- `docs/workflow-conveyor-policy.md` for conveyor state semantics.

5.2. Tools:

- `tools/top.py` for `package-handoff` and stronger `cycle`.
- `tools/flow.py` for package role prompts, or a new `tools/package_handoff.py`.
- `tools/conveyor.py` if runtime should represent `ready` separately from `inflight`.
- `tools/package_gate.py` only if new front-matter fields need validation.
- `tools/agenda_gen.py` to surface ready packages and missing role outputs.
- `tools/cauldron_task_materializer.py` to turn processed synthesis into task candidates.

5.3. Operating files:

- `kotel/packages/PKG-*.md` for each delegation batch.
- `kotel/agenda.md` while the agenda remains manual.
- `queues/outbox/*.md` for worker reports.

## 6. Codex self-critique

6.1. The immediate reason I underused agents is practical: I optimized for local edits and validation because no direct live worker launcher was exposed in this chat.

6.2. That is not enough. The repo policy already expects a lead-agent to package work even when launch is external. I should at least create the package/handoff artifacts first, then continue integration work while waiting for external workers.

6.3. The correct future pattern is:

```text
brief -> PKG -> A/B/C read-only roles -> Codex continues safe solo work
     -> landed reports -> verification -> synthesis -> cauldron lanes
     -> follow-up task/tool/doc change
```

6.4. For this turn I created `PKG-20260706-codex-delegation-refill` and this review as the first refill artifact.

## 7. Strategic questions for Stefan / human gate

7.1. Should Codex create background Codex threads for `governance-scout`, `tooling-scout`, and `process-scout` when the user says "use agents", or only create package files and let the human/other platforms launch them?

7.2. Should `ready-for-launch` packages count toward conveyor target, or should only actually running workers count?

7.3. Should `top.py cycle` be changed from "safe solo cycle" to "delegation-first cycle" for strategic tasks?

7.4. Should package-aware handoff be a separate script (`tools/package_handoff.py`) or a subcommand inside `top.py`?

7.5. Should low-risk read-only scout roles be allowed to start without a T-id, using only a `PKG-*` id?