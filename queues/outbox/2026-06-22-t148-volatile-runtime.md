---
from: codex
type: result
task: T-148
related: [D-022, docs/parallel-work-policy.md, tools/test_volatile.py]
status: done
---

# T-148 result — volatile runtime snapshots

Implemented the remaining volatile-files part of D-022/T-148.

Changed:

- untracked runtime snapshots from Git: `LIVE.md`, `PIPELINE.md`, `logs/heartbeat.json`, `logs/pipeline.json`;
- added them to `.gitignore`;
- added `tools/test_volatile.py` regression: snapshot may rewrite volatile files, but `generate.py --check` remains green;
- updated `docs/pipeline-operator-guide.md` and `tools/README.md` to state that these files are live runtime views, not ordinary commit scope.

Existing auto-escalation via `cohort guard` was already merged in `82cab10`/`e2e700f`; this task does not duplicate that code.