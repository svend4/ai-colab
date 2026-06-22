---
name: repo-friction-playbook
description: >
  Use when Codex works in this repository and sees repeated operational friction: Windows sandbox or PowerShell issues, TEMP PermissionError, Git index.lock, stale generated indexes, foreign half-done work, pipeline claim mistakes, runtime log noise, stream adoption drift, or when asked to record complaints/suggestions and turn repeated manual fixes into docs, skills, or future tools.
---

# Repo Friction Playbook

## Purpose

Use this skill to avoid repeating the same manual fixes in the AI collaboration repository. The source of truth is the repo documentation, not this skill body.

Read these files as needed:

- `docs/friction-ledger.md` — archetypes, approximate repeat counts, risks, automation threshold.
- `docs/friction-playbook.md` — “if X, do Y” recipes and Q&A.
- `docs/friction-complaints-suggestions.md` — complaints/suggestions log and proposed improvements.
- `docs/parallel-work-policy.md` — D-022 Level 1 triggers for parallel work.

## First Move

1. Run or inspect current state before changing files:

```powershell
git status --short --untracked-files=all
python tools\top.py status codex
python tools\generate.py --check
```

2. Match the symptom to an `F-XXX` entry in `docs/friction-ledger.md`.
3. Apply the recipe from `docs/friction-playbook.md`.
4. If the symptom repeats, update the ledger or complaints log before inventing a new workaround.

## Decision Tree

- `apply_patch` fails in Windows sandbox: use the documented UTF-8 PowerShell fallback inside workspace only.
- PowerShell shows broken Russian text: use the UTF-8 setup recipe before editing files.
- Python/CMD/PowerShell hangs: stop long command chains; use runtime smoke checks and the recovery playbook.
- `%TEMP%` gives `PermissionError`: use `tmp-work`, `C:\tmp`, or `drivers/test_tmp.py`.
- Git lock or `.git` permission issue: use `commit_lock.py`; use escalated git only for explicit stage/commit/restore.
- Foreign half-done files or stale generated indexes: do not `git add -A`; use selective-add or Level 1 worktree by D-022.
- Runtime noise in `LIVE.md` or `logs/*`: do not include it in normal commits.
- Pipeline selected the wrong task: release only your own mistaken claim; prefer a future targeted `claim <T-id>` workflow.
- Stream lacks adoption: add status/related/adoption conditions or create a synthesis task.

## Recording A New Complaint

Append to `docs/friction-complaints-suggestions.md` using this shape:

```md
## YYYY-MM-DD — short symptom

- F-ID:
- Who noticed:
- Where/command:
- Repeat count estimate:
- Manual solution:
- Time lost/risk:
- Proposal:
- Status: open | documented | playbook | automate | done
```

If no `F-ID` exists, add one to `docs/friction-ledger.md` first.

## Automation Threshold

Use this rule from the ledger:

- 1 occurrence: document as observation.
- 2-3 occurrences: add to playbook.
- 4+ occurrences: create or update a skill/top command.
- 6+ occurrences or >10 minutes lost: add read-only detector.
- 8+ occurrences or commit/data-loss risk: add guard/gate.

## Commit Discipline

When committing friction work:

1. Run `python tools\generate.py` after task/question/decision changes.
2. Run `python tools\validate.py` and `python tools\generate.py --check`.
3. Exclude volatile runtime files unless the task is explicitly about them.
4. Stage only explicit files.
5. Use `tools/commit_lock.py acquire/release`.