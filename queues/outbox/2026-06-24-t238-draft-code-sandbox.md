---
id: 2026-06-24-t238-draft-code-sandbox
type: implementation-report
status: done
owner: codex
date: 2026-06-24
related:
  - tasks/T-238.md
  - sandbox/README.md
  - sandbox/.gitignore
  - sandbox/drafts/README.md
  - sandbox/templates/draft-code-manifest.template.json
  - docs/external-code-sandbox.md
  - docs/execute-sandbox-preflight.md
---

# T-238 draft-code sandbox lane

## Summary

A no-execute draft-code lane was added for experimental code written by agents or humans. The lane lets agents propose program code without touching shared project code and without authorizing execution.

This answers the user question: yes, agents can have a place to write experimental code, but it must be treated as an untrusted proposal until Codex and observers review it and a separate promotion task is created.

## What Changed

- Added `sandbox/drafts/README.md`.
- Added `sandbox/templates/draft-code-manifest.template.json`.
- Updated `sandbox/.gitignore` so raw draft folders are ignored by default.
- Updated `sandbox/README.md` with the draft-code lane.
- Added task source `tasks/T-238.md`.

## Proposed Flow

```text
agent writes draft code -> manifest -> static review -> outbox report -> Codex decision -> separate promotion task -> normal tests -> possible mainline change
```

The important boundary is that the draft lane is not a build lane. It is a review lane.

## Advantages

- Agents can write concrete code variants without blocking the main repository.
- Several agents can produce competing variants in separate draft folders.
- Observers can compare variants before Codex chooses one.
- The main `tools/`, `drivers/`, `core/`, and generated files stay protected.
- Draft code can be checked read-only with static tools before any execution.
- The idea fits the existing sandbox and conveyor model.

## Disadvantages And Risks

- Draft folders can accumulate noise if not periodically summarized or deleted outside Git.
- Agents may confuse draft code with accepted code unless reports are strict.
- Static review cannot prove runtime correctness.
- If raw drafts are force-added to Git too early, the repository can fill with half-finished code.
- If execute gates are ignored, this lane becomes unsafe.

## Verification Note

The full sandbox tree currently contains older self-reflection inbox material with broken relative links. That is pre-existing intake data and is not part of the new draft-code lane. The correct link-check target for this task is sandbox/drafts.

## Policy Opinion

The best structure is a three-step promotion gate:

1. Draft: agent may write code only in an isolated draft folder.
2. Review: observer and Codex inspect it read-only and require an outbox report.
3. Promotion: useful code is rewritten or moved through a normal claimed task with tests.

This keeps creative parallelism without letting unreviewed agent code become operational code.

## Checks

Checks:

Commands to verify this report and the lane:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-t238-draft-code-sandbox.md
python tools\sandbox_link_checker.py sandbox --json
python tools\validate.py
python tools\generate.py --check
```

## Applied instructions

Applied instructions evidence:

AGENTS.md and PROTOCOL.md were followed. The work was recorded as a task, no accepted decision was changed, no external or draft code was executed, and the result was documented in a new outbox report.