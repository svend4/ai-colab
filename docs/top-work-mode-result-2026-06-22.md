# Top work-mode result — 2026-06-22

Task: `T-144`
Related: `D-021`, `T-136`, `T-143`, `tools/top.py`, `tools/flow.py`, `tools/worktree.py`

## What changed

`tools/top.py` now has a dry-by-default command:

```powershell
python tools\top.py work-mode <agent> <task>
python tools\top.py work-mode <agent> <task> --parallel --hot-files
python tools\top.py work-mode <agent> <task> --mode worktree
```

It recommends one of two D-021 modes:

- **Level 0 shared tree** — default for small, low-conflict edits;
- **Level 1 worktree** — explicit mode for parallel work, dirty mainline, or hot generated/shared files.

The command only prints a plan. It does not create a worktree, does not commit, and does not merge.

## Why this matters

D-021 accepted worktree-streams, but a human or agent still needed to remember when to use them. `work-mode` makes that choice visible at task start. This is the right level of automation: it reduces friction without hiding the underlying tools.

## Verification

Passed:

- `python tools\test_top.py`
- `python tools\top.py work-mode codex T-144`
- `python tools\top.py work-mode codex T-144 --parallel`
- `python tools\top.py work-mode codex T-144 --mode worktree`
- `python tools\top.py buttons --json`

## Limits

This is not a scheduler and not an auto-router. It is a small decision helper. If the user wants automatic worktree creation, that should be a separate higher-risk task because it touches Git state outside the current workspace.