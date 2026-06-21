# D-021 acceptance closeout — 2026-06-21

Task: `T-143`
Related: `D-021`, `T-136`, `T-137`, `T-020`, `D-020`

## What changed

The repository now treats `D-021` as the accepted governance decision for the open kettle packet.

Closed as done:

- `T-136` — commit policy / Level 0 / Level 1 / semi-format consensus;
- `T-137` — broader open-points synthesis around D3 scope, worktree-streams, sandbox intake, and dependency policy.

Still open/blocked by design:

- `T-020` remains blocked until a real read-only external source/path/archive is provided;
- PDF extraction remains a future dependency decision;
- heavier §9 P1 automation remains deferred until measured demand.

## Technical verification

Passed:

- `python tools\test_worktree.py`
- `python tools\test_flow.py`
- `python tools\test_stream.py`
- `python tools\test_merge_gate.py`

Dry-run operational checks also passed without creating a worktree:

- `python tools\worktree.py spawn codex T-143`
- `python tools\flow.py start codex T-143 --worktree`
- `python tools\flow.py finish codex T-143 --worktree`

## Current rule

Level 0 remains the default in the shared working tree: selective-add plus `commit_lock`.

Level 1 is accepted but explicit: use `--worktree` for real parallel load where dirty work, generated indexes, or commit locks would otherwise collide. Merge into mainline is gated and confirmed by Stefan or a named integrator.

## My opinion

This is the right stage transition. The project should not force every small edit into a worktree; that would slow down simple documentation and low-risk fixes. But the system now has a real escape hatch for parallel agents: separate worktree, separate branch, merge gate, explicit integration. That is the missing middle layer between a chat-like shared folder and a full CI/CD platform.

The next valuable improvement is not another governance document. It is a small human/agent wrapper that makes Level 0 vs Level 1 choice obvious at task start: simple task -> shared tree; contested/parallel task -> worktree stream.
