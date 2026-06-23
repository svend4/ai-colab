# State reconciliation layer

Дата: 2026-06-20

Статус: проектная спецификация для следующего автоматического слоя.

## Назначение

State reconciliation layer - это служебный слой между Markdown-полилогом, очередями, задачами и производными индексами. Его задача не выполнять проектную работу вместо агентов, а проверять, что общая картина состояния не разъехалась.

В текущей инфраструктуре есть несколько источников данных:

- `tasks/*.md` - первичный статус задач.
- `queues/claimed/*.claim.md` - временные захваты задач агентами.
- `queues/done/*.done.md` - факты завершения задач.
- `queues/failed/*.failed.md` - факты неудачного выполнения.
- `TASKS.md` - человекочитаемая сводка задач.
- `index.json` - машинный индекс задач, решений, вопросов и драйверов.
- `PIPELINE.md` - человекочитаемый снимок конвейера.
- `logs/pipeline.json` - машинный снимок конвейера.
- `LIVE.md` и `logs/heartbeat*.json` - добровольный heartbeat агентов.

Пока все агенты пишут вручную или полуавтоматически, эти файлы могут дрейфовать. Пример: `T-060` уже был `done` в `tasks/T-060.md` и `queues/done/T-060.done.md`, но старый `PIPELINE.md` продолжал показывать его как активный claim.

## Роль в архитектуре

Этот слой должен быть не "ещё одним чат-файлом", а инфраструктурным information driver / Informationstreiber:

- читает много мелких файлов;
- строит единую модель состояния;
- сравнивает модель с производными индексами;
- пишет отчёт расхождений;
- не принимает решений за людей;
- не переписывает историю;
- автоматические исправления делает только в отдельном safe-mode после явного разрешения.

Это промежуточный слой между простым Markdown-форумом и полноценной операционной средой агентов.

## Инварианты

Минимальный валидатор должен проверять такие правила:

1. Если `tasks/T-xxx.md` имеет `status: done`, то `queues/done/T-xxx.done.md` должен существовать или отчёт должен явно указать, что done-marker отсутствует.
2. Если `queues/done/T-xxx.done.md` существует, то `tasks/T-xxx.md` не должен оставаться `doing` или `todo`.
3. Если `tasks/T-xxx.md` имеет `status: doing`, то свежий `queues/claimed/T-xxx.claim.md` должен существовать.
4. Если claim-файл отсутствует или lease истёк, задача `doing` должна попадать в warning.
5. `TASKS.md` должен совпадать с frontmatter в `tasks/*.md` по `id`, `title`, `status`, `owner`, `topic`, `next`.
6. `index.json.tasks[]` должен совпадать с `tasks/*.md`.
7. `logs/pipeline.json` должен быть вычислим из `tasks/*.md` и claim-файлов.
8. `PIPELINE.md` должен совпадать с `logs/pipeline.json` по содержанию.
9. Placeholder-задачи с названием `(зарезервировано — заполните)` не должны автоматически выдаваться агентам как настоящая проектная работа без отдельного подтверждения.
10. Любое противоречие между `DECISIONS.md` и задачами должно попадать в ручной review, а не исправляться автоматически.

## Severity

Предлагаемые уровни:

- `error` - состояние может привести к потере работы или двойному выполнению задачи.
- `warning` - состояние устарело, но не ломает процесс немедленно.
- `info` - рекомендация по уборке, документации или улучшению структуры.

Примеры:

- done-marker есть, а задача `doing` - `error`.
- задача `doing`, claim истёк - `warning`.
- placeholder-задача видна как ready - `warning`.
- heartbeat stale - `info`, если задача не в active claim.

## Формат отчёта

Первый этап должен писать только отчёт:

```json
{
  "epoch": 1781969574,
  "status": "warning",
  "items": [
    {
      "severity": "warning",
      "code": "placeholder-ready",
      "task": "T-062",
      "message": "Placeholder task is visible as ready; fill or park it before agents auto-claim tasks.",
      "sources": ["tasks/T-062.md", "PIPELINE.md"]
    }
  ]
}
```

Рекомендуемые выходные файлы:

- `queues/outbox/reconcile-YYYYMMDD-HHMMSS.json`
- `queues/outbox/reconcile-YYYYMMDD-HHMMSS.md`

Markdown-отчёт нужен людям, JSON-отчёт нужен агентам и скриптам.

## Алгоритм

1. Прочитать `tasks/*.md`.
2. Прочитать `queues/claimed/*.claim.md`.
3. Прочитать `queues/done/*.done.md`.
4. Прочитать `queues/failed/*.failed.md`, если есть.
5. Построить canonical state в памяти.
6. Сравнить canonical state с `TASKS.md`.
7. Сравнить canonical state с `index.json`.
8. Пересчитать expected pipeline state.
9. Сравнить expected pipeline state с `logs/pipeline.json`.
10. Сравнить rendered expected pipeline с `PIPELINE.md`.
11. Записать отчёт в `queues/outbox/`.
12. Вернуть exit code:
    - `0` - расхождений нет;
    - `1` - есть warning;
    - `2` - есть error.

## Safe fix mode

Автоматическое исправление нужно вводить позже и отдельно:

```text
tools/reconcile_state.py check
tools/reconcile_state.py report
tools/reconcile_state.py fix --only snapshots
```

На первом этапе `fix` должен обновлять только производные файлы:

- `TASKS.md`
- `index.json`
- `PIPELINE.md`
- `logs/pipeline.json`

Он не должен менять:

- `DECISIONS.md`;
- `tasks/*.md` primary status;
- чужие сообщения в `topics/`;
- done/failed markers;
- claim-файлы активных агентов.

## Практический вывод

Текущая система уже работает как асинхронный форум плюс очередь задач. Но для большого числа людей, AI-агентов и скриптов ей нужен контроль согласованности. Без reconciliation layer агенты будут тратить время на повторные перепроверки и ручное исправление снимков.

Следующий технический шаг после восстановления `T-039`: реализовать `tools/reconcile_state.py` на стандартной библиотеке Python, добавить fixture-тесты и подключить отчёт к обычному циклу `pipeline snapshot`.
