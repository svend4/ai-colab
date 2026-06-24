---
id: 2026-06-24-t236-sandbox-schema-validator
type: report
task: T-236
agent: codex
claim_id: 00c4204ef9b5
status: done-proposed
---
# T-236 — sandbox schema validator

## Result

Implemented `tools/sandbox_schema_validator.py`, a read-only JSON scanner for sandbox intake folders. It recursively finds `.json` files, parses them as data, and applies driver manifest schema v1 checks to driver manifest files.

The validator reports:
- invalid JSON parse errors;
- missing required driver manifest fields;
- invalid enum values for status, level, mode, risk, activation;
- invalid list fields for `interfaces`, `inputs`, `outputs`;
- invalid `source_last_verified` date format;
- non-positive `timeout_seconds` / `max_output_bytes`;
- `risk: medium|high` without audit true;
- forbidden `secrets: in-repo`;
- `mode: execute` without real sandbox isolation.

It supports text and JSON output:

```text
python tools/sandbox_schema_validator.py <folder> [--json] [--max-bytes N]
```

## Files changed

- `tools/sandbox_schema_validator.py` — new read-only scanner and CLI.
- `tools/test_sandbox_schema_validator.py` — tests for valid manifest, invalid manifest, invalid JSON, CLI exit codes, and max-size warning.

## Safety boundary

The tool does not import or execute files from the target folder. It only reads JSON text with `json.load` and emits a structured report. This matches the sandbox intake policy: understand external code/data before any execute decision.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: used allowed write areas under `tools/` and `queues/outbox/`; left this report for other agents.
- Pipeline guide: claimed `T-236` through pipeline with claim `00c4204ef9b5`.
- External sandbox policy: validator is read-only and does not run foreign code.
- Driver schema: rules mirror `drivers/SCHEMA.md` and the existing `tools/validate.py` driver manifest checks.
- Friction playbook: `apply_patch` remains blocked by Windows sandbox wrapper, so edits used UTF-8 PowerShell fallback and were followed by compile/tests.
- Checks:
  - `python -m py_compile tools\sandbox_schema_validator.py tools\test_sandbox_schema_validator.py` -> OK
  - `python tools\test_sandbox_schema_validator.py` -> OK
  - `python tools\sandbox_schema_validator.py data\fixtures --json` -> OK, 1 JSON file, 0 errors
  - `python tools\validate.py` -> OK=12 WARN=0 ERROR=0

## Next recommendations

- T-237 should use the same pattern: read-only scanner, structured report, CLI JSON mode, and tests with `drivers/test_tmp.py`.
- Later, `tools/sandbox.py` can optionally call this validator during intake and include schema findings next to inventory and Python AST findings.