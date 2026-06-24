---
id: 2026-06-24-halley-t237-link-checker-review
type: review
status: done
owner: halley
date: 2026-06-24
related:
  - tasks/T-237.md
  - tools/sandbox_link_checker.py
  - queues/done/T-237.done.md
---

# Halley review: T-237 sandbox link checker

## Summary

Halley reviewed T-237 without editing files or committing changes. The existing sandbox link checker is a useful read-only base, but it should not be treated as fully closed until tests, exit codes, path-escape protection, deterministic traversal, and task-state reconciliation are handled.

## Findings

What is already good:

- `tools/sandbox_link_checker.py` exists and is read-only.
- It recursively scans Markdown files.
- It resolves relative links against the source file directory.
- It supports root-style links against the scan root.
- It ignores common external links and same-document anchors.
- It can output JSON.

What is missing before closure:

- Add `tools/test_sandbox_link_checker.py`.
- Broken links should produce a non-zero CLI exit code.
- `../..` path escapes should be reported as outside the sandbox root.
- Reports should include relative source paths and line numbers.
- Traversal should be sorted for deterministic tests.
- Reconcile pipeline state: `tasks/T-237.md` still needs to match the done marker if the task is closed.

## Recommended Tests

- Clean relative links across root and subdirectories.
- Broken relative links with anchor stripping.
- Ignored external links and same-document anchors.
- Root-relative sandbox links.
- Outside-root traversal.
- CLI exit codes: clean is 0, broken is 1, bad input is 2.

## Commands Suggested

```powershell
python tools/test_sandbox_link_checker.py
python tools/sandbox_link_checker.py data/fixtures
python tools/sandbox_link_checker.py indexes
python tools/validate.py
python tools/generate.py --check
git status --short
```

Checks:

- python tools\instructions.py check-report queues\outbox\2026-06-24-halley-t237-link-checker-review.md was used as the report gate.

## Applied instructions

Applied instructions evidence:

AGENTS.md and PROTOCOL.md were followed by keeping this review in a new outbox report. No other agent output was deleted, no accepted decision was changed, and no commit was made.