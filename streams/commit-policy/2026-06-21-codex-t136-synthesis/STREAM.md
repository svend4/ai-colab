---
id: 2026-06-21-codex-t136-synthesis
topic: commit-policy
status: ready-for-review
author: codex
related: [T-136, D-017, D-018, D-019]
adoption: proposed-in-D-019
variant_of: commit-stream-policy
---

# Codex synthesis for T-136

## Problem

The current shared worktree works for small sequential edits, but it becomes fragile when several agents edit task sources and generated indexes at the same time.

T-136 asks for a decision on three layers:

- Level 0: selective-add + commit-lock in the shared worktree;
- Level 1: per-agent/per-task git worktrees plus a merge-gate;
- semi-commit format: `streams/` packet versus git branch versus ad hoc Markdown.

## Evidence

The T-133 case is useful because it happened live:

- Codex held the T-133 pipeline claim and completed `text_extract`.
- Claude saw the active claim and did not overwrite/commit T-133 files.
- Claude's own evidence for T-137/T-136 was ready, but generated indexes were stale because T-133 was active.
- A broad regenerate + commit would have mixed another agent's half-done state into the commit.

This proves that Level 0 is necessary but incomplete. Commit-lock serializes the actual git operation; selective-add prevents broad commits; neither gives isolated generated artifacts.

## Codex Position

1. **Use Level 0 now.** It is cheap, tested, and already fits the repository policy.
2. **Make `streams/` the semi-commit format.** It is the right layer for variants, evidence, proposed patches, and adoption records. It should not replace git.
3. **Move to Level 1 for real parallelism.** Worktree-per-agent/task is the technical boundary that makes `git add -A`, generated indexes, local logs, and test artifacts local to the stream instead of shared noise.
4. **Use a merge-gate, not free merging.** Mainline should receive only reviewed integration commits with `validate`, `generate --check`, and focused tests green.
5. **Do not close this as accepted without Stefan.** Worktrees change how the system is operated; D-018 says this needs human/collective approval.

## Proposed Architecture

```text
stream packet
  -> optional worktree/branch for implementation
  -> local generate/validate/tests
  -> integration review
  -> mainline commit
  -> stream adoption note
```

## Why not a separate Markdown changeset system

A Markdown changeset is useful as evidence inside `streams/`, but not as a second VCS. Once code changes are involved, git already provides diff, merge, conflict resolution and history. The repository should not reimplement those features in ad hoc text files.

## What Stefan Needs To Decide

- Are per-agent/per-task worktrees allowed on this machine/project?
- Who is the merge-gate owner: Stefan, a named integrator agent, or a rotating role?
- Should Level 1 be mandatory for all agents or only for high-conflict tasks touching generated indexes/code?

## Recommendation

Accept Level 0 immediately. Approve Level 1 as the target for multi-agent parallelism. Keep `streams/` as the visible discussion/evidence layer and git worktrees as the execution isolation layer.