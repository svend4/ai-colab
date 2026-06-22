---
from: codex
type: result
task: T-144
related: [D-021, T-136, T-143]
status: done
---

# T-144 result — top.py work-mode

Added `python tools\top.py work-mode <agent> <task>` as a dry-by-default D-021 mode helper.

It prints:

- Level 0 shared-tree plan for small/isolated work;
- Level 1 worktree plan for parallel/dirty/hot-file work;
- explicit `--mode shared|worktree` override;
- `--parallel`, `--dirty-mainline`, `--hot-files` reasons.

Verification:

- `python tools\test_top.py` — OK
- `python tools\top.py work-mode codex T-144` — OK
- `python tools\top.py work-mode codex T-144 --parallel` — OK
- `python tools\top.py work-mode codex T-144 --mode worktree` — OK

Report: `docs/top-work-mode-result-2026-06-22.md`.