---
from: codex
type: review
task: T-146
related: [D-017, D-019, D-021, Q-015, T-135, T-136, T-144]
status: historical
---

# T-146 — review of streams/worktree waiting problems

Подготовлен обзор `docs/parallel-streams-problems-review-2026-06-22.md`.

Ключевой вывод: проблема ожидания чужого commit уже доказана практикой. Level 0 (`commit_lock` + selective-add) нужен, но не устраняет shared generated indexes. При чужих незавершённых файлах, stale generated index и hot files Level 1 worktree должен быть обязательным или почти обязательным режимом.

Созданы:

- `Q-015` — вопрос о триггерах обязательного Level 1;
- `streams/commit-policy/20260622-0555-codex/STREAM.md` — stream-предложение по trigger policy;
- профильная запись в `topics/commit-policy-streams-2026-06-21.md`.

Практическая проверка:

- `python tools\top.py work-mode codex T-146 --parallel --hot-files` рекомендует `Level 1 worktree`;
- `python tools\flow.py start codex T-146 --worktree` печатает dry-run worktree-команду.