---
status: historical
---
# T-227 — evidence addenda and pipeline fencing test alignment

Codex closed the fresh assurance debt for `T-223` and `T-224` without rewriting other agents' done markers.

## Changes

- Added `queues/evidence/T-223.evidence.md`.
- Added `queues/evidence/T-224.evidence.md`.
- Updated `tools/test_pipeline_fencing.py` so `done` without `--claim` is expected to fail, matching `tasks/T-224.md` and current `tools/pipeline.py` behavior.

## Findings

`T-223` evidence says the D-Card validator exists, but current repository inventory still lacks many D-Cards. That is a valid partial implementation result, not a reason to mark full metadata enforcement complete.

`T-224` evidence found a real stale test: the code had moved to strict claim fencing, but the test still expected backward-compatible `done` without claim. The test is now aligned with the stricter safety policy.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; docs/instruction-assurance.md; tasks/T-223.md; tasks/T-224.md; tools/pipeline.py; tools/test_pipeline_fencing.py; queues/evidence/T-223.evidence.md; queues/evidence/T-224.evidence.md.

Checks:
- python -m py_compile tools/enforce_metadata.py tools/pipeline.py tools/test_pipeline_fencing.py -> OK
- python tools/test_pipeline_fencing.py -> OK after test update
- python tools/instructions.py check-report queues/evidence/T-223.evidence.md -> OK after evidence update
- python tools/instructions.py check-report queues/evidence/T-224.evidence.md -> OK after evidence update
- python tools/assurance.py all -> expected PASS after addenda are indexed