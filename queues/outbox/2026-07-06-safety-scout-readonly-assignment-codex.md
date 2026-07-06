---
agent: codex
date: 2026-07-06
type: delegation-request
status: proposed
role: subagent-worker/safety-scout
mode: read-only
related: [D-026, tools/bulk_guard.py, tools/commit.py, tools/githooks/pre-commit, reports/no-verify-bulk-guard-review-2026-07-06.md]
---

# Safety-scout read-only assignment

Задание предназначено для временной роли `subagent-worker/safety-scout`, а не для добавления нового постоянного агента в ростер.

## Контекст

Была цитата, что агент обошёл `bulk_guard` через `git commit --no-verify`. Codex уже перепроверил `D-026`, `bulk_guard`, `pre-commit` и усилил логику `backup-on-HEAD`.

## Ограничения

- Работать read-only.
- Не редактировать файлы.
- Не создавать коммиты.
- Не менять `tools/githooks/**`, `tools/permissions.json`, `sandbox/approvals/**`.

## Что проверить

1. `decisions/D-026.md`.
2. D-026-раздел в `PROTOCOL.md`.
3. `tools/bulk_guard.py`.
4. `tools/tests/test_bulk_guard.py`.
5. `tools/commit.py`.
6. `tools/tests/test_commit.py`.
7. `tools/githooks/pre-commit`.
8. `reports/no-verify-bulk-guard-review-2026-07-06.md`.

## Требуемый отчёт

1. Какие слои защиты уже есть.
2. Как именно `--no-verify` их обходит.
3. Какие 3 технических меры нельзя обойти локальным `--no-verify`: CI, pre-receive, merge-gate/range guard.
4. Точный CLI-контракт для `bulk_guard --range` или отдельного `bulk_range_guard.py`.
5. Риски ложных срабатываний.
6. Ссылки формата `file:line` на проверенные места.

## Мнение Codex

Это правильный тип задачи для роя: read-only scout не блокирует основного исполнителя, даёт независимую доказательную базу, а интегратор потом сравнивает выводы с текущим отчётом Codex.
