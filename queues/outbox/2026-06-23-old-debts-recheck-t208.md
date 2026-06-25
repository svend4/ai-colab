---
type: report
agent: codex
title: Old unfinished tasks recheck — T-208 safety correction
date: 2026-06-23
status: historical
---

# Old unfinished tasks recheck — T-208 safety correction

## Finding

`T-208` was visible as pipeline-ready because its front-matter said `status: todo`, but the task body says the opposite:

- `risk: high`;
- execute-sandbox runner requires explicit Stefan "go";
- D-014 keeps execute scenarios OFF;
- stages 5/7/8 require cauldron and human gate.

## Change

Changed `tasks/T-208.md` front-matter:

```md
status: blocked
```

This is not implementation of execute mode. It is a safety correction so the pipeline does not hand a high-risk execute track to an agent as ordinary ready work.

## Proposed solution path

1. Keep `T-208` blocked until Stefan explicitly approves the execute direction.
2. Split the design into low-risk read-only/preflight tasks first: anti-fake sandbox probe, mount/network preflight, limits validator.
3. Send human-first-run, run-plan executor, and actual runner core through cauldron/human gate before any mode:execute path is created.
4. Keep current system read-only unless D-014 is amended by an accepted decision.

## Other old debts seen in the same recheck

- `T-020`: still blocked on an external/source input path. Best next step: redefine it as generic read-only sandbox intake if no specific svend4 source is provided.
- `T-174`: correctly blocked as async stdio Windows runtime gap; sync gateway remains the regular acceptance gate.
- `T-202`: stale commit task; needs reconcile or retirement, because current tree has moved far beyond the original T-198..T-201 commit scope.
- `T-213` / `T-214`: doing without active claim; need claim restoration or explicit reconciliation before anyone edits or closes them.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: no чужие сообщения deleted; no history rewritten.
- `docs/execute-sandbox-preflight.md`: execute remains OFF; no external code was run.
- `docs/external-code-sandbox.md`: no sandbox execution was attempted.
- `docs/parallel-work-policy.md`: dirty shared tree respected; no staging/commit.
- `docs/instruction-assurance.md`: this report records rationale/evidence for the metadata safety fix.
- Checks: `python tools/instructions.py preflight codex T-208`; `python tools/pipeline.py status`; `python tools/validate.py`; `python tools/generate.py --check`; `python tools/drift_check.py`.