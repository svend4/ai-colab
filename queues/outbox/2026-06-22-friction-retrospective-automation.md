---
id: outbox-2026-06-22-friction-retrospective-automation
type: outbox
topic: friction-retrospective
author: codex
related: [T-150, T-147, T-149, D-022]
status: historical
---

# T-150 — friction retrospective + automation

Codex выполнил глубокую ретроспективу повторяющихся проблем и добавил первый read-mostly detector.

## Добавлено

- `docs/friction-retrospective-2026-06-22.md` — полный обзор прошлого: runtime/TEMP, PowerShell UTF-8, git/shared-worktree, generated drift, pipeline claims, streams, sandbox/svend4, skill/docs drift.
- `tools/friction.py` — команды `status`, `recipe`, `list`.
- `tools/test_friction.py` — герметичные тесты для registry/recipes/pure detectors/temp probe.
- `tools/top.py friction` — одна “кнопка” для людей и агентов.
- Обновлены `docs/friction-ledger.md`, `docs/friction-playbook.md`, `docs/friction-complaints-suggestions.md`, `docs/README.md`, `tools/README.md`, `skills/repo-friction-playbook/SKILL.md`.

## Саморефлексия по T-150

Во время задачи повторились старые архетипы:

- F-001: `apply_patch` снова упал в Windows sandbox, применён documented UTF-8 PowerShell fallback.
- F-004: первый `test_friction.py` упал на `%TEMP% PermissionError`, исправлен на `C:\tmp`/`tmp-work`.
- F-006/F-015: `friction.py` показал dirty generated/shared files во время активной задачи — правильный сигнал против `git add -A`.
- F-013: `stream.py check` показывает legacy broken streams; это отдельный cleanup-долг, не часть T-150.
- F-018: skill был обновлён, чтобы ссылаться на `tools/friction.py`.

## Не смешивать с этим commit

В рабочем дереве обнаружены unrelated изменения `streams/apex-panel/.../STREAM.md` и `streams/portal-location/.../STREAM.md` (`status: adopted`, `adopted_commit: D-021`). Они выглядят осмысленными, но не относятся к T-150. Их нужно проверять/коммитить отдельной задачей или интеграционным решением.

## Следующие кандидаты

1. `pipeline.py claim <agent> <T-id>` / `top.py take <agent> <T-id>` для F-016.
2. Cleanup старых stream front-matter, чтобы `python tools/stream.py check` был зелёным.
3. Ownership-aware dirty classifier в `friction.py` или `cohort.py`.
4. `friction.py note` / `logs/friction.jsonl` для точных счётчиков повторов.
5. Подключить краткий friction summary к `top.py agent-start`.