---
id: synthesis-architecture-core-2026-06-24
topic: architecture-core
type: document-synthesis
status: proposed
agent: codex
date: 2026-06-24
documents: 10
---

# Синтез документов: architecture-core

> proposed — это материал для котла по D-017/D-018. Документ выделяет общий слой, похожие варианты и разногласия, но не принимает accepted-решение.

## 00. Corpus

| # | Файл | Заголовок |
|---:|---|---|
| 1 | `docs/optimal-information-architecture-2026-06-24.md` | Оптимальная информационная архитектура: ядро, порталы, индексы, карточки файлов |
| 2 | `docs/workspace-pyramid-levels.md` | Workspace pyramid levels |
| 3 | `docs/top-layer-throughput-methodology.md` | Методология верхнего слоя |
| 4 | `docs/top-layer-command-groups.md` | Top layer command groups — панель вершины пирамиды |
| 5 | `docs/orchestration-architecture-2026-06-23.md` | Архитектура оркестрации воркфлоу |
| 6 | `docs/workflow-conveyor-policy.md` | Политика конвейера воркфлоу |
| 7 | `docs/agent-capacity-methodology.md` | Методология динамической ёмкости агентов |
| 8 | `docs/agent-onboarding.md` | Онбординг и карта возможностей — что система умеет СЕЙЧАС (чистовик) |
| 9 | `queues/outbox/2026-06-23-lagrange-nested-system.md` | Lagrange: вложенная система агентов |
| 10 | `queues/outbox/2026-06-23-lagrange-nested-system-continuation.md` | Lagrange: practical nested agent architecture |

## 01. Две рабочие полосы котла

### 01A. ratify-build — уже достаточно сходится, нужно ратифицировать и строить

| ID | Evidence | Refs | Что делать дальше |
|---|---|---|---|
| evidence-assurance | 10/10 docs | `docs/optimal-information-architecture-2026-06-24.md:32`, `docs/optimal-information-architecture-2026-06-24.md:39`, `docs/optimal-information-architecture-2026-06-24.md:44`, `docs/workspace-pyramid-levels.md:33`, `docs/workspace-pyramid-levels.md:151`, +3 | Ratify evidence-required closure, then enforce it in pipeline/assurance gates. |
| safety-execute-off | 10/10 docs | `docs/optimal-information-architecture-2026-06-24.md:40`, `docs/optimal-information-architecture-2026-06-24.md:53`, `docs/optimal-information-architecture-2026-06-24.md:57`, `docs/workspace-pyramid-levels.md:5`, `docs/workspace-pyramid-levels.md:17`, +3 | Ratify execute boundary, then keep runner work behind human/backend gates. |
| top-layer-facade | 10/10 docs | `docs/optimal-information-architecture-2026-06-24.md:54`, `docs/optimal-information-architecture-2026-06-24.md:65`, `docs/optimal-information-architecture-2026-06-24.md:67`, `docs/workspace-pyramid-levels.md:31`, `docs/top-layer-throughput-methodology.md:4`, +3 | Ratify command-group vocabulary, then wire a top.py wrapper/bundle. |
| layered-pyramid | 9/10 docs | `docs/optimal-information-architecture-2026-06-24.md:8`, `docs/optimal-information-architecture-2026-06-24.md:37`, `docs/optimal-information-architecture-2026-06-24.md:38`, `docs/workspace-pyramid-levels.md:5`, `docs/workspace-pyramid-levels.md:9`, +3 | Ratify the L1/L2/L3/L4 contract, then build folder/layer budget checks. |
| metadata-indexes | 9/10 docs | `docs/optimal-information-architecture-2026-06-24.md:26`, `docs/optimal-information-architecture-2026-06-24.md:28`, `docs/optimal-information-architecture-2026-06-24.md:41`, `docs/workspace-pyramid-levels.md:139`, `docs/top-layer-throughput-methodology.md:121`, +3 | Ratify metadata/index scope, then build file/folder/command index checks. |
| parallel-worktree | 9/10 docs | `docs/optimal-information-architecture-2026-06-24.md:57`, `docs/optimal-information-architecture-2026-06-24.md:65`, `docs/optimal-information-architecture-2026-06-24.md:85`, `docs/top-layer-throughput-methodology.md:48`, `docs/top-layer-throughput-methodology.md:51`, +3 | Ratify worktree/merge-gate triggers, then improve guard/top recommendations. |
| synthesis-divergence | 9/10 docs | `docs/optimal-information-architecture-2026-06-24.md:30`, `docs/optimal-information-architecture-2026-06-24.md:32`, `docs/optimal-information-architecture-2026-06-24.md:39`, `docs/workspace-pyramid-levels.md:16`, `docs/workspace-pyramid-levels.md:31`, +3 | Ratify the split of consensus vs divergence, then integrate doc_synthesis with streams/top.py. |
| workflow-conveyor | 9/10 docs | `docs/optimal-information-architecture-2026-06-24.md:119`, `docs/optimal-information-architecture-2026-06-24.md:128`, `docs/optimal-information-architecture-2026-06-24.md:323`, `docs/workspace-pyramid-levels.md:81`, `docs/workspace-pyramid-levels.md:92`, +3 | Ratify intake/verify/synthesize/integrate wording, then connect to conveyor status/drain tasks. |
| recursive-self-improvement | 8/10 docs | `docs/optimal-information-architecture-2026-06-24.md:58`, `docs/optimal-information-architecture-2026-06-24.md:69`, `docs/optimal-information-architecture-2026-06-24.md:227`, `docs/workspace-pyramid-levels.md:212`, `docs/top-layer-throughput-methodology.md:47`, +3 | Ratify advice activation path, then mine friction/advice into tools and guards. |

### 01B. divergence-detail — ещё не готово, нужно детализация/варианты/доказательства

| ID | Evidence | Refs | Что делать дальше |
|---|---|---|---|
| universal-core-portals | 5/10 docs | `docs/optimal-information-architecture-2026-06-24.md:15`, `docs/optimal-information-architecture-2026-06-24.md:26`, `docs/optimal-information-architecture-2026-06-24.md:37`, `docs/workspace-pyramid-levels.md:5`, `docs/workspace-pyramid-levels.md:9`, +3 | Clarify why accepted D-016 is under-propagated in newer architecture docs. |
| file-section-cards | 2/10 docs | `docs/optimal-information-architecture-2026-06-24.md:26`, `docs/optimal-information-architecture-2026-06-24.md:28`, `docs/optimal-information-architecture-2026-06-24.md:44`, `docs/agent-onboarding.md:13` | Collect more variants, define minimum card schema, then decide coverage scope. |
| DVG-001 | open divergence | — | Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists. |
| DVG-002 | open divergence | — | Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists. |
| DVG-003 | open divergence | — | Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists. |
| DVG-004 | open divergence | — | Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists. |
| DVG-005 | open divergence | — | Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists. |
| DVG-006 | open divergence | — | Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists. |
| DVG-007 | open divergence | — | Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists. |

Пропорция работы выбирается агентом/человеком: 50/50 для балансировки, 70/30 если нужно быстрее строить consensus-ready, 30/70 если главная ценность сейчас в детализации разногласий.

## 02. Верхний слой: полный или сильный консенсус

### layered-pyramid — Слои L1/L2/L3/L4 и разделение чистовика/истории/хаоса (9/10)
- Общее утверждение: Рабочая область должна разделять переносимое ядро, порталы, полилог/evidence и входной хаос.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`, `queues/outbox/2026-06-23-lagrange-nested-system.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:8`, `docs/optimal-information-architecture-2026-06-24.md:37`, `docs/optimal-information-architecture-2026-06-24.md:38`, `docs/workspace-pyramid-levels.md:5`, `docs/workspace-pyramid-levels.md:9`, +18
- Ещё источников: 1

### top-layer-facade — Верхний слой как фасад/панель команд (10/10)
- Общее утверждение: Людям и агентам нужен один верхний фасад команд вместо памяти о десятках скриптов.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:54`, `docs/optimal-information-architecture-2026-06-24.md:65`, `docs/optimal-information-architecture-2026-06-24.md:67`, `docs/workspace-pyramid-levels.md:31`, `docs/top-layer-throughput-methodology.md:4`, +19
- Ещё источников: 2

### workflow-conveyor — Конвейер, workflow, fan-out/fan-in, drain before refill (9/10)
- Общее утверждение: Параллельные агенты полезны только при дисциплине intake -> verify -> synthesize -> integrate.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:119`, `docs/optimal-information-architecture-2026-06-24.md:128`, `docs/optimal-information-architecture-2026-06-24.md:323`, `docs/workspace-pyramid-levels.md:81`, `docs/workspace-pyramid-levels.md:92`, +21
- Ещё источников: 1

### synthesis-divergence — Варианты не удалять: synthesis + divergence streams (9/10)
- Общее утверждение: Повторы и варианты надо сравнивать, а спорные пункты выносить в отдельные divergence-документы.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:30`, `docs/optimal-information-architecture-2026-06-24.md:32`, `docs/optimal-information-architecture-2026-06-24.md:39`, `docs/workspace-pyramid-levels.md:16`, `docs/workspace-pyramid-levels.md:31`, +22
- Ещё источников: 1

### evidence-assurance — Evidence, assurance, checks, applied instructions (10/10)
- Общее утверждение: Задачи и инструкции должны закрываться доказательно: checks, evidence, assurance, drift/validate.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:32`, `docs/optimal-information-architecture-2026-06-24.md:39`, `docs/optimal-information-architecture-2026-06-24.md:44`, `docs/workspace-pyramid-levels.md:33`, `docs/workspace-pyramid-levels.md:151`, +25
- Ещё источников: 2

### parallel-worktree — Параллельная работа через worktree/merge-gate/commit-lock (9/10)
- Общее утверждение: При конкуренции за hot-файлы агенты уходят в worktree/streams, а общий main остаётся интеграционным слоем.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`, `queues/outbox/2026-06-23-lagrange-nested-system.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:57`, `docs/optimal-information-architecture-2026-06-24.md:65`, `docs/optimal-information-architecture-2026-06-24.md:85`, `docs/top-layer-throughput-methodology.md:48`, `docs/top-layer-throughput-methodology.md:51`, +22
- Ещё источников: 1

### metadata-indexes — Метаданные, front-matter, индексы и карты навигации (9/10)
- Общее утверждение: Каждый важный объект должен иметь ID/статус/слой/связи, а навигация должна генерироваться.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:26`, `docs/optimal-information-architecture-2026-06-24.md:28`, `docs/optimal-information-architecture-2026-06-24.md:41`, `docs/workspace-pyramid-levels.md:139`, `docs/top-layer-throughput-methodology.md:121`, +19
- Ещё источников: 1

### safety-execute-off — Execute OFF, sandbox, human gate (10/10)
- Общее утверждение: Исполнение внешнего кода остаётся закрытым до backend/human/preflight/decision gate.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:40`, `docs/optimal-information-architecture-2026-06-24.md:53`, `docs/optimal-information-architecture-2026-06-24.md:57`, `docs/workspace-pyramid-levels.md:5`, `docs/workspace-pyramid-levels.md:17`, +25
- Ещё источников: 2

### recursive-self-improvement — Система работает над улучшением самой себя (8/10)
- Общее утверждение: Повторяющиеся проблемы должны становиться playbook -> tool -> guard -> assurance.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-throughput-methodology.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`, `docs/agent-capacity-methodology.md`, `docs/agent-onboarding.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:58`, `docs/optimal-information-architecture-2026-06-24.md:69`, `docs/optimal-information-architecture-2026-06-24.md:227`, `docs/workspace-pyramid-levels.md:212`, `docs/top-layer-throughput-methodology.md:47`, +17

## 03. Средний слой: похожие пункты, но требуется нормализация

### universal-core-portals — Универсальное ядро + тематические порталы (5/10)
- Смысл: Доменная специфика должна жить в порталах/плагинах, а не в ядре.
- Почему не верхний слой: тема встречается не во всех вариантах или требует выбора формата/границ.
- Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/workspace-pyramid-levels.md`, `docs/top-layer-command-groups.md`, `docs/orchestration-architecture-2026-06-23.md`, `docs/workflow-conveyor-policy.md`
- Evidence refs: `docs/optimal-information-architecture-2026-06-24.md:15`, `docs/optimal-information-architecture-2026-06-24.md:26`, `docs/optimal-information-architecture-2026-06-24.md:37`, `docs/workspace-pyramid-levels.md:5`, `docs/workspace-pyramid-levels.md:9`, +6

## 04. Нижний слой: одиночные полезные идеи

- **File cards / section cards / semantic elevator** (2/10): Файл должен быть читаем сверху вниз: карточка, краткая карта, детали, evidence, next. Источники: `docs/optimal-information-architecture-2026-06-24.md`, `docs/agent-onboarding.md`

## 05. Разногласия для streams/architecture-core

| ID | Спор | Варианты | Почему важно |
|---|---|---|---|
| DVG-001 | Физически переносить L3 в collab/ или оставить логическим слоем | physical-collab, logical-collab | Физический перенос делает архитектуру чище, но создаёт noisy diff и риск сломанных ссылок. |
| DVG-002 | Отдельная папка indexes/ или расширение существующих generated files | new-indexes-folder, extend-existing-index-json-status-board | Новый слой улучшает понятность, но может дублировать уже работающий index.json/STATUS/board. |
| DVG-003 | File cards обязательны для всех файлов или только для важных L1/L2/policy/manual | all-significant-files, l1-l2-policy-first | Полное покрытие удобно машинам, но может перегрузить мелкие файлы и увеличить ритуал. |
| DVG-004 | Portal-local tools в portals/<name>/tools/ или только общий tools/ | portal-local-tools, shared-tools-only | Локальные tools делают портал похожим на мини-приложение, но усложняют discovery и safety. |
| DVG-005 | GUI/кнопки сейчас или сначала CLI-контракт top.py | gui-now, cli-contract-first | GUI удобен людям, но без стабильного CLI-контракта быстро станет декоративной оболочкой. |
| DVG-006 | Расширять число агентов или сначала усиливать synthesis/drain слой | scale-agents, scale-upper-layer-first | Параллелизм производит больше результатов, но узкое место часто в проверке, синтезе и интеграции. |
| DVG-007 | Runner core считать завершением execute-track или только компонентом blocked umbrella | runner-done, umbrella-blocked-until-human-backend | Код runner существует, но без backend/human/scenario gate execute не должен считаться operationally accepted. |

## 06. Вопросы, найденные в корпусе

### `docs/optimal-information-architecture-2026-06-24.md`
- **Назначение.** Ответить на фундаментальный вопрос: как бы я спроектировал этот проект заново, если цель — удобная совместная работа людей и нескольких AI-агентов над большим информационным полем, кодом, документацией...
- 1. Что это за область?
- 2. На какое ядро она опирается?
- 3. Какие источники разрешены?

### `docs/workspace-pyramid-levels.md`
- 1. Нужно ли физически переносить существующие `tasks/`, `questions/`, `decisions/`, `topics/` внутрь `collab/`, или оставить L3 как логический слой?
- 2. Что считать первым настоящим `core/` export: pipeline, drivers, capabilities или knowledge workflow?
- 3. Первый L2 portal должен быть generic demo, юридический/социальный домен или repo-inventory?
- 4. Должен ли `portals/` хранить data, или только clean configuration и ссылки на data/sandbox?

### `docs/top-layer-command-groups.md`
- Если агент знает тему задачи заранее, стартуйте так: `python tools\top.py agent-start codex --task T-id --context "<тема или вопрос>"`. Это сразу показывает onboarding/status, assurance/advice и поднимает релевантные ...
- | Проверяемость | увидеть, применяются ли инструкции и не устарел ли слой | поднять Q-016 applied/currency/coverage/flow к вершине | `assurance` вызывает `assurance.py` advisory по умолчанию, strict только явно |
- После T-165 верхний слой показывает Q-016 проверяемость одной командой:

### `docs/orchestration-architecture-2026-06-23.md`
- > **Слой над `docs/workflow-conveyor-policy.md` §3-quater** (двусторонний конвейер: широкий producer-фронт + широкий consumer-фронт + тонкий-дешёвый integrator). Бригада — это **именованная единица параллелизма конвей...
- **Бригада = { N producer-агентов + 1 integrator }** — самодостаточный многофазный воркфлоу, обрабатывающий ровно **один вопрос/кластер** конвейера от сырья до готового артефакта:
- ОДИН вопрос/кластер

### `docs/workflow-conveyor-policy.md`
- | Один большой вопрос, равномерно фан-аут-able (аудит N измерений, карта N областей), один синтезатор держит все N | **ОДИН воркфлоу** (политика §1). Дробить на N воркфлоу — лишние издержки формулировки/извлечения без...
- - **Большой вопрос, части НЕ независимы** (их надо сверять друг с другом) → ОДИН воркфлоу с широким фан-аутом и одним примиряющим синтезатором, а не N воркфлоу с ручной сверкой в голове (именно эту нагрузку конвейер и...
- многих открытых вопросах запускают **флот** — по воркфлоу на вопрос (5, 8, больше). Запуск дёшев и
- Классифицировать КАЖДОЕ ребро **до** запуска, не во время. Тест формулировки: *потребляет ли payload запуска Wj (промпт/схема под-агентов) ЗНАЧЕНИЕ, которое производит Wi?*

### `docs/agent-capacity-methodology.md`
- **Бригада-исследователь — идеальная широкая нагрузка.** Бригада = `{N продюсеров + 1 интегратор}` несёт обе дорогие фазы (produce + integrate), и обе «параллелятся свободно» (`orchestration-architecture-2026-06-23.md:...
- **Сбой 3 — частичные волны (спасти хорошие ноги + перезапустить только недостающую).** Малый fan-in выбран именно чтобы смерть узла была дешёвой: «упал один продюсер/дирижёр — перезапускаешь ТОЛЬКО его (а не поддерево...

### `docs/agent-onboarding.md`
- 6. Не уверен — заведи вопрос в `QUESTIONS.md`, не меняй итоговые файлы молча.
- ### Q1. Как несколько агентов работают над ОДНИМ полем, не мешая друг другу?
- ### Q5. Как менять статус без бюрократического ожидания человека?
- это двигает ПРОДУКТ или документирует ПРОЦЕСС?»*

### `queues/outbox/2026-06-23-lagrange-nested-system-continuation.md`
- - Нужно ли Lagrange регистрировать как постоянного агента?
- - Кто является merge-owner для worker worktree?

## 07. Предложения, найденные в корпусе

### `docs/optimal-information-architecture-2026-06-24.md`
- **Статус.** `proposed`: это архитектурный синтез и рабочее предложение, а не принятое решение. По D-017/D-018 спорные места нужно выносить в `streams/<topic>/` и принимать через коллективную перепроверку.
- 1. `D-016`: принято универсальное ядро + тематические порталы. Домен не должен загрязнять код ядра.
- **Операционная стадия:** примерно `580/1000`. Система может работать над самой собой, но пока требует внимательного агента: нужно помнить, когда запускать `generate`, `validate`, `drift_check`, `assurance`, `cohort gu...
- Хорошие советы уже есть, но агент может их не использовать. Это значит, что документация пока часто пассивная. Нужно превращать повторяемые правила в:
- Пример: “не ждать чужой коммит, уходить в worktree” уже описано, но агент всё равно может забыть. Значит правило должно быть не только в `docs/parallel-work-policy.md`, а в `tools/cohort.py guard`, `tools/top.py`, `as...

### `docs/workspace-pyramid-levels.md`
- `core/` — верхний чистый слой. Там должен быть только тот код и документация, которые:
- Но он не должен содержать всю историю обсуждения. Это не архив и не хаотичный inbox. Это текущая чистовая рабочая версия.
- ### Основное правило
- 6. **Лучше для многих агентов.** Разные агенты могут работать на разных уровнях и не мешать друг другу.
- Лучше начать с generic demo portal или уже созданного `data/portals/example`, если он будет принят.

### `docs/top-layer-throughput-methodology.md`
- безопасно внести изменения в канон. Поэтому верхний слой должен быть не большим ручным чатом, а
- реального synthesis. Поэтому `conveyor.py target` должен регулироваться не желанием “запустить больше”, а
- Каждый результат агента должен иметь машинную привязку:
- Если output не указан, верхний слой должен считать результат незавершённым процессом, а не готовым знанием:
- Если два агента пишут на одну тему, это не обязательно дубль. Верхний слой должен различать:

### `docs/top-layer-command-groups.md`
- ## Зачем это нужно
- Верх должен быть простым:
- Моё мнение: это именно та “середина пирамиды”, которую стоит развивать сейчас. Она автоматизирует повторяемые действия агентов и людей, но не вводит тяжёлый router/RAG/execute слой до доказанной необходимости.
- Моё мнение: это правильная форма гарантии для текущей стадии. Не нужно сразу блокировать все действия большим policy-engine. Сначала агент должен явно видеть применимые инструкции и оставлять evidence. Потом часто пов...
- Safety-правило: `--with-streams` не перезаписывает существующий ручной `divergence.md`; если файл уже есть, создаётся `divergence.generated.md` для ручного сравнения.

### `docs/orchestration-architecture-2026-06-23.md`
- 2. **LANDED-QUEUE (буфер между производством и потреблением).** Завершённый воркфлоу роняет `.output`-уведомление и переходит `inflight → landed`; результат садится в очередь `landed` **с машинной output-ref** на dura...
- **`status` — ВЕРДИКТ + exit-код** (`conveyor.py:247-255`, exit `1 = нужно действие`, `0 = healthy` — чтобы следить из hook/CI/wakeup). Ядро — чистая функция `assess(d, now, target, idle_min)` (`conveyor.py:129-167`), ...

### `docs/workflow-conveyor-policy.md`
- - **Большой вопрос, части НЕ независимы** (их надо сверять друг с другом) → ОДИН воркфлоу с широким фан-аутом и одним примиряющим синтезатором, а не N воркфлоу с ручной сверкой в голове (именно эту нагрузку конвейер и...
- - **Пополнять ЗАРАНЕЕ, а не после.** Запускать следующую ноду нужно в момент, когда **начинаешь обрабатывать** завершённую (на её RELEASE/REPLENISH-шаге), а не когда полностью её доделал. Иначе между «доделал» и «запу...
- - **Подтверждение порядка обработки:** завершившийся воркфлоу — **не повод бросать текущую работу** и мгновенно переключаться (это верно, §4 TRIAGE: blocking/топ-value → process, иначе PARK). Но «не переключаться» отн...
- - **Источник будущих заданий должен работать постоянно.** Чтобы было чем пополнять, нужен **стоячий перспективный бэклог** — и его надо генерировать тем же конвейером. Держать **воркфлоу-сканер бэклога** (поверхности:...
- - **`conveyor.py status`** считает in-flight против цели и печатает ВЕРДИКТ + **exit-код** (1 = нужно

### `docs/agent-capacity-methodology.md`
- **4096 items/фан-аут — на порядки выше нужды.** Один `parallel()` мог бы взять до 4096 ног (`:24`, `:34`), но аргумент span-of-control ограничивает реальный fan-in интегратора числом **3** (`docs/nested-orchestration-...
- **1-уровневое вложение — единственный потолок с зубами, но его обходят, а не упираются.** `nested-orchestration-3to1.md:82-86` помечает его КРИТИЧЕСКИМ: `workflow()` внутри ребёнка «бросает исключение», поэтому глубок...
- **Реальный бинд — токены/CPU.** `assess()` (`conveyor.py:130-168`) меряет только in-flight/landed/serial-commit полосу — у него нет понятия контенции, потому что read-only продюсеры её не создают. Поэтому из четырёхчл...
- **Merge гейтится TTL-локом — конкретный механизм сериализации.** Конкурентные merge/commit сериализуются через `tools/commit_lock.py acquire <agent> --ttl <T> --wait <W>` — атомарный O_EXCL с `lease_epoch` TTL и stale...
- - **Правка base/accepted файлов маршрутизируется в котёл, НЕ в соло-build или бригаду.** `workflow-conveyor-policy.md:182` — явное правило: side-branch, который «спорное/меж-агентное (трогает зону Codex, политика/архи...

### `docs/agent-onboarding.md`
- > и **рекомендация-микроскилл** (короткое правило для следующего раза). Многие формализованы в `skills/`.
- нужно от других — D-003). Это даёт асинхронную трассируемость для людей и агентов.

### `queues/outbox/2026-06-23-lagrange-nested-system.md`
- Важно разделить две вещи: repo flow и platform orchestration. Repo flow готовит задачу, claim, worktree, инструкции и gate. Platform orchestrator запускает реальных sub-agent'ов во внешней среде. Репозиторий не должен...
- Сначала Lagrange должен быть зарегистрирован в `AGENTS.md`: ID, роль, разрешённые зоны записи, ограничения. До регистрации его лучше считать внешним sub-agent'ом: читать можно, писать только в явно выделенный outbox/w...
- - Память в файлах требует дисциплины: устаревшие docs надо обновлять или помечать.
- - Внешний orchestrator должен быть явно отделён от repo tools.

### `queues/outbox/2026-06-23-lagrange-nested-system-continuation.md`
- **Chief** держит связь с человеком и каноном репозитория: не делает вид, что утвердил решение, если нужно human approval.
- Правило: worker не переписывает итог, integrator не скрывает разногласия, conductor не принимает governance-решения без человека.
- Markdown-результат должен быть коротким, структурированным и пригодным для synthesis.
- - Нужно ли Lagrange регистрировать как постоянного агента?
- Для shared-tree commit лучше не использовать широкий `git add -A`. Использовать только явные файлы или repo wrapper:

## 08. Что делать дальше

1. Перенести пункты из раздела 02 в clean architecture mainline или portal/core manuals.
2. Пункты из раздела 03 превратить в конкретные tasks: file-card standard, indexes policy, portal v2 contract, top verify bundle.
3. Пункты из раздела 05 держать в `streams/architecture-core/divergence.md` до выбора человеком/котлом.
4. Не помечать этот синтез accepted: он proposed и требует review другими агентами/людьми.

## 09. Counts

- Documents scanned: 10
- Consensus themes: 9
- Near-consensus themes: 1
- Minority useful themes: 1
- Divergences listed: 7
- Question snippets: 26
- Proposal snippets: 43
