---
status: historical
---
# UX/safety review: `top.py conveyor-recover`

- Date: 2026-06-24
- Author: codex
- Scope: `python tools/top.py conveyor-recover [--json] [--limit N]`
- Mode: read-only/outbox-only review

## Summary

`tools/conveyor.py` already has a read-only `recover` diagnostic path. It returns `schema: conveyor_recover.v1`, includes `mutates: False`, checks landed outputs, missing output paths, stale heartbeat, refill deficit, and unreferenced outbox reports, and supports `--json` plus `--limit`.

The current top layer does not expose `conveyor-recover`: `tools/top.py` has `conveyor` for status and `process-landed`, but no parser entry, button entry, or command handler for `conveyor-recover`. This is the main UX gap. The top command should be a thin advisory wrapper over `tools/conveyor.py recover`, not a new recovery engine.

## Human UX

Recommended commands:

```powershell
python tools/top.py conveyor-recover
python tools/top.py conveyor-recover --limit 5
```

The human output should look like a diagnostic panel, not an action runner:

```text
CONVEYOR RECOVER - read-only recovery diagnostics
read-only: no conveyor ledger changes, no Git changes, no land/ship/dismiss/launch/tick executed

state: inflight=2 landed=0 deficit=0 healthy=true
checked outbox reports: 138

[info] unreferenced-outbox-reports
  count: 125
  sample:
    - queues/outbox/example.md
  suggested manual next step: if a report belongs to an inflight workflow, land that workflow with --output; otherwise leave it as historical evidence
```

Human-facing wording rules:

- Put `read-only` and `no Git changes` near the top, before findings.
- Label every command-like suggestion as `suggested manual next step`, not `run`, `execute`, `fixing`, or `recovering`.
- If suggestions mention `land`, `ship`, `dismiss`, `launch`, or `tick`, make clear that `top.py conveyor-recover` did not execute them.
- Use calm severity labels: `action` means "needs human/agent follow-up", not that the command mutated anything; `info` means advisory context.
- Keep `--limit N` scoped to samples only. It must not change the actual counts, ledger, target, heartbeat, or outbox state.

## Agent UX

Recommended command:

```powershell
python tools/top.py conveyor-recover --json --limit 10
```

The JSON path should be clean machine output with no `_run()` banner, no echoed command, and no trailing `EXIT N` text. It can either pass through `conveyor_recover.v1` unchanged or wrap it in a top schema, but the stable fields should be present:

```json
{
  "schema": "top_conveyor_recover.v1",
  "mutates": false,
  "source_schema": "conveyor_recover.v1",
  "assessment": {},
  "findings": [],
  "checked_outbox_reports": 0
}
```

Agent-facing rules:

- `mutates: false` is mandatory.
- Include enough structured data for routing: `kind`, `severity`, `workflow`, `label`, `output`, `count`, `sample`, and `suggestion` when available.
- Do not encode suggested actions as executable task plans. They are diagnostics and recommendations only.
- Do not call `git status`, `git diff`, `commit_lock.py`, `pipeline.py take/next`, or any conveyor mutator from this command.
- Do not include side-effect flags such as `--run`, `--fix`, `--land`, `--ship`, `--dismiss`, `--launch`, or `--tick` in the top command.

## Wording and exit-code rules

Recommended exit-code contract:

| Case | Exit code | Notes |
|---|---:|---|
| Diagnostics produced, no findings | 0 | Advisory success. |
| Diagnostics produced, findings exist | 0 | Findings are not a hard gate by default. |
| Invalid arguments, invalid `--limit` | 2 | Parser/user input error. |
| Child command timeout | 124 | For `--json`, emit a JSON error object. |
| Unexpected child failure | Child code or 1 | For `--json`, keep stderr separate or emit structured error JSON. |

Do not reuse `conveyor status` semantics where unhealthy state can return nonzero. `conveyor-recover` is a diagnostic/advisory command, like top-layer assurance in non-strict mode. If a future gate is needed, it should be a separate explicit `--strict` decision, not default behavior.

Recommended non-JSON error wording:

```text
CONVEYOR RECOVER - error
read-only: no conveyor ledger changes and no Git changes were made
error: <reason>
```

Recommended JSON error shape:

```json
{
  "schema": "top_conveyor_recover_error.v1",
  "mutates": false,
  "error": "timeout",
  "command": "python tools/conveyor.py recover --json --limit 10"
}
```

## Safety review

The safe implementation shape in `tools/top.py` is:

- Add a `conveyor-recover` button row with `effect: read-only`.
- Add `cmd_conveyor_recover(args)` that invokes only `python tools/conveyor.py recover`.
- Add parser flags `--json` and `--limit`; optionally reject negative `--limit` at parser level.
- For `--json`, capture and print only the child JSON or structured top error JSON.
- For text output, either print raw `render_recover()` output or add a small top header/footer that preserves the read-only warning.
- Never call `_tool("conveyor.py", "land"|"ship"|"dismiss"|"launch"|"tick")`.
- Never call Git from this command.

The low-level `recover` suggestions currently include manual commands such as `land`, `dismiss`, and `tick`. That is acceptable only because they are suggestions in the returned diagnostics. The top wrapper should not turn those suggestions into execution.

## Current observed state

- `tools/conveyor.py recover` exists and behaved as advisory JSON in the local check.
- `tools/top.py conveyor-recover` is currently not registered; the top parser reports `invalid choice: 'conveyor-recover'`.
- `docs/top-layer-command-groups.md` already establishes the pattern that top commands should clearly mark read-only vs writing effects.
- `docs/friction-playbook.md` supports this design: detectors should start read-only/dry-by-default, and automatic fixes need a separate decision.

## Applied instructions

- User instruction: strict read-only/outbox-only; write only this report.
- `AGENTS.md`: use `queues/outbox/` for automatic-agent results; do not delete messages or rewrite discussion history.
- `PROTOCOL.md`: keep outputs in queue/outbox and avoid changing shared/final decision files.
- `docs/top-layer-command-groups.md`: top-layer commands should be simple scenario buttons with explicit side-effect boundaries.
- `docs/friction-playbook.md`: repeated-problem tools should start read-only/dry-by-default; automatic correction requires separate approval/decision.

Checks:

- Read `tools/top.py`.
- Read `tools/conveyor.py`.
- Read `docs/friction-playbook.md`.
- Read `docs/top-layer-command-groups.md`.
- Searched relevant markers with `rg -n "conveyor-recover|cmd_conveyor|process-landed|recover|render_recover|exit|return 0|return 1|return 2|mutates|land|ship|dismiss|launch|tick|Git|read-only|strict" ...`.
- Confirmed this report file did not exist before writing: `Test-Path queues/outbox/2026-06-24-top-conveyor-recover-ux-review.md` returned `False`.
- Ran `$env:PYTHONDONTWRITEBYTECODE='1'; python tools/conveyor.py recover --json --limit 2`: exit 0, `mutates: false`, healthy assessment, info finding for unreferenced outbox reports.
- Ran `$env:PYTHONDONTWRITEBYTECODE='1'; python tools/top.py conveyor-recover --help`: current top parser reports invalid choice, so the top-level command is not yet exposed.
- Did not run `land`, `ship`, `dismiss`, `launch`, `tick`, or any Git command.
