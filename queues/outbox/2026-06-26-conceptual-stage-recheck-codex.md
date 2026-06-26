---
type: audit
title: Conceptual stage recheck - current implementation and development direction
date: 2026-06-26
author: codex
status: outbox
scope:
  - conceptual coverage
  - implementation stage
  - answer coverage
  - proposal quality
  - innovation and practical next steps
---

# Концептуальная перепроверка текущей стадии

## Короткий вердикт

Текущая стадия сильная, но ее нельзя честно назвать завершенной реализацией.
Это стадия **архитектурно собранного направления + первого исполняемого каркаса**.

Главный удачный поворот: проект не пытается копировать Zed GUI или изобретать
новый редактор. Он формулирует более подходящую для этого репозитория цель:

```text
file-native offline/headless workbench поверх существующего канона
```

Это не "велосипед заново". Это попытка приделать к уже работающему файловому
канону крылья: thread history, task/worktree/outbox/checks в одной карточке,
независимые варианты, синтез разногласий, безопасные песочницы и проверяемый
governance.

Но крылья еще не установлены полностью. `thread.py` уже есть и проходит тест,
а `workspace-cell`, terminal-thread descriptor, local LLM adapter, context-recall
acceptance и тонкая dashboard-поверхность пока остаются следующими шагами.

## Что проверено

- `docs/zed-like-headless-workbench-mvp.md`
- `topics/zed-multiplayer-agents-analysis-2026-06-26.md`
- `topics/repo-as-collaborative-dev-service-2026-06-26.md`
- текущий `index.json`
- текущий `TASKS.md`
- `tools/thread.py --help`
- `tools/test_thread.py`
- `tools/pipeline.py status`
- `tools/generate.py --check`
- `tools/validate.py`

Фактические проверки на момент перепроверки:

- `python tools\validate.py`: `OK=12 WARN=0 ERROR=0`
- `python tools\generate.py --check`: все основные генерируемые файлы актуальны
- `python tools\test_thread.py`: `TESTS OK thread: init/add-message/add-output/status`
- `python tools\pipeline.py status`: 0 задач в работе, но `T-264` все еще показана как ready/todo

Последний пункт важен: реализация `T-264` фактически появилась, но учетная стадия
задачи не сведена с фактом.

## Покрытие вопросов

По машинному индексу:

- всего вопросов: 23
- answered: 22
- open: 1

Открытый вопрос:

```text
Q-023: Какая матрица полномочий нужна для людей и AI-агентов?
```

На него уже есть содержательный proposed-ответ через `D-027`, но это не то же
самое, что принятое решение. Поэтому формулировка такая:

- почти все поставленные вопросы получили ответы;
- последний открытый вопрос концептуально закрыт черновиком;
- формально он остается незакрытым, пока человек или назначенный интегратор не
  примет, отклонит или уточнит `D-027`.

Дополнительно важные proposed-решения:

- `D-024`: Structured Divergences
- `D-026`: безопасность массовой информации
- `D-027`: матрица полномочий
- `D-028`: independent-first variants
- `D-030`: independent-consensus

Эти решения дают хорошую концептуальную основу, но пока не являются accepted.

## Покрытие тем

Темы 2026-06-26 в индексе в основном имеют статус `proposed`, включая:

- Zed/headless workbench
- offline/headless MVP
- repo as collaborative-dev-service
- `.inf` / infon cross-pollination
- TVCP/live repo evaluation
- text diffusion canvas
- MMORPG/2D text workbench
- local multi-agent governance через consensus/divergence

Вывод: темы не брошены. По большинству есть предложения, варианты и границы.
Слабое место не в отсутствии идей, а в том, что их слишком много и они пока не
сведены в один принятый маршрут.

Самая зрелая линия сейчас:

```text
thread.py -> workspace-cell -> context recall test -> terminal-thread descriptor
-> draft-code sandbox -> local LLM adapter -> thin dashboard
```

Менее зрелые, но перспективные линии:

- `.inf`/block/view идеи как источник для typed blocks, stable ids, saved views;
- CRDT/field+line merge как технический слой конкурентной записи;
- textscene/MMORPG/canvas как будущая визуальная или навигационная метафора.

## Стадия реализации

### Уже реально работает

- базовый канон: tasks/questions/decisions/topics/docs;
- генерация `STATUS.md`, `board.md`, `index.json`, `indexes/topics.md`;
- валидация основных структур;
- pipeline-статус;
- `tools/thread.py` как stdlib-only файловый registry;
- тест `tools/test_thread.py`;
- CRDT/merge-инструменты как локальная техническая линия, судя по файлам
  `crdt_merge.py`, `seq_merge.py`, `git_reconcile.py` и связанным темам.

### Работает частично или требует сведения

- `T-264`: код и тест есть, но task/pipeline все еще считают задачу `todo`;
- CRDT-слой: инструменты есть, но документы расходятся в языке статуса.
  Одни тексты говорят "CRDT-слой построен", другие говорят "CRDT позже после
  thread/workspace-cell". Более строгая оценка: field/line merge tooling есть,
  full sequence-CRDT и продуктовая интеграция еще не завершены.

### Пока не реализовано как приемочный слой

- `workspace-cell` aggregator;
- `top.py workspace-cell <id> --json`;
- terminal-thread descriptor и transcript convention;
- local LLM adapter;
- `thread ask` dry-run/local;
- context/view recall acceptance test;
- thin dashboard/portal над workspace-cell;
- единый "полный тест" для всего проекта.

## Качество концепции

Сильные стороны:

- Правильно найден ближайший недостающий объект: не GUI, не модель, не полный
  CRDT, а durable `thread` и затем `workspace-cell`.
- Архитектура уважает уже работающий файловый канон и Git, вместо того чтобы
  строить отдельную закрытую систему.
- Governance не отложен "на потом": independent-first, divergence, quorum,
  red-team и proposed матрица полномочий встроены в мышление проекта.
- Есть ясная безопасность: execute закрыт, local LLM не обязателен, mainline-код
  только через sandbox/worktree/review.
- Внешние идеи Zed, `.inf`, TVCP используются как паттерны, а не как слепое
  копирование.

Слабые стороны:

- Слишком много proposed-тем одновременно. Это снижает читаемость и затрудняет
  выбор следующего шага.
- Есть терминологическое расползание: Zed-like workbench, collaborative-dev-service,
  `.inf`, TVCP, textscene, MMORPG, CRDT, workspace-cell. Все они полезны, но их
  надо сжать в одну дорожную карту.
- Статус реализации местами завышается текстами. Особенно вокруг CRDT: tooling
  есть, но "готовый слой" требует жесткой приемки.
- Нет одного принятого governance-решения по полномочиям людей, AI-агентов,
  observer/integrator и скриптов.
- Технический тестовый контур все еще неоднороден: базовые валидаторы зеленые,
  но полный pytest-контур из предыдущего аудита не является рабочей единой
  проверкой без дополнительных зависимостей и таймаутов.

## Инновационность и практическая ценность

Концепция выглядит качественной и достаточно новой именно в своем сочетании:

```text
plain-text canon + git + append-only multi-agent protocol
+ durable threads + workspace-cell
+ independent variants + semantic synthesis
+ field/line merge tooling
+ sandbox/worktree safety
```

Отдельно эти элементы не уникальны. Сильная часть проекта в композиции: не
"AI-чат в редакторе", а проверяемая операционная среда для многих агентов и
людей, где состояние остается обычными файлами.

Лучшие "крылья", которые действительно стоит приделывать сейчас:

1. `workspace-cell` как кабина управления одной работой.
   Она должна показывать task, claim, thread, stream, worktree, outbox, checks,
   blockers и next command.

2. Context/view recall acceptance.
   Нужно доказать, что сохраненный view или terminal-thread не теряет важный
   факт, зависимость или исключение вне первого видимого среза.

3. Semantic runway.
   Единая видимая цепочка: independent variants -> consensus -> divergences ->
   proposed decision -> accepted decision -> implementation task.

4. Draft-code sandbox.
   Агентам нужно место, где можно развивать смелый вариант полностью, но без
   риска сломать mainline или выдать черновик за принятое решение.

5. Thin dashboard только после JSON.
   Сначала `top.py workspace-cell --json`, затем HTML/TUI/GUI. Иначе есть риск
   построить красивую доску без надежного состояния.

## Ответ на главный вопрос

На поставленные вопросы в основном даны ответы. На заявленные темы в основном
даны предложения и варианты. Качество концепции высокое: она не сводится к
копированию Zed, `.inf` или Git workflow, а пытается собрать практичный
file-native multi-agent workbench.

Но текущая стадия еще не доказывает, что все это "хорошо работает" как цельный
продукт. Она доказывает, что:

- направление выбрано разумно;
- первая сущность `thread` реализована;
- базовый канон валидируется;
- есть мощный набор proposed-решений;
- следующий bottleneck понятен.

Критический bottleneck сейчас:

```text
workspace-cell + принятие/сведение proposed-решений
```

Без этого проект останется богатым архивом хороших идей. С этим он начнет
становиться настоящим рабочим местом для людей и агентов.

## Рекомендуемые следующие действия

1. Свести `T-264`: либо перевести в done/review с отчетом, либо split на
   "implemented thread.py" и "hardening/documentation".
2. Создать следующую задачу: `workspace-cell read-only aggregator`.
3. Добавить задачу: `view/context recall acceptance test`.
4. Синтезировать темы 2026-06-26 в один roadmap-документ с тремя статусами:
   accepted now, proposed later, research only.
5. Ратифицировать или уточнить `D-027`, `D-028`, `D-030`.
6. Зафиксировать статус CRDT: prototype/tooling, accepted merge layer, или
   research branch. Не смешивать эти уровни в текстах.
7. Ввести один официальный full-test сценарий: что считается полной проверкой,
   какие зависимости нужны, какие long tests optional.

