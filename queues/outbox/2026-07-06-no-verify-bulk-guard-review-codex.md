---
agent: codex
date: 2026-07-06
type: incident-review
status: proposed
related: [D-026, tools/bulk_guard.py, tools/commit.py, reports/no-verify-bulk-guard-review-2026-07-06.md]
---

# No-verify / bulk-guard review

Codex перепроверил цитату про обход `bulk_guard` через `git commit --no-verify`.

Вывод: текущий репозиторий не содержит массовых tracked deletions; D-026 accepted, `bulk_guard` и pre-commit подключены, hooksPath активен. Но `--no-verify` действительно может обойти локальный hook, поэтому нужна защита выше: безопасная commit-обёртка + CI/pre-receive/merge-gate bulk-range check.

Сразу усилено: `bulk_guard` теперь засчитывает страховку только если `backup-*` tag указывает на текущий HEAD; старые backup-теги больше не страхуют новый bulk-diff.

Подробно: `reports/no-verify-bulk-guard-review-2026-07-06.md`.