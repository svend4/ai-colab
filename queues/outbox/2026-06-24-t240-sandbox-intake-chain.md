---
id: 2026-06-24-t240-sandbox-intake-chain
type: implementation-report
status: proposed
owner: codex
date: 2026-06-24
related: T-240, queues/outbox/2026-06-24-sandbox-intake-chain-map.md, queues/outbox/2026-06-24-sandbox-intake-orchestrator-review.md
---

# T-240 — sandbox intake chain orchestrator

Implemented a read-only intake-chain orchestrator for sandbox sources and agent draft-code folders.

## What changed

- Added `tools/sandbox_intake_chain.py`.
- Added `tools/test_sandbox_intake_chain.py`.
- Stabilized the upstream contracts that the orchestrator depends on:
  - `tools/python_analyzer.py` now exposes `analyze_source`, `analyze_file`, structured AST summaries, structured risks, and a CLI-compatible `main(argv)`.
  - `tools/sandbox_schema_validator.py` now exposes `scan`, scans all `.json` files, returns summary counts and issue codes, and keeps `scan_directory`/`validate_manifest` compatibility for older callers.
- Kept the security invariant: target code is parsed/read as data only. The normalized result always has `execute_allowed: false`.

## Result contract

`python tools/sandbox_intake_chain.py <folder> --json` emits schema `sandbox-intake-result.v1` with four check blocks:

1. `inventory` — file counts, extensions, markdown/python/manifest lists.
2. `python_ast` — read-only Python AST analysis through `tools/python_analyzer.py`.
3. `schema` — JSON and manifest validation through `tools/sandbox_schema_validator.py`.
4. `markdown_links` — local markdown link validation through `tools/sandbox_link_checker.py`.

The risk routing is intentionally conservative:

- schema errors, markdown-link errors, or Python parse errors -> `high`, route `ask-agent-revision`;
- Python risk signals or schema warnings -> `medium`, route `keep-quarantine`;
- clean `agent-draft` input -> `low`, route `create-promotion-task`;
- no route grants execution.

## Agent review applied

Ampere reviewed the planned orchestrator and found real contract drift before closure:

- `tools/test_python_analyzer.py` failed because `analyze_source` was missing.
- `tools/test_sandbox_schema_validator.py` failed because `scan` was missing.
- `tools/test_sandbox.py` failed because the Python AST report did not match the expected structured analyzer output.

I applied that review before closing T-240. The fix was not to weaken the new orchestrator; it was to restore the lower-level contracts and then make the orchestrator use them.

Chandrasekhar reviewed `conveyor recover` adoption separately. That report is not implemented in T-240, but it should become the next top-layer wrapper task: expose recover as an advisory `tools/top.py` command, not as automatic repair.

## Current observed behavior

`sandbox/drafts` is clean as an empty draft lane:

- risk: `low`
- route: `create-promotion-task`
- execute allowed: `false`

The full `sandbox/` folder is intentionally not clean:

- risk: `high`
- route: `ask-agent-revision`
- blocking: `markdown-link-errors`
- warnings: `python-risk-signals`

That is a useful result, not a failure. It shows the chain can distinguish a clean draft lane from the broader historical sandbox area that still contains unresolved material.

## Applied instructions

- Followed `AGENTS.md`: used outbox reports, did not delete other agents' messages, did not approve decisions as accepted.
- Followed `PROTOCOL.md` task workflow: worked through claimed T-240 and prepared a close-out report.
- Followed sandbox policy: read-only intake only, no execution of sandbox code, no network, no dependency install.
- Applied Ampere's read-only risk review before finalizing the implementation.
- Used the Windows fallback for file edits because `apply_patch` was blocked by the local sandbox wrapper; edits remained inside the allowed workspace.

Checks:

```
python -m py_compile tools\python_analyzer.py tools\sandbox_schema_validator.py tools\sandbox_intake_chain.py tools\test_python_analyzer.py tools\test_sandbox_schema_validator.py tools\test_sandbox.py tools\test_sandbox_intake_chain.py -> OK
python tools\test_python_analyzer.py -> OK
python tools\test_sandbox_schema_validator.py -> OK
python tools\test_sandbox.py -> OK
python tools\test_sandbox_intake_chain.py -> OK
python tools\instructions.py check-report queues\outbox\2026-06-24-sandbox-intake-orchestrator-review.md -> OK
python tools\result_intake.py classify queues\outbox\2026-06-24-sandbox-intake-orchestrator-review.md --json -> OK, class governance, confidence medium
python tools\sandbox_intake_chain.py sandbox\drafts --kind agent-draft --json -> OK, risk low, route create-promotion-task
python tools\sandbox_intake_chain.py sandbox --text -> expected exit 1, risk high, blocking markdown-link-errors
python tools\validate.py -> OK=12 WARN=0 ERROR=0
python tools\generate.py --check -> OK, generated indexes current
```

## Next recommended task

Create a follow-up task to expose `tools/conveyor.py recover` through `tools/top.py` as a top-layer advisory command. It should print diagnosis and suggested commands only; it must not auto-land, auto-ship, auto-dismiss, auto-launch, or touch Git.