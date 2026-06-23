---
id: instruction-assurance
type: doc
title: Instruction assurance — проверяемое применение инструкций агентами
status: draft
owner: codex
related: [T-154, T-121, T-122, T-138, T-150]
---

# Instruction assurance

Дата: 2026-06-22.

Назначение: сделать так, чтобы инструкции из основания пирамиды доходили до агента на вершине не как надежда, а как проверяемый рабочий шаг.

## Главный принцип

Количество документов не гарантирует дисциплину. Гарантию даёт цепочка:

```text
metadata -> task-scoped retrieval -> preflight -> evidence -> machine check -> gate
```

Эта цепочка не заменяет мышление агента. Она заставляет агента явно назвать, какие правила применяются к текущей задаче, какие риски есть и какими командами будет проверен результат.

## Что уже было до T-154

- `AGENTS.md` и `PROTOCOL.md` задают роли, зоны записи, append-only режим, D-003 обоснование правок и streams.
- `docs/agent-onboarding.md` объясняет людям и агентам, что система умеет сейчас.
- `docs/top-agent-operating-manual.md` описывает вершину пирамиды и рабочий цикл агента.
- `tools/top.py` уже даёт верхние команды: status, health, take, friction, work-mode, synthesis-helper.
- `tools/friction.py` фиксирует повторяющиеся проблемы и рецепты.

Пробел: не было отдельного машинного отчёта “какие инструкции применимы именно к этой задаче и где evidence, что они были учтены”.

## Новый слой

`tools/instructions.py preflight <agent> [T-id]` собирает task-scoped preflight:

- обязательные правила для любого агента;
- task card и topic текущей задачи;
- правила pipeline/claim/done;
- правила selective-add, commit-lock и streams, если в дереве есть dirty files;
- правила sandbox, если задача говорит про внешний код;
- правила synthesis/fork, если задача говорит про варианты, streams или расхождения;
- evidence-template для outbox/done отчёта.

Команда read-only. Она ничего не утверждает и не принимает решений.

## Evidence-блок

Каждый существенный outbox/done отчёт должен иметь блок:

```md
## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: соблюдена зона записи, чужие сообщения не переписаны.
- `tasks/T-XXX.md`: выполнены критерии done или явно указана недоделка.
- `docs/...`: применены профильные инструкции задачи.
- Commit safety: использован selective-add; `git add -A` не применялся в dirty shared tree.
- Checks: перечислены команды проверки и результат.
```

Это не абсолютная защита от формального отчёта. Но это даёт проверяемый след, который можно читать людям, другим агентам и будущим gate-инструментам.

## Уровни гарантии

| Уровень | Механизм | Что доказывает | Ограничение |
|---|---|---|---|
| Мягкий | onboarding + preflight | агент видел применимые правила | не доказывает качество применения |
| Средний | evidence в отчёте | агент сопоставил правила с действиями | можно заполнить формально |
| Жёсткий | validate/generate/friction/merge_gate | часть правил проверена машинно | покрывает только формализуемые правила |
| Блокирующий | pre-commit / future gate | опасное действие остановлено | требует точных правил, иначе будет мешать |

## Как использовать

Перед задачей:

```powershell
python tools\instructions.py preflight codex T-154
python tools\top.py instruction-preflight codex T-154
```

После задачи:

```powershell
python tools\instructions.py check-report queues\outbox\2026-06-22-instruction-assurance-and-synthesis.md
python tools\pipeline.py done codex T-156 --claim <claim_id> --report "..." --applied "AGENTS.md, PROTOCOL.md, docs/instruction-assurance.md, Checks"
```

`--applied` — мягкий evidence-маркер. Он не блокирует старые задачи, но делает `queues/done/<T-id>.done.md` проверяемым: в front matter появляется поле `applied`, а в теле отчёта — читаемая строка `Applied instructions:`. `tools/instructions.py check-report` принимает оба формата: подробный outbox-блок `## Applied instructions` и короткий pipeline done-маркер. Начиная с T-158, `pipeline.py done` печатает warning для service/governance-задач без `--applied`; это промежуточная стадия перед возможным strict gate. Начиная с T-166, `check-report` дополнительно печатает advisory-находки по ссылкам на repo-файлы и `Checks:` командам; этот слой read-only и не меняет exit-code evidence gate.

## Моё мнение

Правильный следующий шаг — не заставлять каждого агента читать всё подряд, а строить короткий task-scoped preflight. Большая система инструкций должна быть похожа на компилятор: она не просто хранит правила, а выбирает релевантные правила, показывает evidence и постепенно превращает повторяющиеся нарушения в машинные проверки.

## Дальше

1. После нескольких успешных warning-прогонов решить, какие service/governance-задачи можно переводить на strict `--applied` gate.
2. Сделано в T-166 как advisory: `tools/instructions.py check-report` проверяет ссылки на repo-файлы и форму `Checks:` команд без исполнения команд и без ужесточения exit-code.
3. Связать preflight с `merge_gate.py`, но только после нескольких ручных прогонов.
4. Добавить instruction freshness index: `status`, `last_verified`, `applies_to`, `supersedes` для ключевых docs.
