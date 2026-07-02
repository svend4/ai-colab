---
id: OIA-2026-06-24
type: architecture-synthesis
status: proposed
owner: codex
date: 2026-06-24
last_verified: 2026-06-24
layer: L1-L4
related:
  - docs/workspace-pyramid-levels.md
  - docs/engine-state-2026-06-22.md
  - docs/agent-onboarding.md
  - docs/top-layer-command-groups.md
  - docs/top-layer-throughput-methodology.md
  - core/engine-manifest.md
  - decisions/D-016.md
  - decisions/D-017.md
  - decisions/D-018.md
  - decisions/D-021.md
  - decisions/D-022.md
  - decisions/D-023.md
  - questions/Q-014.md
  - questions/Q-016.md
---

# Оптимальная информационная архитектура: ядро, порталы, индексы, карточки файлов

## 00. Карточка документа

**Назначение.** Ответить на фундаментальный вопрос: как бы я спроектировал этот проект заново, если цель — удобная совместная работа людей и нескольких AI-агентов над большим информационным полем, кодом, документацией, внешними источниками и вариантами решений.

**Статус.** `proposed`: это архитектурный синтез и рабочее предложение, а не принятое решение. По D-017/D-018 спорные места нужно выносить в `streams/<topic>/` и принимать через коллективную перепроверку.

**Короткий вывод.** Оптимальная архитектура здесь — не одна большая папка и не один большой агент, а **слоистый информационный двигатель**:

```text
L1 core/       универсальное переносимое ядро
L2 portals/    чистовые специализированные рабочие области
L3 collab/     полилог, задачи, решения, evidence, streams
L4 sandbox/    хаотичный вход, внешние источники, quarantine
indexes/       машинные карты и навигация поверх всех уровней
```

**Главная инженерная мысль.** Чем больше людей и агентов, тем важнее не “ещё один документ”, а повторяемый контракт: у каждого объекта есть ID, карточка, статус, владелец, слой, входы, выходы, проверки, ссылки на evidence и команда, которая показывает актуальное состояние.

## 01. Что уже есть сейчас

### 01.01. Сильная база

В проекте уже есть рабочие элементы правильной архитектуры:

1. `D-016`: принято универсальное ядро + тематические порталы. Домен не должен загрязнять код ядра.
2. `docs/workspace-pyramid-levels.md`: описаны уровни `core/`, `portals/`, логический `collab/`, `sandbox/`.
3. `docs/engine-state-2026-06-22.md`: есть карта текущего движка и команд верхнего слоя.
4. `core/engine-manifest.md`: начат переносимый L1-манифест ядра.
5. `tools/generate.py`, `tools/validate.py`, `tools/drift_check.py`: есть проверяемый канон, а не только ручные тексты.
6. `tools/pipeline.py`, `tools/dispatch.py`, `tools/commit_lock.py`, `tools/worktree.py`, `tools/merge_gate.py`: есть зачатки координационного слоя для многих агентов.
7. `tools/friction.py`, `docs/friction-ledger.md`, `docs/friction-playbook.md`: уже начата бухгалтерия повторяющихся проблем.
8. `tools/portal.py`: портал как тематическая рабочая область поверх универсального знания уже реализуется.
9. `tools/synthesis_helper.py`, `tools/variants.py`, `streams/`: есть механизм “варианты не уничтожать, а синтезировать”.
10. `tools/assurance.py`, `tools/instructions.py`: появилась проверка, применяются ли инструкции и есть ли evidence.

### 01.02. Текущая стадия реализации

**Концептуальная стадия:** примерно `760/1000`. Основные идеи уже сформулированы: пирамида, универсальное ядро, порталы, котёл, streams, worktree, evidence, upper-layer фасад.

**Техническая стадия:** примерно `620/1000`. Многие механизмы уже работают, но они ещё не сведены в единый удобный продуктовый слой. Есть команды, но не все стали привычными “кнопками”. Есть правила, но не все правила проверяются автоматически.

**Операционная стадия:** примерно `580/1000`. Система может работать над самой собой, но пока требует внимательного агента: нужно помнить, когда запускать `generate`, `validate`, `drift_check`, `assurance`, `cohort guard`, `synthesis_helper`.

**Навигационная стадия:** примерно `480/1000`. Документов много, но нет полного стандарта “визитная карточка каждого файла + индекс каждого каталога + карта внутри длинного файла”.

## 02. Что мне не нравится в текущем состоянии

### 02.01. Слишком много знания живёт как текст, а не как активный контракт

Хорошие советы уже есть, но агент может их не использовать. Это значит, что документация пока часто пассивная. Нужно превращать повторяемые правила в:

1. короткий onboarding;
2. команду верхнего слоя;
3. validator/guard;
4. evidence check;
5. generated index.

Пример: “не ждать чужой коммит, уходить в worktree” уже описано, но агент всё равно может забыть. Значит правило должно быть не только в `docs/parallel-work-policy.md`, а в `tools/cohort.py guard`, `tools/top.py`, `assurance.py` и quickstart.

### 02.02. Внутренняя навигация файлов слабее навигации папок

Папки уже имеют структуру, но длинные markdown-файлы часто читаются как линейная простыня. Для людей и AI это плохо: модель тратит контекст на поиск смысла, человек теряет обзор.

Нужна одинаковая схема:

```text
front-matter
00. карточка файла
01. краткая карта
02. основной канон
03. детали
04. evidence / history links
05. next actions
```

### 02.03. Ядро пока описано, но не полностью оформлено как продукт

`core/` должен быть не просто папкой, а переносимым control-plane. Сейчас ядро частично описано в `core/engine-manifest.md`, но вокруг ещё много исторической инфраструктуры L3.

Нужен чёткий критерий:

> L1-файл можно взять в пустой проект, прочитать его карточку, запустить его тесты и понять, что он делает без знания всей истории полилога.

### 02.04. Порталы пока больше “области”, чем полноценные мини-приложения

Правильный портал должен быть не только информационной папкой. Он должен быть маленьким прикладным слоем:

```text
portals/<name>/
  portal.md              identity + manifest + l1_basis
  current-state.md        чистовое состояние
  workflows.md            команды и процессы
  sources.md              источники и intake policy
  glossary.md             термины
  index.md                generated/manual navigation
  reports/                clean reports
  tools/                  optional local wrappers
  tests/                  optional portal checks
```

Если портал не имеет workflows и l1_basis, он остаётся папкой документов, а не рабочим порталом.

### 02.05. Evidence часто добавляется после факта

Задача должна закрываться не “done”, а “done + evidence + tests + links”. Если evidence приходится восстанавливать задним числом, значит pipeline ещё недостаточно строгий.

## 03. Если бы я строил проект заново

### 03.01. Минимальный стартовый каталог

Я бы начал не с большого количества документов, а с такого каркаса:

```text
repo/
  README.md
  AGENTS.md
  PROTOCOL.md
  core/
    engine-manifest.md
    tools/
    tests/
  portals/
    README.md
  collab/
    README.md
  sandbox/
    README.md
  indexes/
    README.md
  tasks/
  decisions/
  questions/
  queues/
  streams/
  tools/
  docs/
```

`collab/` можно оставить логическим слоем, но я бы сразу сделал `collab/README.md`, который перечисляет, что `tasks/`, `decisions/`, `questions/`, `queues/`, `streams/` относятся к L3.

### 03.02. Правило “нет файла без карточки”

У каждого значимого файла была бы верхняя карточка. Для markdown:

```md
---
id: DOC-000
status: draft|proposed|accepted|active|deprecated
layer: L1|L2|L3|L4
owner: codex|claude|human|pool
last_verified: YYYY-MM-DD
related: [...]
---

# Название

## 00. File card

Purpose: ...
Audience: human | agent | script
Inputs: ...
Outputs: ...
Commands: ...
Checks: ...
Next: ...
```

Для Python-файла:

```python
"""
id: TOOL-000
layer: L1
purpose: ...
inputs: ...
outputs: ...
checks:
  - python tools/test_x.py  # [planned] плейсхолдер примера, не реальный файл
"""
```

Если формат файла не поддерживает нормальную шапку, нужен sidecar:

```text
file.ext
file.ext.meta.md
```

### 03.03. Один фасад сверху

Сейчас есть много команд. Это нормально для разработки, но неудобно для человека и нового агента. Сверху должен быть один фасад:

```powershell
python tools\top.py start codex
python tools\top.py status
python tools\top.py next
python tools\top.py guard
python tools\top.py verify
python tools\top.py synthesize <topic>
python tools\top.py friction
python tools\top.py portal <name>
```

Внутри `top.py` может делегировать в `pipeline.py`, `cohort.py`, `assurance.py`, `synthesis_helper.py`, `portal.py`, `friction.py`, но пользователь и агент должны помнить меньше команд.

### 03.04. Строгий split между каноном и историей

Канон настоящего времени:

```text
README.md
core/
portals/
docs/current-*.md
indexes/
```

История и доказательства:

```text
tasks/
decisions/
questions/
queues/
streams/
topics/
reports/
```

Оба слоя нужны. Ошибка — смешивать их в одном документе так, что новый агент не понимает, где текущая инструкция, а где история спора.

### 03.05. Worktree как стандарт для конкурентных изменений

Если несколько агентов пишут одновременно, общий рабочий каталог подходит только для мелких, непересекающихся правок. Для всего, что трогает hot-файлы, индексы, генераторы, `tools/top.py`, порталы или большие docs, я бы сделал default:

```text
shared tree -> только мелкие L0 правки
worktree    -> нормальная разработка
streams     -> варианты мнений и решений
main        -> только синтезированный результат
```

Это устраняет задержку “ждём, пока другой агент закоммитит”. Он не должен блокировать весь процесс. Его работа идёт в своём ручейке, потом проходит merge-gate.

## 04. Архитектура ядра

### 04.01. Ядро как control-plane, а не склад всех функций

Ядро должно быть маленьким и скучным. Оно не должно знать юридический домен, Sven4, конкретного пользователя или конкретный корпус. Оно знает только общие операции:

1. читать канон;
2. валидировать канон;
3. генерировать индексы;
4. выдавать задачи;
5. фиксировать claims;
6. проверять ownership;
7. направлять агента в worktree/stream;
8. собирать evidence;
9. строить portal index;
10. не запускать опасное без gate.

### 04.02. Плоскости ядра

Я бы описывал ядро не как дерево папок, а как набор плоскостей.

| Плоскость | Назначение | Примеры |
|---|---|---|
| Canon plane | источник истины и front-matter | `_canon.py`, `tasks/*.md`, `decisions/*.md`, `questions/*.md` |
| Navigation plane | карты, индексы, быстрый вход | `index.json`, `STATUS.md`, `board.md`, `repo-search`, `knowledge.py` |
| Coordination plane | claims, очередь, claims TTL, dispatch | `pipeline.py`, `dispatch.py`, `flow.py` |
| Parallel plane | не блокировать друг друга | `commit_lock.py`, `worktree.py`, `merge_gate.py`, `cohort.py` |
| Capability plane | драйверы, инструменты, skills | `drivers/`, `tools/`, `.agents/skills/` |
| Evidence plane | доказательства, проверки, применённые инструкции | `instructions.py`, `assurance.py`, `queues/evidence/` |
| Safety plane | риск, permissions, execute off | `risk_gate.py`, `execute_preflight.py`, `permissions.py` |
| Portal plane | домены как плагины | `portal.py`, `portals/*/portal.md` |

### 04.03. Что не должно входить в ядро

В ядро не должны попадать:

1. конкретные внешние репозитории;
2. конкретные документы пользователя;
3. длинные обсуждения;
4. готовые выводы без evidence;
5. execute-runner без принятого human gate;
6. доменные правила, которые нужны только одному порталу;
7. нестабильные эксперименты.

## 05. Архитектура порталов

### 05.01. Портал как тематический plugin

Портал — это не просто папка с текстами. Это доменный слой поверх ядра:

```text
universal core + portal manifest + corpus + workflows + local checks = working portal
```

Портал должен отвечать на вопросы:

1. Что это за область?
2. На какое ядро она опирается?
3. Какие источники разрешены?
4. Какие команды использовать?
5. Какие текущие выводы считаются чистовыми?
6. Где история обсуждения?
7. Какие задачи открыты?
8. Как проверить актуальность?

### 05.02. Минимальная карточка портала

```yaml
id: portal-example
status: active
layer: L2
owner: pool
l1_basis:
  - core/engine-manifest.md
corpus_ref: data/portals/example/corpus
workflows:
  - python tools/portal.py report example
checks:
  - python tools/test_portal.py
last_verified: 2026-06-24
```

### 05.03. Чем портал отличается от темы

`topics/` — это обсуждение и история.  
`portals/` — это чистовая текущая рабочая область.  
`streams/` — это варианты и спорные ручейки.  
`sandbox/` — это вход и quarantine.

Если документ содержит “мы спорили, потом решили”, он L3. Если документ говорит “сейчас делаем так”, он кандидат в L2.

## 06. Метаданные, индексы и расширенное содержание

### 06.01. Две формы каждого знания

Каждое важное знание должно существовать в двух формах:

1. **Короткая машинная форма:** ID, статус, слой, владелец, связи, команды, проверки.
2. **Расширенная человеческая форма:** объяснение, обоснование, примеры, риски, история.

Ошибка — иметь только вторую форму. Человек может прочитать, но машина плохо применяет. Другая ошибка — иметь только JSON/индекс без объяснения. Машина найдёт, но человек не поймёт почему.

### 06.02. Три глубины чтения

Для длинных документов нужна одинаковая глубина:

```text
30 секунд  -> карточка / TL;DR / статус
5 минут    -> карта разделов / решения / команды
30 минут   -> аргументация / детали / evidence / альтернативы
```

Это можно назвать “semantic elevator”: агент или человек должен уметь остановиться на нужном этаже детализации.

### 06.03. Индексы верхнего уровня

Я бы добавил отдельную папку `indexes/` или явно оформил существующие generated-файлы как индексный слой:

```text
indexes/
  files.json              все значимые файлы + карточки
  folders.json            папки, бюджеты, владельцы
  commands.json           команды, назначение, риск, dry-run/run
  questions.json          нормализованные вопросы
  open-loops.json         незакрытые вопросы/долги
  portals.json            порталы и l1_basis
  stale.json              что давно не проверялось
```

Часть уже есть (`index.json`, `STATUS.md`, `board.md`), но нужен более явный file/folder/navigation слой.

## 07. Навигация внутри файла

### 07.01. Абсолютная нумерация разделов

Для больших документов лучше использовать стабильную нумерацию:

```text
00. Карточка
01. Контекст
02. Решение
03. Подробности
03.01. Частный случай
03.02. Частный случай
04. Проверки
05. Разногласия
06. Следующие шаги
```

Плюсы:

1. легче ссылаться в задачах;
2. легче делать diff;
3. легче извлекать sections;
4. легче агентам обсуждать конкретный пункт;
5. можно строить section index.

Минусы:

1. ручное перенумерование раздражает;
2. при частых вставках может быть шумный diff;
3. нужен heading-lint, иначе стандарт быстро расползётся.

Решение: не нумеровать каждый маленький файл, но требовать нумерацию для документов выше порога, например 300 строк или статус `architecture|policy|manual`.

### 07.02. Визитная карточка раздела

В длинных документах полезны не только карточки файла, но и карточки крупных разделов:

```md
## 04. Архитектура ядра

Section card:
- claim: ядро = control-plane
- status: proposed
- evidence: D-016, core/engine-manifest.md
- next: file-card standard + core export check
```

Это особенно полезно для AI, потому можно извлекать section cards без чтения всего текста.

## 08. Размеры папок и файлов

### 08.01. Практическая эвристика

Это не закон, а рабочая эвристика для людей и LLM:

| Объект | Оптимально | Когда делить |
|---|---:|---:|
| Top-level папки | 7-12 | больше 15 требует группировки |
| Активные файлы в human-facing папке | 5-15 | больше 30 нужен index/подпапки |
| Машинная папка generated/logs | 50-500 | если есть индекс и не читается руками |
| Markdown-файл | 200-800 строк | после 1000-1500 строк делить или делать section index |
| Глубина каталогов | 3-5 уровней | больше 6 только для generated/sandbox |
| Задачи в одном обзоре | 10-25 | больше нужны фильтры/status views |
| Команды в quickstart | 5-9 | больше превращать в группы/buttons |

### 08.02. Почему так

Компьютер может читать тысячи файлов. Проблема не в файловой системе. Проблема в когнитивной навигации:

1. человек видит слишком много одинаковых имён;
2. агент тратит контекст на поиск нужного места;
3. риск редактировать не тот файл растёт;
4. generated индексы устаревают незаметнее;
5. длинные документы становятся складом истории вместо текущей инструкции.

### 08.03. Правило для больших папок

Если в папке больше 20 human-facing файлов, нужен `README.md` или `index.md`.

Если больше 50 файлов, нужны подпапки или generated catalog.

Если больше 100 файлов, папка должна быть machine-facing, а человек должен заходить через индекс.

## 09. Список вопросов и степень ответа

Шкала:

```text
0-300   идея зафиксирована, но нет структуры
300-600 описано текстом, но не проверяется
600-800 есть инструменты/команды, частичная автоматизация
800-950 есть tests/gates/evidence, повторяемый процесс
950-1000 переносимо, скучно, стабильно, почти не требует памяти агента
```

| ID | Вопрос | Текущий ответ | Оценка |
|---|---|---|---:|
| OIA-Q001 | Какова оптимальная архитектура с нуля? | L1/L2/L3/L4 + indexes + file cards + top facade | 750‰ |
| OIA-Q002 | Как сделать ядро универсальным? | D-016 принято; core manifest есть; нужен export gate | 720‰ |
| OIA-Q003 | Что такое архитектура ядра? | control-plane из 8 плоскостей, не доменный monolith | 680‰ |
| OIA-Q004 | Как связать краткие метаданные и подробные тексты? | front-matter + file card + section map + generated indexes | 620‰ |
| OIA-Q005 | Как сделать навигацию внутри файла? | предложена абсолютная нумерация и section cards | 430‰ |
| OIA-Q006 | Сколько файлов держать в папке? | есть эвристика, но нет folder-budget tool | 410‰ |
| OIA-Q007 | Как не забывать хорошие советы? | friction ledger + assurance + top commands; нужно больше gates | 690‰ |
| OIA-Q008 | Как работать нескольким агентам без ожидания? | D-021/D-022 worktree/streams; нужны привычные top wrappers | 760‰ |
| OIA-Q009 | Как объединять варианты, а не убивать дубли? | D-017, streams, synthesis_helper; нужно больше регулярного adoption | 700‰ |
| OIA-Q010 | Как сделать порталы не просто папками? | manifest + workflows + l1_basis + checks | 610‰ |
| OIA-Q011 | Как пропускать знание снизу вверх? | promotion gate L4->L3->L2->L1; assurance coverage | 660‰ |
| OIA-Q012 | Какие тесты нужны? | список тестов есть ниже; часть реализована | 580‰ |
| OIA-Q013 | Как оценивать стадию проекта? | conceptual/technical/operational/navigation maturity | 650‰ |
| OIA-Q014 | Как сделать проект удобнее дизайнерски? | top facade/buttons + cards + index maps; UI ещё нет | 420‰ |
| OIA-Q015 | Какие фантастические идеи полезны? | semantic elevator, knowledge city, proof ladder | 350‰ |

## 10. Тесты и проверки, которые я бы ввёл

### 10.01. File-card coverage

Команда будущего:

```powershell
python tools\file_card_check.py
```

Проверяет:

1. есть ли front-matter у значимых markdown;
2. есть ли `id`, `status`, `layer`, `owner`, `last_verified`;
3. есть ли `Purpose/Inputs/Outputs/Checks`;
4. нет ли файла L1 без checks;
5. нет ли accepted policy без related decisions/evidence.

### 10.02. Folder budget

Команда будущего:

```powershell
python tools\folder_budget.py
```

Проверяет:

1. папки с большим числом human-facing файлов;
2. отсутствие README/index;
3. слишком глубокие пути;
4. смешение L1/L2/L3/L4 в одной папке;
5. папки, которые должны стать portal или sandbox.

### 10.03. Section index lint

Команда будущего:

```powershell
python tools\section_index.py docs\optimal-information-architecture-2026-06-24.md
```

Проверяет:

1. есть ли `00. Карточка`;
2. стабильна ли нумерация;
3. есть ли карта разделов;
4. нет ли слишком длинных секций;
5. можно ли извлечь section cards.

### 10.04. Advice activation check

Команда будущего:

```powershell
python tools\advice_activation.py
```

Проверяет, что важные советы не лежат мёртвым текстом:

1. у совета есть источник;
2. есть команда или guard, который его применяет;
3. есть тест/evidence;
4. есть ссылка из onboarding/top-layer;
5. если автоматизации нет, есть задача.

### 10.05. Decision propagation check

Команда будущего:

```powershell
python tools\decision_propagation.py D-016
```

Проверяет, дошло ли решение до:

1. docs;
2. tools;
3. tests;
4. onboarding;
5. portal manifests;
6. assurance checks.

## 11. Как сделать верхний слой сильнее

### 11.01. Верхний слой должен обрабатывать поток, а не только писать

Реальный предел агентов не в том, сколько их можно запустить. Предел в том, сколько результатов верхний слой способен:

1. принять;
2. классифицировать;
3. проверить;
4. сравнить;
5. синтезировать;
6. закоммитить;
7. донести в core/portal/onboarding.

Поэтому верхний слой должен быть не “чатом”, а диспетчерской.

### 11.02. Командные группы как кнопки

Людям и агентам не нужны десятки разрозненных команд. Нужны группы:

| Кнопка | Что делает |
|---|---|
| Start | onboard + status + guard + open tasks |
| Verify | generate --check + validate + drift + assurance |
| Take | pipeline next + claim + task context |
| Worktree | guard + spawn isolated worktree |
| Synthesize | variants + synthesis_helper + divergence skeleton |
| Evidence | check-report + assurance delta |
| Portal | portal report + l1_basis + corpus status |
| Friction | known problems + recipes + relevant checks |

Технически это может быть `tools/top.py` subcommands, later GUI, MCP tool, local web UI или ChatGPT app. Сначала нужен CLI-контракт.

## 12. Проблемы, которые уже встречались, и выводы

| Проблема | Симптом | Что сделали | Что автоматизировать дальше |
|---|---|---|---|
| PowerShell mojibake | русские символы ломаются | UTF-8 encoding / `_ioutil.configure_output()` | console encoding preflight |
| TEMP PermissionError | тесты падают в системном TEMP | `tmp-work/` внутри проекта | helper для всех tests |
| apply_patch blocked | Windows sandbox не даёт patch | PowerShell/.NET UTF-8 fallback | safe edit wrapper |
| index.lock / чужая работа | нельзя ждать другого агента | commit_lock/worktree/merge_gate | top-level auto recommendation |
| stale generated indexes | generate цепляет чужие изменения | D-023 ownership-aware indexes | guard warns + selective generated ownership |
| done без evidence | assurance находит пустой done | queues/evidence addendum | pipeline done требует evidence |
| execute risk | runner нельзя включать сразу | preflight/human gate, execute OFF | full gate before runner |
| docs drift | совет есть, но не применяется | assurance/friction docs | advice activation check |
| duplicate vs variant | агент не должен отказываться от своего варианта | streams + synthesis_helper | automatic divergence scaffolds |
| sandbox external code | Sven4/внешний код нельзя сразу запускать | read-only sandbox intake | generic intake manifest + report |

## 13. Консенсус и разногласия

### 13.01. Консенсус

На основе текущих документов и решений можно считать сильным консенсусом:

1. ядро универсальное, домен через портал (`D-016`);
2. история обсуждения не удаляется, но чистовик должен быть отдельно;
3. варианты не являются дублями и должны синтезироваться (`D-017`);
4. человек утверждает спорные решения (`D-018`);
5. worktree нужен для параллельной разработки (`D-021`, `D-022`);
6. generated indexes нельзя коммитить слепо вместе с чужими изменениями (`D-023`);
7. execute должен оставаться выключенным до полного gate.

### 13.02. Разногласия / открытые вопросы

Эти пункты нужно вынести в будущие `streams/architecture-core/` или отдельные задачи:

1. Делать ли физическую миграцию L3 в `collab/` или оставить логический слой?
2. Нужна ли отдельная папка `indexes/`, если уже есть `index.json`, `STATUS.md`, `board.md`?
3. Нумеровать ли все длинные документы вручную или генерировать section ids автоматически?
4. Должны ли portal-local tools жить в `portals/<name>/tools/` или только в общем `tools/`?
5. Делать ли file cards обязательными для всех файлов или только для L1/L2/policy/manual?
6. Какой минимальный набор L1 core-export считать переносимым продуктом?
7. Нужен ли GUI/кнопки сейчас или достаточно `tools/top.py`?

## 14. Инновационные и “фантастические” идеи, которые полезны практически

### 14.01. Knowledge city

Представить репозиторий как город:

```text
core       = электростанция и водопровод
portals    = районы города
docs       = библиотеки
tasks      = мастерские
queues     = почта
streams    = исследовательские лаборатории
sandbox    = порт и таможня
indexes    = карта города
```

Польза не в метафоре, а в навигации: у каждого района есть карта, вход, правила и ответственный.

### 14.02. Proof ladder

Любое утверждение проходит лестницу:

```text
idea -> note -> task/question -> proposed doc -> evidence -> test -> accepted decision -> core/portal adoption
```

Если ступень пропущена, `assurance.py` должен показывать это как gap.

### 14.03. Semantic elevator

У каждого важного документа три версии внутри одного файла или рядом:

```text
10 words   -> метка
100 words  -> executive summary
1000 words -> рабочее объяснение
full       -> детали/evidence
```

Это ускоряет и людей, и AI.

### 14.04. Information drivers / трайберы

“Информационный драйвер” должен быть маленькой способностью с manifest:

```text
drivers/<name>/
  manifest.md
  README.md
  tool.py
  test_tool.py
  examples/
```

Он не обязан сразу быть MCP или плагином. Сначала это может быть passive/active file bundle: манифест + команда + тест + риски. Когда повторяется в двух порталах, можно поднимать в core.

## 15. Следующая карта работ

### 15.01. Ближайшие задачи

1. **File-card standard.** Создать `docs/file-card-standard.md` и шаблоны для markdown/python/portal/task.
2. **File-card checker.** Реализовать `tools/file_card_check.py` [planned] в read-only режиме.
3. **Folder budget report.** Реализовать `tools/folder_budget.py` [planned] без автоправок.
4. **Top verify bundle.** Добавить или проверить команду `python tools/top.py verify`, которая запускает стандартный набор проверок.
5. **Advice activation.** Начать `docs/advice-activation.md`: какие советы уже автоматизированы, какие нет.
6. **Architecture stream.** Создать `streams/architecture-core/` для альтернативных вариантов по спорным пунктам.
7. **Portal v2 contract.** Уточнить обязательные поля `portal.md`: `l1_basis`, `corpus_ref`, `workflows`, `checks`, `last_verified`.
8. **Evidence-required done.** Сделать так, чтобы служебные задачи не закрывались без evidence.

### 15.02. Средний этап

1. Сформировать `indexes/files.json` из file cards.
2. Сформировать `indexes/commands.json` из docstrings/tools metadata.
3. Связать `assurance.py` с `last_verified` и file-card coverage.
4. Добавить section index для длинных policy/architecture/manual docs.
5. Включить folder budget warnings в top/start.
6. Сделать portal dashboard report: текущее состояние, источники, stale docs, open questions.

### 15.03. Дальняя стадия

1. Local UI или web-dashboard поверх `tools/top.py buttons --json`.
2. MCP/ChatGPT app wrapper для верхнего слоя.
3. Автоматический “advice miner”: поиск советов в старых outbox/topics и предложение новых friction rules.
4. Multi-agent synthesis queue: агент-продюсер пишет вариант, synthesis-agent строит consensus/divergence, integrator принимает.
5. Portable core package: минимальный экспорт L1 как отдельный reusable engine.

## 16. Моё итоговое мнение

Проект уже прошёл стадию “папка для полилога” и стал прототипом информационного двигателя. Его главная сила — не в одном скрипте, а в связке: канон, индексы, задачи, решения, streams, worktree, evidence, порталы, sandbox.

Главная слабость — знания стало больше, чем привычных входов в него. Поэтому следующий скачок должен быть не в добавлении ещё десяти документов, а в превращении существующих правил в активные верхние команды, file cards, indexes и gates.

Если сказать коротко: дальше нужно строить не “больше текста”, а **самоописывающийся, самопроверяющийся каталог способностей**. Текст остаётся, но каждый важный текст получает ID, карточку, слой, проверку и путь применения.