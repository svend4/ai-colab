---
id: 2026-06-24-halley-next-agent-work-queue
type: workflow-review
status: historical
owner: halley
date: 2026-06-24
mode: read-only/outbox-only
related: 
---

# Halley next agent work queue after T-237

## Summary

The formal backlog is almost empty after T-237. During this review, `tasks/T-237.md` moved from unfinished to `status: done`, while the earlier `PIPELINE.md` snapshot still listed T-237 as ready. Treat `PIPELINE.md` as stale until the main integrator refreshes it.

The next useful work should not start with broad code edits. The safest conveyor refill is two outbox-only reviews: one sandbox-intake chain map and one unused-advice audit. Code/build follow-ups exist, but they should wait for Codex or a worktree because they touch `tools/` and may require generated-file refreshes.

## Current backlog observations

- `tasks/T-237.md` is now `status: done`, and `queues/done/T-237.done.md` exists, but `queues/outbox/2026-06-24-halley-t237-link-checker-review.md` says the implementation still needed tests, non-zero broken-link exit codes, path-escape protection, line numbers, deterministic traversal, and state reconciliation.
- `PIPELINE.md` showed T-237 as ready when read, so it is not a reliable current queue source until `python tools/pipeline.py snapshot` is run by the main integrator.
- `queues/outbox/2026-06-24-t236-sandbox-schema-validator.md` recommends using the same read-only scanner, structured report, JSON mode, and `drivers/test_tmp.py` test pattern for T-237.
- `queues/outbox/2026-06-24-t235-python-analyzer.md` leaves two safe follow-ups: compact JSON export for sandbox intake and later risk-rule improvements such as alias tracking.
- `queues/outbox/2026-06-24-t233-cli-paths-readonly-utils.md` and `queues/outbox/2026-06-24-t234-result-intake-external-code.md` both report an unrelated metadata gap: `tools/edges.py` and `tools/test_edges.py` need D-Cards.
- `queues/outbox/2026-06-24-pipeline-reconciliation-cleanup-report.md` says `tasks/T-020.md`, `tasks/T-174.md`, and `tasks/T-208.md` have blocker history, but current front matter shows them as done. Their `next` fields still describe work that needs external input or human/governance gates.
- `queues/outbox/2026-06-24-lagrange-centralization-information-plan.md` provides the best low-conflict refill pattern: outbox-only reports with exact write scopes, then Codex verifies and turns selected items into build tasks.

## Top 8 candidate tasks for agents

| Rank | Candidate | Why now | Owner type | Mode | Exact allowed write scope | Forbidden files | Verification commands | Risk |
|---:|---|---|---|---|---|---|---|---|
| 1 | Sandbox intake chain map | T-235, T-236, and T-237 form a read-only external-code intake chain, but there is no single map of how AST, schema, and link checks should appear in one intake result. | researcher or reviewer | read-only/outbox-only | one new file: `queues/outbox/2026-06-24-sandbox-intake-chain-map.md` | `tools/sandbox.py`; `tools/sandbox_link_checker.py`; `tools/sandbox_schema_validator.py`; `tools/python_analyzer.py`; `TASKS.md`; `index.json`; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python tools/instructions.py check-report queues/outbox/2026-06-24-sandbox-intake-chain-map.md`; `python tools/result_intake.py classify queues/outbox/2026-06-24-sandbox-intake-chain-map.md --json` | low |
| 2 | Unused advice audit | `docs/friction-ledger.md` and `docs/top-layer-command-groups.md` contain many recommendations; Lagrange explicitly identified unused advice as safe next work. | reviewer | read-only/outbox-only | one new file: `queues/outbox/2026-06-24-unused-advice-audit.md` | `docs/friction-ledger.md`; `docs/top-layer-command-groups.md`; `docs/workflow-conveyor-policy.md`; `TASKS.md`; `index.json`; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python tools/instructions.py check-report queues/outbox/2026-06-24-unused-advice-audit.md`; `python tools/result_intake.py classify queues/outbox/2026-06-24-unused-advice-audit.md --json` | low |
| 3 | T-237 post-closeout verifier | T-237 is now marked done, but Halley review recorded concrete closeout criteria. A second read-only report can check whether those criteria were actually satisfied without touching implementation files. | reviewer | read-only/outbox-only | one new file: `queues/outbox/2026-06-24-t237-post-closeout-verifier.md` | `tools/sandbox_link_checker.py`; `tools/test_sandbox_link_checker.py`; `tasks/T-237.md`; `TASKS.md`; `index.json`; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python tools/instructions.py check-report queues/outbox/2026-06-24-t237-post-closeout-verifier.md`; `python tools/result_intake.py classify queues/outbox/2026-06-24-t237-post-closeout-verifier.md --json` | low |
| 4 | D-Card gap plan for edges | Two separate fresh reports mention missing D-Cards for `tools/edges.py` and `tools/test_edges.py`; a tiny plan can define exact edit/test scope before any build worker touches `tools/`. | reviewer | read-only/outbox-only | one new file: `queues/outbox/2026-06-24-edges-dcard-gap-plan.md` | `tools/edges.py`; `tools/test_edges.py`; `docs/dcard_index.md`; `TASKS.md`; `index.json`; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python tools/instructions.py check-report queues/outbox/2026-06-24-edges-dcard-gap-plan.md`; `python tools/result_intake.py classify queues/outbox/2026-06-24-edges-dcard-gap-plan.md --json` | low |
| 5 | Next-action button design | Lagrange suggests a read-only top-layer button for next actions. This should be specified before any `tools/top.py` implementation. | Lagrange or reviewer | read-only/outbox-only | one new file: `queues/outbox/2026-06-24-next-action-button-design.md` | `tools/top.py`; `tools/conveyor.py`; `tools/result_intake.py`; `docs/top-layer-command-groups.md`; `TASKS.md`; `index.json`; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python tools/instructions.py check-report queues/outbox/2026-06-24-next-action-button-design.md`; `python tools/result_intake.py classify queues/outbox/2026-06-24-next-action-button-design.md --json` | low |
| 6 | Cauldron lane picklist | `tasks/T-221.md` and `tasks/T-222.md` are done, but their `next` fields still describe choosing lane A and lane B items. A review can produce the next ratify-build/divergence-detail picklist. | synthesis-agent | read-only/outbox-only | one new file: `queues/outbox/2026-06-24-cauldron-next-lanes-review.md` | `docs/cauldron-two-lane-board-2026-06-24.md`; `docs/architecture-core-documents-synthesis-2026-06-24.md`; `streams/architecture-core/divergence.md`; `TASKS.md`; `index.json`; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python tools/instructions.py check-report queues/outbox/2026-06-24-cauldron-next-lanes-review.md`; `python tools/result_intake.py classify queues/outbox/2026-06-24-cauldron-next-lanes-review.md --json` | low |
| 7 | Sandbox intake JSON export build | T-235 recommends a compact JSON export command for sandbox intake. This is likely useful, but it touches code and tests. | Codex or worker in worktree | build/worktree | `tools/sandbox.py`; `tools/test_sandbox.py`; one new file: `queues/outbox/2026-06-24-sandbox-intake-json-export.md` | `TASKS.md` unless claimed; `index.json` unless final integrator regenerates; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python -m py_compile tools/sandbox.py tools/test_sandbox.py`; `python tools/test_sandbox.py`; `python tools/validate.py`; `python tools/generate.py --check`; `python tools/instructions.py check-report queues/outbox/2026-06-24-sandbox-intake-json-export.md` | medium |
| 8 | Execute no-execute gate review | `queues/outbox/2026-06-24-execute-track-safety-recheck.md` keeps the execute umbrella gated. A read-only review can identify any accidental execute surface before human approval. | reviewer | read-only/outbox-only | one new file: `queues/outbox/2026-06-24-execute-no-execute-gate-review.md` | `tools/sandbox_runner.py`; `tools/execute_preflight.py`; `tools/execute_human_gate.py`; `tasks/T-208.md`; `tasks/T-217.md`; `TASKS.md`; `index.json`; `PIPELINE.md`; `system-capabilities.json`; `logs/heartbeat.json`; `logs/pipeline.json` | `python tools/instructions.py check-report queues/outbox/2026-06-24-execute-no-execute-gate-review.md`; `python tools/result_intake.py classify queues/outbox/2026-06-24-execute-no-execute-gate-review.md --json` | low for review; high if converted to execute |

## Launch Immediately In Parallel

1. Sandbox intake chain map: write only `queues/outbox/2026-06-24-sandbox-intake-chain-map.md`.
2. Unused advice audit: write only `queues/outbox/2026-06-24-unused-advice-audit.md`.

These two can run together because they are read-only and write different new outbox files. They do not require current Codex T-237 implementation files and do not require `TASKS.md`, `index.json`, `PIPELINE.md`, `system-capabilities.json`, `logs/heartbeat.json`, or `logs/pipeline.json`.

## Must Wait For Codex Or Human Approval

- T-237 implementation hardening must wait for Codex/integrator status, because `tasks/T-237.md` changed during this review and the implementation files are current main work.
- D-Card edits in `tools/edges.py` and `tools/test_edges.py` should wait for Codex or a worktree. The outbox-only gap plan can run now.
- Sandbox intake JSON export should wait for Codex or a worktree because it edits `tools/sandbox.py` and `tools/test_sandbox.py`.
- Any change that regenerates `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `STATUS.md`, `index.json`, `system-capabilities.json`, or `PIPELINE.md` should wait for the main integrator.
- Any execute-sandbox run or `mode: execute` enablement must wait for human approval and the gates described in `queues/outbox/2026-06-24-execute-track-safety-recheck.md`.
- Work related to `tasks/T-020.md` must wait for a human-provided external source path, archive, or snapshot.

## Checks

Exact commands to verify this report:

```powershell
python tools/instructions.py check-report queues/outbox/2026-06-24-halley-next-agent-work-queue.md
python tools/result_intake.py classify queues/outbox/2026-06-24-halley-next-agent-work-queue.md --json
python -c "import pathlib,json; ids={'T-020','T-174','T-202','T-208','T-221','T-222','T-237'}; rows=[]; [rows.append({'file':str(p).replace('\\','/'),'id':d.get('id','').strip(),'status':d.get('status','').strip(),'next':d.get('next','').strip()[:120]}) for p in sorted(pathlib.Path('tasks').glob('T-*.md')) for lines in [p.read_text(encoding='utf-8',errors='replace').splitlines()] for end in ([lines.index('---',1)] if len(lines)>1 and lines[0]=='---' and '---' in lines[1:] else []) for d in [dict((line.split(':',1)[0].strip(), line.split(':',1)[1].strip()) for line in lines[1:end] if ':' in line)] if d.get('id','').strip() in ids]; print(json.dumps(rows, ensure_ascii=True, indent=2))"
rg "T-237|sandbox|D-Card|missing D-Card|Next recommendations|should be handled separately" queues/outbox -g "2026-06-24-*.md"
```

## Applied instructions

- `AGENTS.md:7` says to work by `PROTOCOL.md`; this report follows the queue/outbox workflow and does not edit task source files.
- `AGENTS.md:12` says automatic work results should use `queues/outbox/`; this task wrote only `queues/outbox/2026-06-24-halley-next-agent-work-queue.md`.
- `PROTOCOL.md:42` says one message equals one file; this report is a single new outbox file.
- `PROTOCOL.md:94` defines `queues/outbox/` as prepared results not yet moved into main files; this report proposes work, it does not apply decisions.
- `PROTOCOL.md:98` says agents use pipeline status, write outbox/profile-topic results, and humans or the main agent move important content into main files; this report leaves implementation to Codex/integrator.
- `PROTOCOL.md:190` warns against broad `git add -A` in a dirty workspace; this report requests no git, no commit, and no generated-file updates.
- User instruction for this run: read-only/outbox-only, no code edits, no `TASKS.md`, no `index.json`, no `PIPELINE.md`, no logs, no generated files, no git.

Checks:

- `python tools/instructions.py check-report queues/outbox/2026-06-24-halley-next-agent-work-queue.md`
- `python tools/result_intake.py classify queues/outbox/2026-06-24-halley-next-agent-work-queue.md --json`
