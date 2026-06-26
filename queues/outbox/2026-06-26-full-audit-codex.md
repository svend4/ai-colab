---
type: audit
title: Full audit - Codex - 2026-06-26
date: 2026-06-26
author: codex
status: outbox
scope:
  - workspace health
  - generated indexes
  - tests
  - queues
  - residual risk
---

# Full audit — Codex — 2026-06-26

## Scope

Full workspace audit requested directly in chat. I treated this as a read-mostly audit of project health, governance state, queues, generated indexes, tests, and current working tree.

## Checks run

- `git status --short`
- `python tools\validate.py`
- `python tools\generate.py --check`
- `python tools\pipeline.py status`
- `python tools\top.py health`
- `python tools\friction.py status`
- `python tools\stream.py check`
- `python tools\drift_check.py`
- `python tools\metrics.py --json`
- `python tools\assurance.py all`
- `python tools\test_thread.py`
- `python -m pytest tools drivers`
- Script fallback over `tools/**/test_*.py` and `drivers/**/test_*.py`
- Read-only local audit scripts: `_audit_links.py`, `_audit_topics_diff.py`, `_audit_fm.py`

## Current green checks

- Canon validator is green: `OK=12 WARN=0 ERROR=0`.
- Generated navigation is current now: `generate.py --check` reports all OK, `index.json` current, 62 topics in navigation.
- Drift layer is green now: `OK: дрейфа не обнаружено`.
- Pipeline reports 0 active work items and 1 ready task: `T-264`.
- Stream lifecycle check is clean.
- Driver catalog and capabilities checks are current.
- Focused `thread.py` test passes: `TESTS OK thread: init/add-message/add-output/status`.

## Findings

### P1 — Broad test layer is not reliable as a release gate

`pytest` is not installed in the current venv, so `python -m pytest tools drivers` fails immediately with `No module named pytest`.

Fallback script execution over 122 `test_*.py` files produced:

- passed: 87
- failed: 31
- timeout: 4
- duration: 1434.2 seconds

Observed failing files included `tools/test_agent_queue_fencing.py`, `tools/test_autolink.py`, `tools/test_canon_index.py`, `tools/test_capabilities.py`, `tools/test_code_pyramid.py`, `tools/test_consensus_by_meaning.py`, `tools/test_decay.py`, `tools/test_divergence_detail.py`, `tools/test_drivers_catalog.py`, `tools/test_edges.py`, `tools/test_folder_index.py`, `tools/test_friction.py`, `tools/test_git_reconcile.py`, `tools/test_header.py`, `tools/test_heading_check.py`, `tools/test_independence_measure.py`, `tools/test_instruction_trace.py`, `tools/test_layer_check.py`, `tools/test_maturity.py`, `tools/test_metrics.py`, `tools/test_oracle_quorum.py`, `tools/test_portals.py`, `tools/test_provenance.py`, `tools/test_red_team_gate.py`, `tools/test_reflect_ingest.py`, `tools/test_ripeness_gate.py`, `tools/test_seal_verify.py`, `tools/test_synthesis_helper.py`, `tools/test_thread_runner.py`, `tools/test_two_track.py`, `tools/test_view.py`.

Timeouts: `tools/test_blocks.py`, `tools/test_cohort.py`, `tools/test_onboard.py`, `tools/test_top.py`.

Interpretation: this is not the same as an official pytest result, but it is enough to show there is no clean, documented, fast full-test entrypoint.

### P1 — Working tree is mixed and should not be bulk-staged

Final status still includes modified shared/generated files and active tool changes:

- `STATUS.md`
- `board.md`
- `index.json`
- `indexes/topics.md`
- `tools/crdt_merge.py`
- `tools/test_crdt_merge.py`
- `tools/view.py`
- `tools/test_view.py`

Also untracked: `_audit_fm.py`, `_audit_links.py`, `_audit_topics_diff.py`, `_picks.json`, old reports, sandbox imports, and new topic/outbox files.

Friction recommendation remains effectively: selective-add only; do not use `git add -A`.

### P1 — `T-264` is status-drifted

Pipeline reports `T-264` as ready/todo. The task body says Stage A was implemented by Codex and lists `tools/thread.py` plus `tools/test_thread.py`. Focused test passes. This should be reconciled: either close/review `T-264`, or split remaining hardening into a new follow-up and update `T-264` status.

### P2 — 13 top-level topic files are on disk but absent from `index.json`

`_audit_topics_diff.py` found 75 top-level `topics/*.md` files on disk, but 62 indexed. The 13 missing all lack `title` front-matter, so `generate.py` intentionally omits them:

- `topics/adoption-statistics-2026-06-23.md`
- `topics/alchemy_synthesis_20260625_144041.md`
- `topics/alpha2-to-alpha3-roadmap-2026-06-24.md`
- `topics/drivers-subsystem-state-2026-06-23.md`
- `topics/information-refactoring-cycle-1-2026-06-25.md`
- `topics/information-refactoring-cycle-2-2026-06-25.md`
- `topics/information-refactoring-cycle-3-2026-06-25.md`
- `topics/information-refactoring-question-tree-2026-06-25.md`
- `topics/new-problems-2026-06-23.md`
- `topics/parallel-forks-history-2026-06-22.md`
- `topics/q016-assurance-state-2026-06-23.md`
- `topics/solver-report-2026-06-23.md`
- `topics/text-extract-deps-evidence-2026-06-21.md`

### P2 — Link audit has many sandbox/import false positives, but real checker policy is unclear

`_audit_links.py` scanned 1165 markdown files, checked 1522 local link targets, and reported 489 broken targets. Most visible cases are under imported sandbox material (`sandbox/inbox/self_reflection_global`, `sandbox/tvcp_fetched`) where relative links point to source repo layout that was flattened or partially imported.

This should not become a hard gate without sandbox-aware exclusions, but it is a useful signal for imported corpus hygiene.

### P2 — Metadata soft-check reports 50 missing/invalid D-Cards

`top.py health` metadata soft-check reports 50 files missing valid D-Cards, mostly newer tools and tests. It is warn-only today, but it is growing enough to make D-Card coverage unreliable as a navigation layer.

### P2 — Assurance reports 4 evidence findings

`assurance.py all` verdict: `ATTENTION`, 4 findings, 1 high/medium:

- `T-247`: weak evidence, missing `PROTOCOL.md`.
- `T-240`, `T-238`, `T-237`: formal evidence, missing task-specific links.

### P3 — Queue metrics count legacy artifacts differently than pipeline

`pipeline.py status` reports 0 active claims. `metrics.py --json` still reports `queue.claimed = 1`, because `queues/claimed/T-202.claim.md` remains as a legacy file. `queues/failed` contains `T-184.failed.md` and `T-185.failed.md`. This is not currently blocking, but the two views should be clarified in docs or metrics.

### P3 — Root-level audit helper scripts are untracked clutter

`_audit_fm.py`, `_audit_links.py`, and `_audit_topics_diff.py` are useful read-only diagnostics, but they are untracked in repository root. If kept, move them under `tools/` with D-Cards/tests or under `tmp-work/`/`queues/outbox/` as ephemeral evidence.

## Recommended next actions

1. Reconcile `T-264`: close/review it if Stage A is done, and create follow-up tasks for hardening.
2. Define one supported full-test command. Either add pytest to the environment or provide a project-native `tools/test_all.py` that knows which scripts are smoke, slow, or non-hermetic.
3. Add titles/front-matter to the 13 unindexed topic files or explicitly mark them archival/non-indexed.
4. Keep `generate.py --check`, `validate.py`, `drift_check.py`, and `top.py health` as the immediate pre-commit gate set; they are currently green except advisory metadata/evidence.
5. Do not stage broadly. Use explicit file lists because the workspace contains concurrent/generated/untracked work.
