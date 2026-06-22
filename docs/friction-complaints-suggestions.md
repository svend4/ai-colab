# Friction complaints and suggestions log

Дата: 2026-06-22  
Связано: `T-149`, `docs/friction-ledger.md`, `docs/friction-playbook.md`, `skills/repo-friction-playbook/SKILL.md`.

## Назначение

Это “журнал жалоб и предложений” для повторяющихся проблем разработки. Здесь фиксируются не эмоции, а операционные сигналы: что повторилось, сколько раз примерно, что помогло, что нужно автоматизировать.

## Формат записи

```md
## YYYY-MM-DD — короткий симптом

- F-ID:
- Кто заметил:
- Где/команда:
- Повторяемость:
- Ручное решение:
- Потеря времени/риск:
- Предложение:
- Статус: open | documented | playbook | automate | done
```

## Записи

### 2026-06-22 — Ошибочный claim не той задачи через `pipeline.py next`

- F-ID: F-016
- Кто заметил: Codex
- Где/команда: при T-149 команда `python tools\pipeline.py next codex` взяла ready-задачу T-148, потому она была раньше/обычного приоритета.
- Повторяемость: 1 явный случай, но риск системный.
- Ручное решение: снять только свой ошибочный claim T-148, вернуть T-148 в `todo`, повысить T-149 до `high`, повторить `next`.
- Потеря времени/риск: можно случайно удерживать чужой/неактуальный work item и создать ложную блокировку.
- Предложение: добавить targeted claim: `pipeline.py claim <agent> <T-id>` или `top.py take <agent> <T-id>`.
- Статус: documented

### 2026-06-22 — Повторяемые Windows sandbox fallbacks

- F-ID: F-001, F-002, F-003, F-004
- Кто заметил: Stefan/Codex/другие агенты
- Где/команда: `apply_patch`, PowerShell `Get-Content`, `python`, `%TEMP%`.
- Повторяемость: 6+ суммарных ручных обходов.
- Ручное решение: UTF-8 setup, short commands, timeout, `tmp-work`, PowerShell UTF-8 write fallback.
- Потеря времени/риск: повторное ручное лечение, ложные подозрения на повреждение файлов, зависания.
- Предложение: `tools/friction.py runtime/temp/encoding` как read-only diagnostics.
- Статус: playbook

### 2026-06-22 — Shared-worktree/generated-index конфликт

- F-ID: F-006, F-007, F-008, F-015
- Кто заметил: Codex/Claude через T-133/T-136/T-146/T-147
- Где/команда: `git status`, `generate.py --check`, `commit_lock.py`, volatile `LIVE.md/logs`.
- Повторяемость: 8+ суммарных проявлений.
- Ручное решение: selective-add, commit_lock, restore volatile, Level 1 worktree по D-022 triggers.
- Потеря времени/риск: смешанный commit, ожидание чужого commit, stale generated indexes.
- Предложение: `tools/top.py friction` как unified preflight поверх `cohort guard`, `generate --check`, volatile detector.
- Статус: automate

## Открытые предложения

| ID | Предложение | Основание | Приоритет |
|---|---|---|---|
| FP-001 | `pipeline.py claim <agent> <T-id>` / `top.py take <T-id>` | F-016 | high |
| FP-002 | `tools/top.py friction` read-only status | F-001..F-015 | high |
| FP-003 | `tools/stream.py check` для proposed/adoption lifecycle | F-013 | normal |
| FP-004 | `tools/friction.py note <F-id>` для счётчика повторов | F-017 | normal |
| FP-005 | validate-связь skill -> docs/friction-* | F-018 | low |
### 2026-06-22 — Skill metadata generator: UTF-8 + YAML frontmatter

- F-ID: F-002, F-018
- Кто заметил: Codex
- Где/команда: `generate_openai_yaml.py skills\repo-friction-playbook` сначала упал на cp1252 decode, затем на YAML `description` с двоеточием.
- Повторяемость: 1 конкретный случай, но относится к уже повторявшемуся encoding/frontmatter классу.
- Ручное решение: запускать с `$env:PYTHONUTF8='1'`; YAML `description` писать как block scalar `description: >`.
- Потеря времени/риск: skill выглядит созданным, но metadata/validation падают позже.
- Предложение: добавить в skill/playbook правило frontmatter: длинные descriptions с `:` оформлять block scalar.
- Статус: documented

### 2026-06-22 — T-150 retrospective: старые обходы повторились и стали detector-слоем

- F-ID: F-001, F-004, F-006, F-011, F-013, F-018
- Кто заметил: Codex
- Где/команда: `apply_patch` при правке `tasks/T-150.md`; первый `tools/test_friction.py`; `python tools/friction.py status`; `python tools/stream.py check`.
- Повторяемость: F-001/F-004/F-006 уже 4+ раз; F-013/F-018 повторяются как governance/tooling drift.
- Ручное решение: PowerShell UTF-8 fallback; temp root в `C:\tmp`/`tmp-work`; selective-add; не включать unrelated `streams/*`; обновить skill/docs.
- Потеря времени/риск: без detector агент снова тратит время на уже известные обходы и может смешать чужие изменения в commit.
- Предложение: `tools/friction.py status/recipe/list`, `top.py friction`, затем отдельные задачи для targeted claim, stream cleanup и ownership-aware dirty classifier.
- Статус: automate
