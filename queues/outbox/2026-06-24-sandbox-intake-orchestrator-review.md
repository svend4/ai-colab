---
id: 2026-06-24-sandbox-intake-orchestrator-review
type: implementation-risk-review
status: proposed
owner: codex
date: 2026-06-24
mode: read-only-outbox-only
related:
  - queues/outbox/2026-06-24-sandbox-intake-chain-map.md
  - queues/outbox/2026-06-24-agent-cell-synthesis.md
  - tools/sandbox.py
  - tools/python_analyzer.py
  - tools/sandbox_schema_validator.py
  - tools/sandbox_link_checker.py
  - tools/test_sandbox.py
  - tools/test_python_analyzer.py
  - tools/test_sandbox_schema_validator.py
  - tools/test_sandbox_link_checker.py
  - sandbox/drafts/README.md
  - AGENTS.md
  - PROTOCOL.md
---

# Sandbox intake orchestrator review

## Summary

This is a read-only implementation-risk review for a future sandbox intake chain orchestrator. I did not implement the orchestrator and did not edit code, tasks, generated files, logs, or git state.

The current direction is sound: a future orchestrator should collect read-only evidence from sandbox intake, Python AST analysis, JSON manifest validation, Markdown link checking, and the draft-code lane, then emit one normalized no-execute result. The implementation risk is higher than it looks because the current tree shows drift between tests/reports and some tool APIs.

Primary recommendation: do not start the orchestrator as a broad integration task yet. First stabilize the contracts of `tools/python_analyzer.py` and `tools/sandbox_schema_validator.py`, then make `tools/sandbox.py` consume those contracts consistently. After that, add a thin read-only orchestrator.

## Current tool capabilities

`tools/sandbox.py` is the current external-source read-only intake entrypoint. It registers a source under `sandbox/inbox/`, runs repo-runner inventory, writes an inventory report under `sandbox/reports/`, and explicitly says target code was not executed. Its report can include a Python semantic analysis section when inventory returns `python_analysis`.

`tools/python_analyzer.py` currently exposes a simple file-oriented CLI and function shape in the file content read during this review. It parses one Python file with `ast`, reports imports, classes, functions, and simple risk strings. The tests expect a richer contract with `analyze_source`, `analyze_file`, structured imports/classes/functions/risks, `summary`, `syntax_ok`, `base_dir`, and `--json`.

`tools/sandbox_schema_validator.py` currently exposes a simple manifest validator in the file content read during this review. It validates only standard manifest filenames for a small required key set. The tests expect a richer `scan` API, all-JSON scanning, summary counts, issue codes, manifest schema rules, max byte warnings, and CLI exit codes.

`tools/sandbox_link_checker.py` is the strongest current component. It scans Markdown recursively, sorts traversal deterministically, strips anchors/query strings, ignores external links and same-document anchors, detects outside-root traversal, reports line numbers, supports JSON/text output, and returns non-zero exit codes for broken links.

`sandbox/drafts/README.md` defines a useful no-execute draft-code lane: write draft, static review, outbox report, Codex decision, separate promotion task. It explicitly forbids automatic execution, dependency installation, secret storage, and direct promotion into main project code.

## Drift/gaps

The biggest gap is contract drift:

1. `tools/test_python_analyzer.py` currently fails against `tools/python_analyzer.py` with missing `analyze_source`.
2. `tools/test_sandbox_schema_validator.py` currently fails against `tools/sandbox_schema_validator.py` with missing `scan`.
3. `tools/test_sandbox.py` currently fails in the Python AST intake report case because the report includes Python AST rows but the expected structured values are not present.
4. `tools/test_sandbox_link_checker.py` passes and can be treated as the stable reference component.

This means the future orchestrator should not depend on old narrative reports alone. It should depend on current tested APIs, and those APIs need to be repaired before orchestration.

There is also a classification gap already observed in related reports: `tools/result_intake.py` may classify governance/synthesis reports containing sandbox vocabulary as external-code. That does not block a read-only orchestrator, but it means orchestrator output should include explicit `type`, `mode`, `execute_allowed: false`, and `recommendation.route` fields to reduce ambiguity.

## Minimal orchestrator scope

The minimal safe orchestrator should be thin and read-only:

1. Input: one directory inside `sandbox/`, preferably `sandbox/drafts/`, `sandbox/inbox/`, or a registered source folder.
2. Guard: reject targets outside the workspace sandbox root.
3. Run or import the stabilized capabilities from `tools/sandbox_schema_validator.py`, `tools/sandbox_link_checker.py`, and `tools/python_analyzer.py`.
4. Recursively analyze Python files, but only by reading and parsing AST, never importing or executing them.
5. Emit one normalized JSON object with source, checks, risk summary, execute permission set to false, and recommendation route.
6. Optionally emit a Markdown outbox report that includes evidence and exact commands.
7. Never promote code, never run draft code, never install dependencies, never write to `tools/`, `drivers/`, `core/`, `portals/`, `TASKS.md`, `DECISIONS.md`, or git.

The first implementation should not call `tools/sandbox.py intake` automatically unless the input is a trusted local path selected by Codex or the user. For draft-code review, direct static checks over `sandbox/drafts/<draft-id>` are enough.

## Test cases

Minimum tests before closing the future orchestrator task:

1. Clean draft folder: manifest, README, one Python file, one valid Markdown link; result should be ok/low risk and execute blocked.
2. Broken Markdown link: result should include link checker issue and route to ask-agent-revision.
3. Outside-root Markdown traversal: result should include outside-root issue and route to reject or ask-agent-revision.
4. Invalid JSON manifest: result should include schema issue and non-ok schema status.
5. Python risky import/call: result should include AST risk but still no execution.
6. Python syntax error: result should be data, not a crash.
7. Target outside sandbox: command should return usage/error code and not scan host filesystem.
8. Missing directory: command should return usage/error code.
9. No Markdown/no Python/no JSON: result should be valid with skipped checks, not failure by default.
10. Deterministic output: same fixture should produce stable sorted file order.

## Risks

The main implementation risk is building orchestration over unstable APIs. Fix the failing analyzer/schema/sandbox tests first, otherwise the orchestrator will either duplicate logic or encode accidental behavior.

The second risk is scope creep. A read-only intake orchestrator must not become execute preflight, promotion gate, package installer, or automatic commit helper. It should collect evidence only.

The third risk is false confidence. Static checks can reduce unknowns, but clean static output does not make external or draft code safe to execute.

The fourth risk is report drift. If the orchestrator writes Markdown only, later agents may parse prose inconsistently. Prefer JSON as the primary result and Markdown as a human companion.

The fifth risk is path safety. The orchestrator must enforce a sandbox root and preserve relative paths in output, especially when handling links, manifests, and Python files.

## Exact checks

Checks observed during this review:

```powershell
python tools\test_python_analyzer.py
# FAIL: AttributeError: module 'python_analyzer' has no attribute 'analyze_source'

python tools\test_sandbox_schema_validator.py
# FAIL: AttributeError: module 'sandbox_schema_validator' has no attribute 'scan'

python tools\test_sandbox_link_checker.py
# OK: all tests passed

python tools\test_sandbox.py
# FAIL: python AST intake report does not contain the expected structured summary values
```

Recommended checks before implementing the orchestrator:

```powershell
python tools\test_python_analyzer.py
python tools\test_sandbox_schema_validator.py
python tools\test_sandbox_link_checker.py
python tools\test_sandbox.py
python tools\validate.py
python tools\generate.py --check
```

Recommended checks after writing this review:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-sandbox-intake-orchestrator-review.md
git status --short --untracked-files=all
```

## Applied instructions

AGENTS.md evidence:

- worked by `PROTOCOL.md`;
- did not delete other agents' messages;
- did not rewrite history;
- did not change accepted decisions;
- wrote exactly one automatic work artifact into `queues/outbox/`;
- kept this result as `status: proposed`;
- did not edit code, `TASKS.md`, `index.json`, `PIPELINE.md`, logs, generated files, or git.

PROTOCOL.md evidence:

- followed the queue model by writing a prepared review into `queues/outbox/`;
- used append-only collaboration by creating a new report instead of editing prior worker reports;
- treated this as reviewer work, not final decision authority;
- kept Git commit and integration as later steps outside this read-only/outbox-only run;
- preserved the sandbox rule that raw or draft material must not move upward without controlled review and promotion.

Checks:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-sandbox-intake-orchestrator-review.md
```
