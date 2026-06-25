---
id: 2026-06-24-sandbox-intake-chain-map
type: analysis-report
status: historical
owner: codex
date: 2026-06-24
mode: read-only-analysis
related: 
---

# Sandbox intake chain map

## Summary

This is a retry after a reset/hanging session. I did not assume that any lost agent result existed. I re-read the T-235, T-236, T-237, and T-238 reports, the current tool files, and the sandbox policies, then mapped the current read-only intake chain.

The useful chain already exists conceptually:

```text
external source or agent draft
-> quarantine/intake folder
-> read-only inventory
-> JSON/manifest check
-> Markdown link check
-> Python AST/static risk scan
-> one unified intake result
-> outbox report
-> Codex/human decision
-> separate promotion or execute-preflight task
```

The important correction from this recheck: the reports for T-235 and T-236 describe richer intended behavior than the current tool files expose directly. The current code still gives a usable read-only chain, but the next build task should remove this drift by adding a small orchestrator that calls the actual current tools and emits one normalized result.

## Current intake chain components

### Policy layer

- `docs/external-code-sandbox.md` defines the neutral external-code sandbox: intake, quarantine, read-only inventory, reports, workspaces, execute candidate, run plan, promotion.
- `docs/execute-sandbox-preflight.md` keeps execute off by default and requires accepted decision, inventory, isolation, secret review, network policy, limits, audit, rollback, validation, and explicit human first-run approval.
- `sandbox/drafts/README.md` adds the agent draft-code lane: write draft, static review, outbox report, Codex decision, separate promotion task. It explicitly says draft code must not be executed automatically.
- `AGENTS.md` requires agents to work by `PROTOCOL.md`, preserve other participants' work, use `queues/outbox/` for automatic work, and avoid changing accepted decisions without a new decision record.
- `PROTOCOL.md` defines the queue and append-only collaboration model: agents write results into outbox, a collector/synthesizer promotes useful results, and raw sandbox material moves upward only through controlled stages.

### Technical layer

- `tools/sandbox.py` is the current external-source intake entrypoint. It can register a source under `sandbox/inbox/`, run repo-runner inventory read-only, and write a Markdown report under `sandbox/reports/`. It already includes a Python AST section when the underlying repo-runner inventory returns `python_analysis`.
- `tools/python_analyzer.py` currently analyzes one Python file using the standard-library AST parser. It reports imports, classes, functions, and simple risk signals such as `os`, `sys`, and `open`. It does not import or execute the target file.
- `tools/sandbox_schema_validator.py` currently scans directories for files with the standard manifest filename and validates a minimal schema with `name`, `version`, `entrypoint`, and `schema_version`.
- `tools/sandbox_link_checker.py` scans Markdown files recursively, checks local links inside the scan root, reports missing and outside-root links, and returns a non-zero exit code when issues exist.
- `sandbox/drafts/README.md` defines how agent-written draft code should be placed and reviewed before any promotion.

### Drift observed during retry

- `queues/outbox/2026-06-24-t235-python-analyzer.md` describes analyzer integration with richer summary fields and `--base` style use. The current `tools/python_analyzer.py` CLI accepts a single file path, not a directory/root workflow.
- `queues/outbox/2026-06-24-t236-sandbox-schema-validator.md` describes broader driver-manifest checks. The current `tools/sandbox_schema_validator.py` performs a smaller manifest check.
- `queues/outbox/2026-06-24-t237-sandbox-link-checker.md` matches the current direction better: the current link checker has deterministic traversal, outside-root detection, line numbers, and exit codes.
- `queues/outbox/2026-06-24-t238-draft-code-sandbox.md` matches `sandbox/drafts/README.md`: draft code is proposal material, not executable project code.

This drift is not catastrophic, but it is exactly why the next automation should produce one fresh machine-readable intake result from current code instead of trusting old narrative reports.

## Unified intake result schema proposal

Future proposal, not an existing file: create a future Python orchestrator named sandbox-intake-chain under the tools folder. It should emit a JSON object with this shape:

```json
{
  "schema": "sandbox-intake-result.v1",
  "source": {
    "id": "source-or-draft-id",
    "kind": "external-source | agent-draft",
    "path": "relative sandbox source or draft folder",
    "mode": "read-only",
    "execute_allowed": false
  },
  "checks": {
    "inventory": {
      "status": "ok | warn | error | skipped",
      "tool": "tools/sandbox.py or repo-runner inventory",
      "summary": {}
    },
    "python_ast": {
      "status": "ok | warn | error | skipped",
      "tool": "tools/python_analyzer.py",
      "files_checked": 0,
      "risks": []
    },
    "schema": {
      "status": "ok | warn | error | skipped",
      "tool": "tools/sandbox_schema_validator.py",
      "manifests_checked": 0,
      "issues": []
    },
    "markdown_links": {
      "status": "ok | warn | error | skipped",
      "tool": "tools/sandbox_link_checker.py",
      "files_checked": 0,
      "issues": []
    }
  },
  "risk_summary": {
    "level": "low | medium | high | unknown",
    "execute_blocked": true,
    "blocking_reasons": []
  },
  "recommendation": {
    "route": "reject | keep-quarantine | ask-agent-revision | create-promotion-task | create-execute-preflight-task",
    "human_gate_required": true,
    "next_task_proposal": ""
  },
  "evidence": {
    "reports": [],
    "commands": []
  }
}
```

Design rules:

- Use relative paths inside the project for stable reports.
- Preserve exact tool outputs under `checks`, but normalize status and route at the top.
- Treat every draft or external source as untrusted even if static checks are clean.
- Never convert static-check success into execute permission.
- Let multiple agents produce multiple intake results, then let Codex synthesize them.

## What can be automated now without execute

These operations are safe to automate now because they read files and write reports, not execute untrusted source code:

- Run `tools/sandbox.py` intake for a known local source path.
- Run `tools/python_analyzer.py` on selected Python files.
- Run `tools/sandbox_schema_validator.py` on a sandbox draft folder.
- Run `tools/sandbox_link_checker.py` on a sandbox draft folder.
- Write a normalized Markdown or JSON summary into `queues/outbox/`.
- Use `tools/instructions.py check-report` on the outbox report.
- Use `tools/result_intake.py classify` after an agent report exists.
- Route results into `reject`, `revise`, `promote`, or `needs human decision`.

Automation should prefer short commands and explicit targets because prior PowerShell sessions have shown hangs and delayed output. Large scans should be split by folder and summarized.

## What must stay human-gated

These actions must not be automated by the intake chain:

- Running foreign or draft code.
- Installing dependencies from a sandbox source or draft.
- Enabling network access for external code.
- Changing `mode: execute` in any manifest.
- Promoting draft code into `tools/`, `drivers/`, `core/`, or `portals/` without a separate task, review, and tests.
- Accepting governance decisions in `DECISIONS.md` without human or explicitly assigned collector authority.
- Committing mixed raw sandbox draft material as mainline code.

The human-gated transition is:

```text
static intake result
-> Codex recommendation
-> human/accepted decision if execute or governance is involved
-> separate implementation or execute-preflight task
```

## Draft-code lane review flow

For agent-written code proposals, the recommended flow is:

```text
1. Agent writes draft inside its own child folder in the existing `sandbox/drafts/` area.
2. Agent includes a draft manifest based on `sandbox/templates/draft-code-manifest.template.json`.
3. Agent writes an outbox report explaining the draft, risks, and intended promotion path.
4. Observer runs read-only checks: schema, links, Python AST/static review.
5. Codex writes a synthesis: reject, request another variant, or create a promotion task.
6. If useful, promotion is implemented as a normal claimed task outside the draft lane.
7. Only promoted code is tested as project code.
```

This lets agents write real code variants while preserving the main rule: draft code is evidence and proposal material, not trusted executable project code.

## One next build task proposal for Codex

Create a new task for a read-only orchestrator.

Future proposal task title: Sandbox intake chain orchestrator.

Scope:

- Add future proposal Python file named sandbox-intake-chain in the tools folder.
- Input: one directory under the sandbox sources, sandbox inbox, or sandbox drafts area.
- Output: one JSON result and one Markdown summary in `queues/outbox/` or `sandbox/reports/`.
- Internally call or import the current logic from `tools/sandbox_schema_validator.py`, `tools/sandbox_link_checker.py`, and `tools/python_analyzer.py`.
- For Python, recursively analyze `.py` files instead of requiring the operator to pass one file at a time.
- Include explicit `execute_allowed: false`.
- Include `recommendation.route`.
- Add tests using temporary folders, including clean draft, broken Markdown link, missing manifest field, Python risky import, and outside-root link.

Acceptance checks:

```powershell
python tools\<future-test-file>.py
python tools\<future-orchestrator>.py sandbox\drafts --json
python tools\instructions.py check-report queues\outbox\<generated-report>.md
python tools\validate.py
python tools\generate.py --check
```

The future orchestrator should not replace `docs/execute-sandbox-preflight.md`. It should make the read-only preflight evidence easier to collect.

## Checks

Checks:

```powershell
Test-Path -LiteralPath "queues\outbox\2026-06-24-sandbox-intake-chain-map.md"
python tools\python_analyzer.py tools\sandbox.py
python tools\sandbox_schema_validator.py sandbox
python tools\sandbox_link_checker.py sandbox\drafts --json
python tools\sandbox.py list
```

Observed before writing this report:

- Target report file did not exist before retry.
- `tools/python_analyzer.py` parsed `tools/sandbox.py` and reported functions plus static risk signals without executing target code.
- `tools/sandbox_schema_validator.py sandbox` returned 0 scanned manifests and no issues.
- `tools/sandbox_link_checker.py sandbox\drafts --json` returned 1 Markdown file scanned, 0 issues, `ok: true`.
- `tools/sandbox.py list` returned `demo-fixtures`.

Post-write checks to run:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-sandbox-intake-chain-map.md
git status --short --untracked-files=all
```

## Applied instructions

Applied instructions evidence:

- `AGENTS.md`: the work used `queues/outbox/` for an automatic analysis result, did not delete other agents' messages, did not change accepted decisions, and did not edit generated files.
- `PROTOCOL.md`: this report follows the queue model: one outbox artifact for synthesis, not direct mutation of shared status or decision files.
- `docs/external-code-sandbox.md`: the map preserves intake, quarantine, read-only inventory, reporting, and promotion as separate stages.
- `docs/execute-sandbox-preflight.md`: the map keeps execute blocked until accepted decision, isolation, limits, audit, rollback, validation, and human first-run approval exist.
- `sandbox/drafts/README.md`: the draft-code lane is treated as no-execute proposal material with review before promotion.

Checks:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-24-sandbox-intake-chain-map.md
```
