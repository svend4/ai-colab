---
status: historical
---
# Conveyor backlog normalized dedup

- Дата: 2026-06-23
- Автор: codex
- Связанная задача: T-167
- Связанные файлы: `tools/conveyor.py`, `tools/test_conveyor.py`, `docs/workflow-conveyor-policy.md`

## Что изменено

`conveyor.py next` теперь сравнивает backlog-кандидаты с уже запущенными workflow по нормализованным ключам: дефисы, пробелы, регистр и похожие короткие label больше не должны приводить к повторной выдаче уже отработанной смысловой ноды.

## Почему именно так

После T-166 runtime workflow назывался `instruction-check-report-refs`, а backlog-кандидат назывался `Instruction check-report: verify referenced files/commands exist`. Старое сравнение искало первые символы candidate в сырой строке labels/ids и не видело совпадение из-за пробела/дефиса. В результате конвейер предлагал уже выполненную работу как новый REFILL.

Моё мнение: это маленький, но важный слой самоуправления. Если конвейер сам себя кормит бэклогом, он должен уметь не только находить следующие задачи, но и не возвращать завершённые задачи под другой пунктуацией.

## Проверки

- `python tools/test_conveyor.py` — OK.
- `python tools/conveyor.py next` — больше не показывает `Instruction check-report`; остальные кандидаты остались.
- `python tools/top.py conveyor --json` — healthy, target 4 / in-flight 4 / landed 0.

## Applied instructions

- `AGENTS.md`: работал как `codex`, чужие сообщения и историю не переписывал.
- `PROTOCOL.md`: служебная правка объяснена в этом outbox-отчёте.
- `docs/workflow-conveyor-policy.md`: обновлена только дисциплина `conveyor.py next` dedup.
- Checks: python tools/test_conveyor.py -> OK.
- Checks: python tools/conveyor.py next -> OK.
- Checks: python tools/top.py conveyor --json -> OK.