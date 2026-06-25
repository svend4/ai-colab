---
type: report
agent: codex
date: 2026-06-24
topic: execute-sandbox-safety
status: historical
applied: AGENTS.md, PROTOCOL.md, docs/execute-sandbox-preflight.md, docs/execute-sandbox-runner-design-2026-06-23.md, tasks/T-208.md, tasks/T-217.md, queues/evidence/T-217.evidence.md
related: 
---

# Execute-track safety recheck

## Finding

`T-217` and `T-208` were marked `done` by another agent with plain done markers. `assurance.py all` flagged missing applied-evidence.

Verification found that `tools/sandbox_runner.py` exists and has mocked tests, but the real execute path currently safe-stops before Docker execution:

```text
python tools\sandbox_runner.py execute test-driver alpine -- echo hello
-> ERROR: Preflight checks failed; Docker backend not reachable
```

## Action taken

1. Added `queues/evidence/T-217.evidence.md` for the runner-core implementation.
2. Fixed `tools/sandbox_runner.py` console output via `_ioutil.configure_output()`.
3. Changed `tasks/T-208.md` front-matter from `done` back to `blocked` because the umbrella execute track is not fully accepted until backend/human/scenario ratification is complete.

## Boundary

`T-217` evidence means: runner core exists, mocked tests pass, real path stopped safely at preflight.

It does not mean: arbitrary external code may now be executed.

`T-208` remains blocked until:

1. approved sandbox backend probe passes;
2. human first-run approval exists;
3. concrete execute scenario is accepted through D-018/D-006;
4. any driver `mode: execute` is enabled only after the gate package is accepted.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: no чужой done marker was rewritten; corrections were made through task front-matter and append-only evidence/outbox.
- `docs/execute-sandbox-preflight.md`: execute remains gated and stopped before real run.
- `docs/execute-sandbox-runner-design-2026-06-23.md`: runner core is the last high-risk stage and does not close the umbrella without human/backend ratification.

Checks:
- python tools\sandbox_runner.py
- python tools\test_sandbox_runner.py
- python tools\execute_preflight.py check-all test-driver docker docker run --rm --network none --memory 2g --cpus 2 --pids-limit 256 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m alpine echo hello
- python tools\sandbox_runner.py execute test-driver alpine -- echo hello
- python tools\assurance.py all