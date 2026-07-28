---
id: bulk-guard-range-gate-implementation-2026-07-07
type: report
status: done
agent: codex
date: 2026-07-07
related: [T-294, D-026, reports/bulk-guard-range-gate-proposal-2026-07-06.md, reports/no-verify-bulk-guard-review-2026-07-06.md]
---

# Bulk guard range gate implementation

## Что сделано

Реализован additive-режим:

```powershell
python tools\bulk_guard.py --range BASE..HEAD --json
python tools\bulk_guard.py --range BASE..HEAD --strict
```

Режим не меняет `tools/githooks/**` и не трогает deny-пути. Он предназначен для будущего merge-gate/CI/pre-receive слоя, который нельзя обойти локальным `git commit --no-verify`.

## Что проверяет range-gate

1. `aggregate`: итоговый `git diff --numstat --find-renames BASE HEAD`.
2. `commits`: diff каждого коммита в `git rev-list --reverse BASE..HEAD`.
3. `churn`: суммарные удаления по всем коммитам диапазона.
4. `hidden_by_aggregate`: признак сценария, где итоговый diff выглядит безопасно, но внутри диапазона было крупное удаление.
5. `insurance`: backup-tags на base/head и parent опасного коммита.

## Политика страховки

- Для обычного working/staged diff старая логика сохраняется: backup-tag должен указывать на текущий `HEAD`, потому это состояние до незакоммиченного стирания.
- Для range aggregate/churn страховка должна быть на `BASE`.
- Для per-commit bulk страховка должна быть на parent опасного коммита.
- Backup-tag на финальном `HEAD` не страхует уже совершённое удаление.

## Что подсказали подагенты

Meitner подтвердил главный риск: нельзя реализовывать `--range` как простой aggregate diff, иначе `delete -> restore` будет невидимым. В реализацию добавлены per-commit и churn проверки.

Nash независимо выбрал `bulk-guard-range-gate` как первый additive-кандидат и предложил следующие additive-направления: package handoff, package gate advisory, cauldron materializer, D-033 brief-only.

## Проверки

```text
python -m py_compile tools\bulk_guard.py tools\tests\test_bulk_guard.py tools\tests\test_bulk_guard_range.py -> OK
python tools\tests\test_bulk_guard.py -> OK
python tools\tests\test_bulk_guard_range.py -> OK
python tools\bulk_guard.py --range HEAD..HEAD --json -> verdict ok-not-bulk
python tools\bulk_guard.py --definitely-unknown -> явная ошибка unknown argument
python tools\bulk_guard.py -> не массовая операция
```

## Ограничения

- Интеграция в CI/pre-receive пока не выполнена.
- `--strict` сейчас фиксируется в JSON и оставлен как интерфейс для будущего gate; основной enforcement уже идёт через `verdict` и nonzero при `STOP-uninsured`.
- Merge commits анализируются по first parent. Для сложной merge-политики нужен отдельный follow-up.