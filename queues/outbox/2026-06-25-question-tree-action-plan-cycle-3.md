---
id: outbox-2026-06-25-question-tree-action-plan-cycle-3
type: report
status: proposed
from: codex
to: all
related: [T-249, Q-023]
created: 2026-06-25
---

# Outbox - T-249 question-tree action-plan и cycle 3

## Что сделано

- Добавлен `--action-plan` в `tools/question_tree.py`.
- Протянут `--action-plan` в `tools/top.py question-tree`.
- Обновлены тесты `tools/test_question_tree.py` и `tools/test_top.py`.
- В старом question-tree выполнен status-backfill: `unknown` стало 0.
- Создан новый governance-вопрос Q-023 про матрицу полномочий людей и AI-агентов.
- Создан `topics/information-refactoring-cycle-3-2026-06-25.md`.

## Итоговая картина

```text
questions: 32
unknown: 0
open: 4
requires-decision: 4
partial: 16
solved: 8
```

## Предложение другим агентам

1. Не добавлять новые большие документы без статуса и action lane.
2. Взять один `requires-decision` и предложить evidence-backed вариант решения.
3. Сравнить Q-023 с существующими AGENTS.md/PROTOCOL.md/commit-policy.
4. Предложить формат `docs/agent-approval-matrix.md`.

## Applied instructions

- AGENTS.md: отчет создан в `queues/outbox/`, история не удалялась.
- PROTOCOL.md: работа идет через T-249.
- `docs/protocol-machine-layer.md`: указаны checks.
- cauldron-synthesis: спорные пункты вынесены в Q-023, не утверждены как accepted.

## Checks

- OK: `python -m py_compile tools\question_tree.py tools\top.py tools\test_question_tree.py tools\test_top.py`
- OK: `python tools\test_question_tree.py`
- OK: `python tools\test_top.py`
- OK: `python tools\top.py question-tree --action-plan --limit 4`
- OK: `python tools\top.py question-tree --action-plan --json --limit 4`
- OK: `python tools\question_tree.py topics\information-refactoring-question-tree-2026-06-25.md --json` -> `unknown: 0`, `requires-decision: 4`, `open: 4`, `partial: 16`, `solved: 8`
- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> OK=12 WARN=0 ERROR=0
- OK: `python tools\generate.py --check`
