---
id: 2026-06-24-unused-advice-audit
type: workflow-review
status: historical
agent: codex
created: 2026-06-24
related: 
---

# Unused advice audit

## Summary

This retry audit checks whether valuable advice already exists in the repository but is still not reliably activated as a command, gate, checklist, template, or standard workflow.

The current state is mixed. The project already has a real activation layer: `tools/top.py`, `tools/advice.py`, `tools/friction.py`, `tools/conveyor.py`, `tools/instructions.py`, `tools/result_intake.py`, `tools/adoption.py`, and `tools/assurance.py`. That means the problem is no longer "there is only text". The sharper problem is that some useful recommendations are only partly wired: agents can read them, but the recommended action is not always forced, summarized, queued, or made into a single safe button.

Evidence from this retry:

- `python tools\top.py conveyor --json` reports the retry workflow `godel unused advice audit retry` as in-flight and healthy.
- `queues/outbox/2026-06-24-unused-advice-audit.md` did not exist before this retry write.
- `python tools\top.py advice codex --parallel --hot-files --json` completed and showed active advice A-001, A-002, A-003, A-006.
- `python tools\friction.py status --json` completed but took long enough to demonstrate that some advisory checks need a faster mode.
- `python tools\adoption.py --help` reports high static adoption, but also shows a dormant tool and one orphan doc, so static adoption is not enough to prove operational use.

## Unused advice inventory

| Item | Source | Symptom | Inactive reason | Proposed activation path |
|---|---|---|---|---|
| UAI-001 | `docs/friction-ledger.md`, `docs/friction-playbook.md` | Repeated Windows/runtime/manual workaround problems are documented, but agents may still repeat manual fixes from memory. | `tools/friction.py status` exists, yet the next action after a warning is not always automatically turned into a concrete command sequence for the current task. | Add a top-level "friction next" workflow that runs status, expands only warn/fail recipes, and prints a short task-specific checklist. Future proposal label: friction-next command module, not an existing repo path. |
| UAI-002 | `docs/top-layer-command-groups.md`, `docs/instruction-assurance.md` | Agents can start work without proving they applied task-specific instructions. | `check-report` validates reports after the fact, but preflight is advisory unless the agent chooses to run it. | Make `python tools\top.py agent-start ...` or `python tools\top.py take ...` print a required "preflight evidence target" for the eventual outbox/done report. |
| UAI-003 | `docs/workflow-conveyor-policy.md`, `queues/outbox/2026-06-24-lagrange-agent-conveyor-activation-checklist.md` | Workflows can remain in-flight after reset/hang while the UI does not clearly show progress. | `conveyor.py status` sees in-flight workflows, but there is no standard retry/recover command that checks missing output and writes a recovery note. | Add a "conveyor recover" checklist: status, output existence, check-report, land/ship or dismiss with reason. Future proposal label: conveyor-recover command module, not an existing repo path. |
| UAI-004 | `docs/top-layer-throughput-methodology.md`, `queues/outbox/2026-06-24-codex-agent-hierarchy-operating-model.md` | Multi-agent fan-out creates useful reports, but Codex can become the bottleneck for synthesis and application. | The hierarchy model exists, but "observer cell -> chief synthesis -> implementation queue" is not yet a single repeatable command group. | Add a standard observer-cell report template and a `top.py process-landed --cell` mode that groups related landed outputs before implementation. |
| UAI-005 | `queues/outbox/2026-06-24-halley-next-agent-work-queue.md` | Halley proposed safe next work, but proposed work can remain a text queue instead of becoming actual conveyor work or tasks. | The queue is human-readable; there is no automatic extraction from outbox recommendations to proposed workflow launches. | Use `result_intake.py classify` plus a future "queue proposal extractor" that emits candidate `conveyor.py launch` commands without executing them. |
| UAI-006 | `queues/outbox/2026-06-24-t238-draft-code-sandbox.md`, `sandbox/drafts/README.md` | Draft code sandbox exists, but agents may not know when to use it instead of editing `tools/` directly. | The lane is documented and useful, but not yet surfaced by `advice.py` as a current recommendation when a task asks agents to write experimental code. | Add an advice rule: if task context contains draft/prototype/agent code and no claim/worktree exists, recommend `sandbox/drafts/` manifest flow. |
| UAI-007 | `docs/friction-ledger.md` | Friction repeat counts are approximate. | There is no durable event log for "this workaround was used again". | Add a read-only-by-default note command that appends to a future friction event log only when explicitly asked. Future proposal file name: logs/friction.jsonl. |
| UAI-008 | `docs/friction-ledger.md`, `docs/commit-stream-policy.md` | Streams can be created but not adopted or rejected. | `tools/stream.py check` exists, but stale stream results are not automatically placed into the next synthesis queue. | Add stream check output to `top.py health` or `top.py advice` when open streams are stale. |
| UAI-009 | `docs/instruction-assurance.md` | Reports can contain formal "Applied instructions" evidence without task-specific references. | `assurance.py` detects low-level findings, but current behavior is advisory and not blocking. | For service/governance tasks, require at least one task-specific path in `--applied` or report body before done/ship. Start as warning, later strict gate. |
| UAI-010 | `docs/top-layer-command-groups.md` | Too many useful commands exist, but users and agents need "one button" groups. | `top.py` centralizes many commands, but there is no single "continue safely" command that does status, friction, advice, conveyor, and next candidates. | Add `python tools\top.py continue codex --context "<topic>"` as a composed read-only action. Future proposal file name: no code yet, command name proposal only. |
| UAI-011 | `docs/workflow-conveyor-policy.md`, `docs/top-layer-throughput-methodology.md` | Landed reports can pile up while agents keep launching more work. | `conveyor.py status` reports landed counts, but it does not enforce "process landed before refill" outside human discipline. | Add a soft gate in `conveyor.py regulate`: if landed > 0, print PROCESS as higher priority than REFILL and recommend no new launches. |
| UAI-012 | `AGENTS.md`, `PROTOCOL.md` | Queue rules exist, but retries after UI reset may bypass normal claim/landing evidence. | The retry prompt was clear, but the durable workflow status and output file had to be checked manually. | Add a retry report template for "same task after reset": workflow id, output path, duplicate check, allowed write scope, result. |

## Top 5 activation candidates for Codex

1. **Conveyor recovery command/checklist**: solve the exact current failure mode where a workflow is in-flight, UI does not show activity, and output is missing. This should be first because it directly prevents lost agent work after resets.

2. **Friction next action command**: `friction.py status` already finds F-006, F-011, F-015 and other signals. The missing layer is a short "do these 3 commands now" output that Codex and other agents can apply without reading the whole ledger.

3. **Instruction evidence hardening**: `advice.py` found A-006 because T-237 and T-238 done markers have formal evidence. This should become a stronger service/governance gate after a few warning cycles.

4. **Draft-code sandbox advice rule**: T-238 created a useful lane for agent-written proposal code. It should be activated automatically by advice/preflight when a prompt asks for prototype or experimental agent code.

5. **Observer-cell landed synthesis**: the hierarchy document is useful, but the upper layer needs a small command group for "3 workers + 1 observer -> one synthesis -> one implementation queue".

## Command/check/skill/template classification

| Recommendation | Best form | Why |
|---|---|---|
| Conveyor recovery after reset | Check + command group | It must inspect current state and output existence, then decide land/ship/dismiss. |
| Friction next action | Command | The inputs are machine-detectable warn/fail friction IDs. |
| Applied-instructions hardening | Gate/check | It is evidence quality, not a human essay. |
| Draft-code sandbox routing | Advice rule + template | Agents need a clear manifest and no-execute contract before writing code proposals. |
| Observer-cell synthesis | Template + workflow command | Human-readable reports still need a stable format before automation. |
| Friction event counts | Command + log | The current counts are approximate; automation needs an event stream. |
| Stream lifecycle adoption | Check | It should detect stale/open streams and propose adoption/rejection tasks. |
| Next-action button | Command group | It exists to reduce cognitive overhead, not to create new policy. |
| Skill/docs drift | Check | Skills should stay thin and link back to canonical docs. |
| External-code/sandbox execute policy | Documentation + gate | It should remain conservative; execution must not be normalized by convenience. |

## What should remain documentation only

- Conceptual explanation of the pyramid, middle layer, and human/agent roles should stay in docs. It helps new readers and should not become a rigid command.
- Rationale for why execute is dangerous should stay as documentation plus human gate. This is not a good candidate for automatic execution.
- Historical reports and dismissed workflows should remain archival unless they contain a reusable pattern that has been promoted into a current task, decision, or tool.
- Broad methodology about maximum agent counts should remain advisory. The actual operational limit should come from current landed/in-flight processing capacity, not a fixed magic number.
- The full friction ledger should stay canonical documentation. Commands should summarize and activate it, not replace it.

## Current Codex disposition

This report should be processed as a read-only/outbox-only result for workflow `W-2026-06-24-godel-unused-advice-retry`.

Recommended next processing steps:

1. Run `python tools\instructions.py check-report queues\outbox\2026-06-24-unused-advice-audit.md`.
2. Run `python tools\result_intake.py classify queues\outbox\2026-06-24-unused-advice-audit.md --json`.
3. Run `python tools\conveyor.py land W-2026-06-24-godel-unused-advice-retry --output queues\outbox\2026-06-24-unused-advice-audit.md`.
4. Run `python tools\conveyor.py ship W-2026-06-24-godel-unused-advice-retry` after Codex has summarized or queued the top activation candidates.

## Checks

Commands used or recommended for verification:

- `Test-Path -LiteralPath "queues\outbox\2026-06-24-unused-advice-audit.md"`
- `git status --short --untracked-files=all`
- `python tools\conveyor.py status --json`
- `python tools\pipeline.py status`
- `python tools\top.py conveyor --json`
- `python tools\top.py advice codex --parallel --hot-files --json`
- `python tools\friction.py status --json`
- `python tools\adoption.py --help`
- `python tools\instructions.py check-report queues\outbox\2026-06-24-unused-advice-audit.md`
- `python tools\result_intake.py classify queues\outbox\2026-06-24-unused-advice-audit.md --json`

Observed during retry:

- `python tools\conveyor.py status --json` returned healthy with `godel unused advice audit retry` in-flight.
- `python tools\pipeline.py status` returned no in-work, ready, or blocked tasks.
- `python tools\top.py advice codex --parallel --hot-files --json` returned advice A-001, A-002, A-003, A-006.
- `python tools\friction.py status --json` returned active warnings F-006, F-011, F-015 and a TEMP warning F-004.
- `python tools\adoption.py --help` reported one dormant tool and one orphan doc.

## Applied instructions

Applied instructions evidence:

- `AGENTS.md` says all agents must work by `PROTOCOL.md`, must not delete others' messages, must not rewrite history, and should use `queues/outbox/` for automatic work results. This report writes one new outbox file and does not edit code, tasks, generated files, logs, or git.
- `PROTOCOL.md` defines `queues/outbox/` as prepared results not yet moved into main files and describes the pipeline loop: check status, write result to outbox/profile topic, then the main agent or human moves important content into main files. This report is a proposed result, not an accepted decision.
- `PROTOCOL.md` says duplicate execution should not happen when another agent already has a claim, except for intentional alternatives. This retry did not create a second output file; it used the exact allowed output path from the retry prompt.
- `docs/instruction-assurance.md` requires applied-instruction evidence and a `Checks:` marker. This report includes both this section and the `## Checks` section.

Checks:

- `python tools\instructions.py check-report queues\outbox\2026-06-24-unused-advice-audit.md`
