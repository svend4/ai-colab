---
id: information-refactoring-cycle-1-2026-06-25
type: topic
title: Цикл 1: изучение вопросника, новые вопросы и ответы
status: proposed
owner: codex
date: 2026-06-25
related: [T-247, information-refactoring-question-tree-2026-06-25, information-refactoring-sanation-standard]
---

# Цикл 1: изучение вопросника, новые вопросы и ответы

## 0. Машинный снимок вопросника

Команда:

```powershell
python tools/question_tree.py topics/information-refactoring-question-tree-2026-06-25.md --limit 20
```

Результат:

```text
questions: 32
partial: 14
open: 4
requires-decision: 3
solved: 2
unknown: 9
```

Вывод: главный дефицит не в отсутствии мыслей, а в отсутствии регулярного цикла обработки: часть вопросов уже имеет ответ, но не имеет следующего action; часть имеет ответ, но не имеет явного статуса; часть требует решения человека/интегратора.

## 1. Порядок обработки старых вопросов

### 1.1. Группа A — вопросы без явного статуса

**Проблема:** 9 вопросов имеют ответ, но не имеют отдельного `Статус:`. Это не философская, а навигационная проблема: агент не понимает, можно ли считать вопрос закрытым.

**Простое решение:** добавить недостающий статус в исходный question tree.

**Техническое решение:** сделать later-task `question_tree status-backfill`, который предлагает patch, но не применяет его автоматически.

**Осторожность:** не менять исходный смысл ответа. Только добавить status marker.

**Предлагаемый следующий action:** создать отдельную задачу `Question tree status backfill`.

### 1.2. Группа B — частично решённые вопросы

**Проблема:** 14 вопросов уже имеют направление, но не доведены до команды, validator, top-wrapper, decision или документа.

**Принцип:** partial означает не “плохо”, а “созрел для конкретного следующего шага”.

**Проверенный метод настоящего времени:**

1. Для каждого partial вопроса определить тип следующего шага: `doc`, `tool`, `top-command`, `validator`, `decision`, `sandbox-test`.
2. Создать маленькую задачу, а не большой рефакторинг.
3. После выполнения пересчитать question tree.

**Предлагаемый следующий action:** `top.py actions`, `top.py cli-risk`, `START_HERE.md`, `docs/alpha-status.md`.

### 1.3. Группа C — открытые вопросы

**Проблема:** 4 вопроса требуют не кода, а качественного выбора модели.

**Метод:** scholastic disputation — средневековый формат: сначала вопрос, затем objections, затем ответ, затем replies. Он хорошо подходит для спорных методологических тем.

**Как применить:**

```text
Question -> Objections -> Sed contra / доказательства -> Respondeo / ответ -> Replies -> Next action
```

**Предлагаемый следующий action:** для каждого open вопроса создать маленький debate-документ или раздел в topic.

### 1.4. Группа D — requires-decision

**Проблема:** 3 вопроса нельзя закрыть агентом самостоятельно.

**Правило:** agent может подготовить варианты, но не переводить в accepted.

**Следующий action:** создать `Q-...` или `D-... proposed` только после уточнения, какой вопрос действительно требует человеческого выбора.

## 2. Ответы по порядку на ключевые старые вопросы

### 2.1. Как омолаживать репозиторий без переписывания истории?

**Ответ:** через “живую верхушку”: статусы, gist, индексы, top-команды, synthesis-слои и фильтры active/historical. История остаётся телом айсберга, а интерфейс к ней обновляется.

**Что уже есть:** `docs/information-refactoring-sanation-standard.md`, `tools/sanation.py`.

**Что не хватает:** top-команда для sanitation/status и policy historical/superseded.

### 2.2. Что делать с большим черновиком?

**Ответ:** не пытаться сделать весь корпус чистовиком. Нужны разные температурные режимы:

```text
hot active      = нужно видеть наверху
warm reference  = можно найти по индексу
cold historical = не показывать в первом экране
frozen archive  = хранить ради аудита
```

**Что не хватает:** surface budget — сколько файлов должен видеть новый человек или агент в первые минуты.

### 2.3. Где золотая середина между агентом и Windows/ОС?

**Ответ:** в repo-native control plane. ОС даёт файлы, процессы, права, git, PowerShell. Агент даёт смысл, синтез, выбор. Средний слой должен давать команды, индексы, статусы, проверки и безопасные маршруты.

**Практическая форма:** `tools/top.py`, `tools/pipeline.py`, `tools/sanation.py`, `tools/question_tree.py`, `tools/cli_inventory.py`, `tools/action_tracker.py`.

### 2.4. Что было бы сделано иначе с самого начала?

**Ответ:** сначала создать не только папки, а “операционную поверхность”:

1. `START_HERE.md`.
2. `docs/alpha-status.md`.
3. `top.py` как главный фасад.
4. `questions/`, `decisions/`, `tasks/` сразу в атомарном формате.
5. `sandbox/ideas` для экспериментов.
6. `outbox` с footer-правилом с первого дня.
7. advisory validators до hard validators.

## 3. Новые уточняющие вопросы

### 3.1. Вопрос 13.1. Что такое active surface budget?

Сколько файлов, команд и отчётов должен видеть новый человек/агент, чтобы начать работу без погружения в историю?

**Гипотеза:** первый экран должен содержать не более 7±2 крупных входов: статус, next work, tasks, decisions, top commands, sandbox, recent synthesis.

**Следующий action:** создать `docs/alpha-status.md` или `START_HERE.md`.

### 3.2. Вопрос 13.2. Когда идея должна стать документом, skill или tool?

**Гипотеза:**

```text
однократная мысль -> topic/outbox
повторяемая инструкция -> skill/doc
повторяемая проверка -> tool
повторяемый workflow -> top-command
спорный принцип -> proposed decision
```

**Следующий action:** добавить decision-menu или reference table.

### 3.3. Вопрос 13.3. Что такое semantic depreciation?

Идея может быть не ложной, но устаревшей. Она теряет ценность как active guidance, но сохраняет ценность как historical evidence.

**Следующий action:** добавить в sanitation model поле/понятие `semantic_age` или `superseded_by`.

### 3.4. Вопрос 13.4. Как отличить “дикое творчество” от вредного шума?

**Гипотеза:** дикое творчество полезно, если оно проходит sandbox contract:

1. явно помечено как thought experiment;
2. не исполняет код;
3. имеет expected learning;
4. имеет risk note;
5. после эксперимента получает disposition: adopt / adapt / archive / reject.

### 3.5. Вопрос 13.5. Может ли религиозная/философская форма быть технически полезной?

**Ответ:** да, как дисциплина формы, не как догма. Например:

- монастырский скрипторий -> роли copyist/reviewer/indexer;
- схоластический диспут -> objections/replies для спорных решений;
- исповедь ошибок -> friction ledger;
- литургический календарь -> регулярный цикл санации;
- алхимия -> стадии calcination/dissolution/coagulation как метафора разборки, очистки и сборки смысла.

**Ограничение:** метафора должна давать проверяемый workflow, иначе она остаётся литературой.

## 4. Новые качественно другие вопросы

### 4.1. Вопрос 14.1. Может ли репозиторий иметь иммунную систему?

**Идея:** validators, safe_write, sandbox gates и action_tracker — это иммунитет. Они не создают смысл, но защищают организм проекта от потери данных, застоя и токсичного шума.

**Тест:** добавить `top.py immune-status`, который объединяет validate, sanation, action_tracker, cli_inventory.

### 4.2. Вопрос 14.2. Может ли репозиторий иметь пищеварение?

**Идея:** входящие хаотичные идеи попадают в sandbox/inbox, перевариваются через synthesis, полезное поднимается в tasks/tools/docs, остаток уходит в archive.

**Тест:** sandbox idea lab + promotion route.

### 4.3. Вопрос 14.3. Может ли репозиторий иметь сновидения?

**Идея:** controlled fantasy mode: агенты генерируют странные модели, но не применяют их напрямую. Затем observer-agent извлекает из них проверяемые принципы.

**Тест:** `sandbox/ideas` с шаблоном thought experiment.

### 4.4. Вопрос 14.4. Может ли проект иметь “суд”?

**Идея:** для спорных решений делать court format: prosecution, defense, evidence, judge recommendation. Это полезно для governance, где consensus не очевиден.

**Тест:** применить к одному `requires-decision` вопросу из question tree.

### 4.5. Вопрос 14.5. Может ли проект иметь “сад”?

**Идея:** некоторые идеи не нужно строить сразу. Их можно посадить как seeds, периодически поливать проверками, и только зрелые идеи переводить в tasks.

**Тест:** `ideas/seeds` + maturity score.

## 5. Проверенные методы из разных эпох

### 5.1. Средневековые методы

1. **Scriptorium:** один пишет, второй сверяет, третий индексирует.
2. **Scholastic disputation:** вопрос, возражения, ответ, replies.
3. **Guild apprenticeship:** новичок работает через simple tasks, мастер проверяет promotion.
4. **Cathedral building:** проект строится поколениями; важны чертежи, не только камни.
5. **Monastic rule:** короткие повторяемые правила важнее длинных вдохновенных трактатов.

### 5.2. Методы настоящего времени

1. Control plane.
2. Event sourcing.
3. Knowledge graph.
4. Medallion architecture: bronze/silver/gold.
5. CI/CD gates.
6. Issue tracker + ADR.
7. Read-only first, apply later.
8. Test-driven refactoring.

### 5.3. Фантастические методы будущего

1. **Semantic elevator:** идея автоматически поднимается L4 -> L3 -> L2 -> L1 по доказательствам.
2. **Memory compost:** старые отчёты разлагаются на nutrients: facts, decisions, warnings, patterns.
3. **Idea particle accelerator:** сталкивать две несовместимые идеи и извлекать новую модель.
4. **Proof ladder:** любое утверждение поднимается по ступеням evidence: claim -> source -> test -> adoption.
5. **Agent parliament:** разные агенты имеют роли, но accepted decision делает только человек/интегратор.
6. **Dream sandbox:** безопасное место для странных гипотез без прямого влияния на canon.

## 6. Что тестировать в песочнице

### 6.1. Безопасные эксперименты

- thought experiment без кода;
- Markdown-шаблон идеи;
- synthetic mini-corpus;
- read-only parser;
- scoring formula на искусственных данных.

### 6.2. Небезопасные эксперименты

- выполнение чужого кода;
- автоматическая архивация outbox;
- массовые перемещения файлов;
- hard-fail validators на старом корпусе;
- автоматическое accepted decision.

Они требуют отдельного decision/preflight.

## 7. Ближайшие предложения решений

1. `T-next`: `top.py question-tree` wrapper над `tools/question_tree.py`.
2. `T-next`: status-backfill для 9 unknown вопросов, только proposed patch.
3. `T-next`: `sandbox/ideas` workflow и шаблон thought experiment.
4. `T-next`: `START_HERE.md` как human active surface.
5. `T-next`: `docs/alpha-status.md` как текущая стадия и метрики.
6. `T-next`: debate-format для одного requires-decision вопроса.

## 8. Applied instructions

- AGENTS.md: не удалять историю, писать outbox, proposed status.
- cauldron-synthesis: не стирать разногласия; спорное выносить отдельно.
- docs/protocol-machine-layer.md: action items as checkboxes, Applied instructions, Checks.

Checks:
- python tools/test_question_tree.py -> OK
- python tools/question_tree.py topics/information-refactoring-question-tree-2026-06-25.md --limit 20 -> OK
- python tools/generate.py -> OK
- python tools/validate.py -> OK
- python tools/generate.py --check -> OK
