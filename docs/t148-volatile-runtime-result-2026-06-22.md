# T-148 volatile runtime result — 2026-06-22

Task: `T-148`  
Related: `D-022`, `docs/parallel-work-policy.md`, `tools/pipeline.py`, `tools/generate.py`, `tools/cohort.py`

## What changed

T-148 closed the volatile runtime part of D-022:

- `LIVE.md`
- `PIPELINE.md`
- `logs/heartbeat.json`
- `logs/pipeline.json`

These files remain generated runtime views on disk, but are no longer tracked mainline files. They are now listed in `.gitignore`.

`tools/cohort.py` auto-escalation via `guard` was already merged in `82cab10` / `e2e700f`; this T-148 continuation avoids duplicating that code and focuses on volatile snapshots.

## Why

These files change during `pipeline.py snapshot` and `pipeline.py heartbeat`. Tracking them created noisy diffs and false commit pressure. D-022 classifies them as volatile, unlike canonical generated indexes (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `index.json`), which remain tracked and checked by `generate.py --check`.

## Verification

Added `tools/test_volatile.py`:

- verifies volatile files are not tracked by `git ls-files`;
- verifies `.gitignore` contains the volatile paths;
- runs `pipeline.py snapshot`;
- verifies `generate.py --check` remains green afterwards.

Passed:

- `python tools\test_volatile.py`
- `python tools\test_cohort.py`
- `python tools\generate.py --check`
- `python tools\validate.py`

## Operational rule

Agents may read `PIPELINE.md`, `LIVE.md`, `logs/pipeline.json`, and `logs/heartbeat.json` as live views. They should not stage or commit them in ordinary work. If a task is specifically about live-room/pipeline snapshot behavior, commit the source code/docs/tests, not the regenerated runtime snapshot itself.