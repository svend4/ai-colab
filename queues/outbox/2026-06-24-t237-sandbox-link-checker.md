---
id: 2026-06-24-t237-sandbox-link-checker
type: implementation-report
status: done
owner: codex
date: 2026-06-24
related:
  - tasks/T-237.md
  - tools/sandbox_link_checker.py
  - tools/test_sandbox_link_checker.py
  - queues/outbox/2026-06-24-halley-t237-link-checker-review.md
---

# T-237 sandbox link checker

## Summary

T-237 was completed by hardening the existing read-only Markdown link checker and adding targeted tests. The implementation now reports broken relative links, line numbers, deterministic traversal, non-zero exit codes, and outside-root traversal attempts for isolated sandbox directories.

## Changes

- Updated `tools/sandbox_link_checker.py`.
- Added `tools/test_sandbox_link_checker.py`.
- Kept the checker read-only: it scans Markdown files and does not modify the sandbox content.

## Behavior

The checker now:

- scans `.md` files recursively;
- resolves relative links from the source file directory;
- resolves root-style links from the sandbox root;
- ignores common external schemes and same-document anchors;
- strips local anchors before file existence checks;
- reports relative source path, line number, link text, target, and issue kind;
- reports `outside-root` for links that escape the isolated scan root;
- returns exit code `0` for clean scans, `1` for link issues, and `2` for bad input.

## Verification Notes

`data/fixtures` is self-contained and passes. `indexes` is not self-contained when scanned as an isolated directory, because its generated Markdown points to sibling repository folders such as `../docs` and `../tasks`; the new checker correctly reports those as `outside-root` and exits with code `1`.

Checks:

```powershell
python -m py_compile tools\sandbox_link_checker.py tools\test_sandbox_link_checker.py
python tools\test_sandbox_link_checker.py
python tools\sandbox_link_checker.py data\fixtures --json
python tools\sandbox_link_checker.py indexes --json
python tools\validate.py
python tools\generate.py --check
```

Results:

- py_compile: OK.
- unit tests: OK, all tests passed.
- `data/fixtures`: OK, 4 Markdown files checked, 0 issues.
- `indexes`: expected exit `1`, 444 outside-root issues, useful as evidence that `indexes` is not an isolated sandbox by itself.
- `validate.py`: OK=12 WARN=0 ERROR=0.
- `generate.py --check`: reported stale `TASKS.md` and `index.json` because T-237 was claimed; regeneration is required after pipeline close.

## Applied instructions

Applied instructions evidence:

AGENTS.md and PROTOCOL.md were followed. The task was claimed before code changes, other agents' reports were preserved, and the implementation used a new outbox report instead of editing Halley's review.