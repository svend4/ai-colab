# T-195 — evidence addendum layer

Дата: 2026-06-23
Агент: codex
Статус: implemented, checked

## Что сделано

Добавлен post-hoc слой evidence addendum для `tools/assurance.py`.

Новые/изменённые элементы:

- `tools/assurance.py` теперь читает `queues/evidence/*.evidence.md` и объединяет addendum с исходным `queues/done/<T-id>.done.md` только для applied-evidence проверки.
- `tools/test_assurance.py` покрывает случай, когда слабый done-marker исправлен отдельным addendum, а другая слабая задача остаётся finding.
- `queues/evidence/T-180.evidence.md` добавлен как evidence addendum к `queues/done/T-180.done.md`.
- `queues/evidence/T-182.evidence.md` добавлен как evidence addendum к `queues/done/T-182.done.md`.
- `docs/instruction-assurance.md` описывает формат `queues/evidence/<T-id>.evidence.md`.
- `tasks/T-195.md` оформляет задачу и границу работы.

## Почему именно так

Проблема: `assurance.py all` находил слабое evidence у T-180/T-182, но прямое редактирование чужих `queues/done/*.done.md` подменяло бы историю выполнения.

Решение: addendum отделяет историю от ревью-доказательства.

- `done` остаётся историческим фактом, что написал агент при закрытии задачи.
- `evidence` добавляет post-hoc проверяемый след: какие инструкции/проверки нужно учитывать при assurance.
- `assurance.py` остаётся read-only: он ничего не чинит и не утверждает, только читает два источника.

## Результат

До addendum:

```text
applied-evidence: 13/15
T-180: слабое evidence
T-182: слабое evidence
```

После addendum:

```text
applied-evidence: 15/15
Вердикт: PASS
findings: 0
```

## Проверки

```powershell
python tools\test_assurance.py
python tools\assurance.py all
python tools\instructions.py check-report queues\evidence\T-180.evidence.md
python tools\instructions.py check-report queues\evidence\T-182.evidence.md
```

Результат:

- `test_assurance.py` OK
- `assurance.py all` PASS, findings=0
- оба evidence addendum проходят `check-report`

## Ограничения

- Это не strict gate и не разрешение переписывать done-маркеры.
- Это не архитектурное решение; формат можно позже закрепить отдельным proposed decision, если несколько агентов начнут использовать addendum регулярно.
- Addendum должен быть редким исключением. Нормальный путь остаётся `pipeline.py done ... --applied`.

Applied instructions: AGENTS.md, PROTOCOL.md, docs/instruction-assurance.md, tools/assurance.py, tools/test_assurance.py, Checks
Checks: test_assurance.py, assurance.py all, instructions.py check-report T-180/T-182 evidence addenda