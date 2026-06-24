# T-232 — D-Card repair for portability_check

Codex repaired the current metadata soft-check for the new portability acceptance tool.

## Change

Added standard machine-readable D-Cards to:

- `tools/portability_check.py`
- `tools/test_portability_check.py`

The scope was expanded from the main tool to its paired test because `enforce_metadata.py --warn-only` showed the test as the last remaining missing D-Card after the first edit.

No runtime logic was changed.

## Result

`python tools/enforce_metadata.py --warn-only` now reports that all scripts in `tools/` have valid D-Cards.

`python tools/dcard_indexer.py` regenerated `docs/dcard_index.md` with 475 D-Cards.

## Check nuance

A parallel verification pass briefly produced an inconsistent `top.py health` result: its embedded `generate --check` was OK, while its embedded `drift_check` reported stale navigation. Re-running `generate --check`, `drift_check`, and then `top.py health` sequentially cleared the inconsistency. This looks like a verification-order/race symptom, not a persistent repository drift.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; tasks/T-232.md; tools/portability_check.py; tools/test_portability_check.py; tools/enforce_metadata.py; tools/dcard_indexer.py; docs/dcard_index.md; tools/generate.py; tools/validate.py; tools/drift_check.py; tools/assurance.py; tools/top.py; Checks.

Checks:

- python -m py_compile tools/portability_check.py tools/test_portability_check.py -> OK
- python tools/test_portability_check.py -> OK
- python tools/enforce_metadata.py --warn-only -> OK, all tools have D-Cards
- python tools/dcard_indexer.py -> OK, index regenerated with 475 D-Cards
- python tools/generate.py -> OK, generated files updated
- python tools/pipeline.py snapshot -> OK
- python tools/generate.py --check -> OK
- python tools/validate.py -> OK=12 WARN=0 ERROR=0
- python tools/drift_check.py -> OK
- python tools/assurance.py all -> PASS
- python tools/top.py health -> EXIT 0 after sequential recheck