---
id: triadic-fractal-methodology
type: doc
title: Методология триадного фрактала золотой середины
status: proposed
owner: codex
created: 2026-06-25
related: [T-251, Q-021, triadic-golden-mean-questionnaire-2026-06-25, agent-approval-matrix, card-standard]
---

# Методология триадного фрактала золотой середины

## 0. Карточка файла

- Назначение: описать, как формулировать проблемы до ответов, чтобы затем их можно было автоматически классифицировать, обсуждать и переводить в задачи/решения/инструменты.
- Статус: proposed. Это методологический черновик, не accepted decision.
- Основная формула: любой объект рассматривается в трёх масштабах — частный, средний/гибридный, глобальный.
- Связанные механизмы: `tools/card.py` как фрактальная карточка, `tools/heading_check.py` как файл-дерево, `tools/question_tree.py` как извлечение вопросов.

## 1. Исходная идея

Первичная идея проекта: нужна золотая середина между верхушкой, где работает человек или AI-агент, и основанием, где находится операционная система, файлы, код, логи, внешние репозитории, скрипты и история.

Эта середина не должна быть только одним слоем между агентом и Windows. Она должна повторяться внутри каждого элемента системы:

```text
частный случай -> средний/гибридный случай -> глобальный случай
```

Такой принцип можно рассматривать как фрактал: та же тройка повторяется в skills, plugins, tools, scripts, files, metadata, code, памяти, workflow, ролях агентов и принятии решений.

## 2. Почему триада

Триада полезна не потому, что всё в мире обязано иметь ровно три части, а потому что она заставляет задавать три разных вопроса:

1. Что происходит в малом частном случае?
2. Что происходит в среднем гибридном случае, где встречаются несколько частных случаев?
3. Что происходит в глобальном общем случае, где нужна каноническая политика или общий механизм?

Если оставить только частное, система распадается на локальные исключения. Если оставить только глобальное, система становится жёсткой и плохо видит контекст. Средний слой нужен как портальная, кластерная, гибридная память.

## 3. Фрактальная модель

### 3.1. Схема

```text
GLOBAL
  MESO / HYBRID
    LOCAL
```

Или в треугольной форме:

```text
        global
       /      \
   meso------local
```

Фрактал Серпинского подходит как образ: каждый треугольник может быть разложен на три меньших треугольника. Но для реальной архитектуры одного фрактала мало: дополнительно нужен граф связей, потому объекты имеют не только вложенность, но и перекрёстные отношения.

Практический вывод:

- Серпинский = хорошая модель самоподобной триады.
- Граф = хорошая модель реальных связей между файлами, ролями, задачами и инструментами.
- Каталог/дерево = хорошая модель навигации от общего к частному.

## 4. Триада артефактов

| Тип | Частный уровень | Средний/гибридный уровень | Глобальный уровень |
|---|---|---|---|
| Skill | локальный рецепт для одной задачи | project skill, повторяемый workflow | переносимый plugin/marketplace skill |
| Plugin | узкий connector/tool bundle | project plugin с несколькими related skills/tools | глобальный пакет для многих проектов |
| Tool | one-shot CLI | top-wrapper / composite command | workflow engine / reusable subsystem |
| Script | маленькая проверка | связанный pipeline step | инфраструктурный сервис/validator |
| File | отдельный документ/код | portal/cluster summary | canonical core/policy/index |
| Metadata | id/type/status | relation/action/evidence fields | schema/governance/index contract |
| Code file | function/local helper | public API + grouped modules | package/tool interface |
| Memory | память агента | portal/cluster memory | global project memory/index |
| Agent | scout | observer/integrator | main/human governance |
| Question | локальный вопрос | кластер вопросов | decision/governance problem |

## 5. Иммунная память

Иммунная память проекта — это не только список ошибок. Это память нормы и отклонений.

Три уровня:

1. По-агентная память: что конкретный агент уже видел, где ошибался, какие рецепты использовал.
2. Кластерная/портальная память: что происходит в группе агентов, файлов, tools, workflow или темы.
3. Глобальная память: accepted/proposed decisions, policies, validators, indexes.

Когда связка агентов, кода, скриптов или файлов ведёт себя непредсказуемо, вопрос не должен сразу звучать как “это ошибка?”. Сначала нужна триадная проверка:

```text
это частный сбой? -> это новая кластерная закономерность? -> это глобальная норма/новация?
```

Возможные классификации:

- anomaly: отклонение от нормы, нужно исправить;
- innovation: новая полезная возможность, нужно оформить;
- variant: альтернативный способ, нужно сохранить как stream/вариант;
- drift: старое правило больше не соответствует практике;
- noise: повтор без новой информации.

## 6. Как формулировать авто-отвечаемый вопрос

Вопрос должен иметь минимум:

```text
id: устойчивый номер
object: что классифицируем
scale: local / meso / global / triad
artifact_type: skill/plugin/tool/script/file/metadata/code/memory/agent/question
question: сама формулировка
status: open / partial / solved / requires-decision
expected_output: answer / task / decision / tool / lint / sandbox experiment
next_action: что делать после извлечения
```

Человеческий Markdown-вариант:

```md
**Вопрос 2.1.** Какие виды skills существуют в триаде?

**Объект:** skill
**Масштаб:** triad
**Ожидаемый выход:** classification + examples + next task
**Статус:** open.
```

Такой вопрос уже может быть извлечён `tools/question_tree.py` и превращён в action-plan.

## 7. Три уровня внутри файла

Q-021 уже закрепил принцип “файл как дерево”: метаданные/карточка -> тело -> хвост, общее -> частное.

Для Markdown это естественно:

1. Верх: front matter, карточка, summary, ToC.
2. Середина: основные разделы, краткие ответы, таблицы.
3. Низ: детали, evidence, logs, appendix.

Для Python это сложнее, потому язык и tooling ожидают исполняемый порядок. Но триада всё равно возможна как convention:

1. Верх: file id card, docstring, imports, constants, CLI help, public API list.
2. Середина: public functions/classes, orchestration functions, parse/build/report functions.
3. Низ: private helpers, adapters, main, test fixtures or implementation details.

Важно: не нужно насильно ломать Python ради пирамиды. Нужно сделать навигационный стандарт, который помогает людям и агентам понимать файл.

## 8. Что делать с разными вариантами

Разные варианты часто не являются дублями. Они могут быть разными случаями при разных условиях.

Правило:

```text
same topic != duplicate
same topic + different condition = variant
same topic + same condition + no new evidence = duplicate noise
same topic + incompatible claim = divergence
same topic + independent evidence = confirmation
```

Поэтому вопросник должен хранить условия применимости:

- где это работает;
- при каком масштабе;
- какой risk;
- какой owner;
- какой next action;
- что считается evidence.

## 9. Следующие уровни автоматизации

### 9.1. Минимальный уровень

- Нормализовать вопросы в `**Вопрос X.Y.**`.
- Добавить `**Статус:**`.
- Использовать `python tools\top.py question-tree <file> --action-plan`.

### 9.2. Средний уровень

- Добавить triad fields: object, scale, artifact_type, expected_output.
- Сделать `tools/triad_lint.py` [planned], который проверяет наличие triad fields.
- Связать с `tools/card.py`.

### 9.3. Глобальный уровень

- Ввести canonical triad schema.
- Добавить portal memory indexes.
- Использовать triad classification в `top.py actions`, synthesis и approval matrix.

## 10. Новые вопросы

1. Достаточно ли триады local/meso/global или нужно 5-7 уровней для сложных случаев?
2. Когда средний уровень является порталом, а когда просто кластером?
3. Как отличать hybrid innovation от drift/bug?
4. Какие поля triad-question должны быть strict, а какие advisory?
5. Нужно ли делать `triad_lint.py` до `top.py actions` или после?
6. Как связать triad-memory с существующим `workbench.db`?
7. Должна ли каждая skill иметь local/meso/global maturity tag?
8. Должен ли каждый tool иметь triad scope: one-shot / composite / engine?

## 11. Independent-first variants as triad

Новая политика `D-028` является прикладным случаем этой методологии:

```text
local/private    -> агент пишет свой независимый вариант
meso/portal      -> streams/<topic>/ собирает несколько вариантов и evidence
global/canonical -> consensus/adopted mainline после synthesis
```

Вывод: похожий вопрос не должен автоматически сниматься как дубль. Сначала вариант раскрывается, затем сравнивается. Повторяющиеся пункты становятся подтверждением consensus, а отличия становятся материалом для `divergence-detail`.
## 12. Applied instructions

- AGENTS.md: proposed methodology, no accepted decision.
- PROTOCOL.md: работа оформлена через T-251.
- cauldron-synthesis: варианты не стираются; different case != duplicate.
- Q-021: файл-как-дерево используется как уже существующая опора.

## Checks

- OK: `python tools\top.py question-tree topics\triadic-golden-mean-questionnaire-2026-06-25.md --action-plan --limit 20` -> 31 questions; 3 requires-decision, 14 open, 12 partial, 2 solved.
- OK: `python tools\heading_check.py docs\triadic-fractal-methodology.md` -> 0 findings.
- OK: `python tools\question_tree.py topics\triadic-golden-mean-questionnaire-2026-06-25.md --json` -> `unknown: 0`.
- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> `OK=12 WARN=0 ERROR=0`.
- OK: `python tools\generate.py --check`
