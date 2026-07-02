---
id: alpha2-to-alpha3-roadmap-2026-06-24
type: topic
title: Alpha-2 -> Alpha-3 roadmap: план развития проекта
status: proposed
owner: codex
date: 2026-06-24
related: [T-243, T-244, protocol-machine-layer-2026-06-24]
---

# Alpha-2 -> Alpha-3 roadmap: план развития проекта

## 0. Назначение документа

Этот документ выводит на коллективное согласование следующий этап развития проекта. Он основан на текущей оценке:

```text
Стадия: Alpha-2
Тип: self-hosted collaboration engine / информационный движок для людей и AI-агентов
Готовность концепции: 65-70%
Готовность реализации: 45-55%
Готовность как удобного продукта: 25-35%
```

Цель следующего этапа: перевести проект из "структурируемой инфраструктурной альфы" в более управляемую Alpha-3, где верхний слой не только описан, но реально помогает людям и агентам выбирать работу, проверять риски, синтезировать документы и доводить изменения до приёмки.

## 1. Главный принцип Alpha-3

Alpha-3 не должна быть просто добавлением новых документов. Главный принцип:

```text
ценная рекомендация -> машинная проверка -> верхняя команда -> тест -> отчёт -> повторяемый workflow
```

Если совет существует только в тексте, он легко забывается. Если совет превращён в команду, индекс, тест или skill, верхний слой начинает реально использовать основание пирамиды.

## 2. Что уже работает

- [x] Есть структура задач: `tasks/`.
- [x] Есть вопросы и решения: `questions/`, `decisions/`.
- [x] Есть очередь и полилог: `queues/inbox`, `queues/outbox`, `queues/claimed`, `queues/done`.
- [x] Есть темы и варианты обсуждений: `topics/`, `streams/`.
- [x] Есть песочница для внешнего и чернового материала: `sandbox/`.
- [x] Есть верхняя панель `tools/top.py`.
- [x] Есть конвейер `tools/pipeline.py`.
- [x] Есть диагностика повторяющихся проблем и assurance-слои.
- [x] Есть `tools/cli_inventory.py`, который переводит проблему CLI-help из мнения в измеримый показатель.
- [x] Есть первый batch исправления CLI-help: risky CLI снижены с 45 до 39.

## 3. Что ещё не хватает

### 3.1. Верхний слой управления ещё неполный

Проблема: человек или агент всё ещё должен помнить много команд.

Нужно:

- [ ] Сделать в `tools/top.py` команды верхнего уровня для самых частых сценариев.
- [ ] Добавить `top.py cli-risk` или `top.py fix-cli-help-plan`, чтобы видеть CLI-риски и следующий батч.
- [x] Добавить `top.py actions` для `tools/action_tracker.py`, чтобы видеть отчёты с невыполненными чекбоксами. Выполнено: `8d95fb9`.
- [ ] Добавить `top.py next-work` как read-only рекомендацию следующего безопасного шага.
- [ ] Добавить `top.py alpha-status`, который показывает текущую стадию по шкале Alpha-2/Alpha-3.

### 3.2. Правила есть, но не все машинно проверяются

Проблема: `docs/protocol-machine-layer.md` задаёт правильные машинные правила, но пока не всё валидируется.

Нужно:

- [x] Проверять, что outbox-отчёты имеют `## Applied instructions`. Выполнено advisory-командой `python tools\instructions.py check-report <path>`.
- [x] Проверять, что outbox-отчёты имеют `Checks:`. Выполнено advisory-командой `python tools\instructions.py check-report <path>`.
- [ ] Проверять, что action items оформлены как Markdown-чекбоксы.
- [ ] Проверять, что tools с побочными эффектами имеют явный `--apply` или документированное исключение.
- [ ] Проверять, что JSON-команды не загрязняют stdout человекочитаемым шумом.

### 3.3. Навигация для человека ещё тяжёлая

Проблема: структура уже богата, но человеку трудно быстро понять, куда смотреть.

Нужно:

- [ ] Создать или обновить главный обзор `START_HERE.md` или аналогичный портал.
- [ ] Добавить страницу `docs/alpha-status.md` с текущей стадией, счётом и следующими командами.
- [ ] Сделать короткий human dashboard: что делать человеку, что делать агенту, где посмотреть статус.
- [ ] Разделить "история" и "текущее состояние": не все outbox-отчёты должны быть первичной навигацией.

### 3.4. Консенсус и разногласия ещё не полностью автоматизированы

Проблема: есть котёл, но не всегда ясно, что уже почти консенсус, а что требует детализации.

Нужно:

- [ ] Усилить `cauldron-lanes`: две полосы `ratify-build` и `divergence-detail`.
- [ ] Делать отчёты синтеза с обязательными секциями: общие пункты, расхождения, доказательства, следующий action.
- [ ] Указывать источники документов и строк, где встречается совпадающая рекомендация.
- [ ] Добавить верхнюю команду `top.py synthesize` как простой alias к текущему синтезу документов.

### 3.5. Агентный конвейер ещё требует ручной оркестрации

Проблема: несколько агентов могут работать, но верхний слой пока не всегда помогает выбирать пропорции и группы.

Нужно:

- [ ] Ввести режимы работы: `solo`, `small-cell`, `observer-cell`, `read-only-wave`.
- [ ] Сделать read-only планировщик: сколько задач можно параллелить, какие нельзя.
- [ ] Добавить `top.py agent-cell-plan`, который печатает 3+1 схему: 3 исполнителя и 1 наблюдатель.
- [ ] Сделать правило: build-задачи в shared tree выполняются узко, read-only задачи можно распараллеливать шире.

### 3.6. Песочница ещё должна стать рабочим процессом, а не только папкой

Проблема: внешние репозитории и черновой код должны попадать в проект безопасно и проверяемо.

Нужно:

- [ ] Описать и закрепить lanes: external-source, agent-draft, promotion-candidate.
- [ ] Добавить top-команду для read-only intake sandbox.
- [ ] Сделать отчёты по sandbox intake стандартными: manifest, inventory, risk, recommendation.
- [ ] Не включать execute-песочницу без отдельного accepted decision и preflight.

## 4. Предлагаемые стадии реализации

### Stage A. Согласование roadmap

Цель: не начинать большие кодовые изменения без коллективной рамки.

Действия:

- [ ] Codex публикует этот документ в `topics/`.
- [ ] Другие агенты добавляют комментарии или варианты в `topics/` или `queues/outbox/`.
- [ ] Человек или интегратор выбирает: принять полностью, принять частично, отправить на детализацию.

Критерий готовности:

```text
roadmap status: proposed -> accepted/partially-accepted
```

### Stage B. Top-layer wrappers

Цель: сделать верхний слой более удобным.

Действия:

- [ ] `top.py cli-risk`: обёртка над `cli_inventory.py`.
- [x] `top.py actions`: обёртка над `action_tracker.py status`. Выполнено: `8d95fb9`.
- [ ] `top.py alpha-status`: короткий отчёт по стадии проекта.
- [ ] `top.py next-work`: read-only рекомендация следующей задачи.
- [ ] Обновить `tools/test_top.py`.

Критерии:

```text
python tools/top.py buttons содержит новые команды
python tools/top.py cli-risk --json возвращает JSON
python tools/test_top.py -> OK
```

### Stage C. Machine protocol validators

Цель: превратить `docs/protocol-machine-layer.md` в проверки.

Действия:

- [x] Создать или расширить проверку outbox footer. Сейчас: `tools/instructions.py check-report`.
- [x] Проверять `Applied instructions` и `Checks:`. Сейчас: advisory check-report, не hard gate.
- [x] Интегрировать `action_tracker.py` в top и validate/advisory слой. Сейчас: `python tools\top.py actions`; validate strict-gate ещё не включён.
- [ ] Сделать dry-run/apply audit для tools с побочными эффектами.

Критерии:

```text
new validator finds missing report footers as WARN first, not hard FAIL
validate remains OK for canonical required checks
strict mode can fail when policy is ready
```

### Stage D. CLI-risk reduction batches

Цель: сделать инструменты дружелюбными для людей и агентов.

Текущий счёт:

```text
risky: 39
ok-help-guard: 20
ok-argparse: 12
manual-help: 0
```

Действия:

- [ ] Batch 2: маленькие read-only/report tools.
- [ ] Batch 3: sandbox/intake/reporting tools.
- [ ] Batch 4: hot tools только отдельно: `pipeline.py`, `generate.py`, `validate.py`, `next_id.py`.

Критерии:

```text
risky <= 25 после двух батчей
risky <= 10 после hot-tool этапа
all --help probes have exit 0 and no side effects
```

### Stage E. Human navigation and product surface

Цель: человеку легче пользоваться системой.

Действия:

- [ ] Создать `START_HERE.md` или обновить существующий главный портал.
- [ ] Добавить `docs/alpha-status.md`.
- [ ] Добавить таблицу "если хочешь X, запускай Y".
- [ ] Добавить short path для людей: статус, задачи, отчёты, решения, sandbox.

Критерии:

```text
new human can open one file and find status + next commands in 2 minutes
agent can run one top command and get work context
```

### Stage F. Consensus engine hardening

Цель: отделить почти готовый консенсус от спорных тем.

Действия:

- [ ] Улучшить output `cauldron-lanes`.
- [ ] Добавить score для consensus confidence.
- [ ] Добавить список источников для каждого общего пункта.
- [ ] Разногласия отправлять в отдельные detail-темы.

Критерии:

```text
common points, divergences and next actions are machine-readable
ratify-build items can become implementation tasks
```

### Stage G. Agent orchestration

Цель: управлять группами агентов, а не просто запускать их вручную.

Действия:

- [ ] Описать и реализовать read-only `agent-cell-plan`.
- [ ] Поддержать 3+1 схему: worker, worker, worker, observer.
- [ ] Добавить критерии, когда можно расширять parallelism.
- [ ] Добавить рекомендации target по типам задач.

Критерии:

```text
shared-tree build target stays narrow
read-only/report/search can fan out wider
observer produces synthesis, not raw duplication
```

## 5. Предлагаемая очередь ближайших задач

### T-next-1. Top CLI-risk wrapper

- [ ] Добавить `top.py cli-risk`.
- [ ] Добавить кнопку в `top.py buttons`.
- [ ] Добавить тест parser/button/json.
- [ ] Не исправлять новые CLI в этой задаче.

### T-next-2. Top action tracker wrapper

- [x] Добавить `top.py actions`.
- [x] Подключить `tools/action_tracker.py status`.
- [ ] Сначала read-only.
- [ ] `archive-old --apply` не вызывать из top по умолчанию.

### T-next-3. Alpha status doc and command

- [ ] Создать `docs/alpha-status.md`.
- [ ] Создать `top.py alpha-status`.
- [ ] Хранить показатели в одном месте.
- [ ] Обновлять score после крупных этапов.

### T-next-4. Machine report footer validator

- [x] Проверять `Applied instructions` через `tools/instructions.py check-report`.
- [x] Проверять `Checks:` через `tools/instructions.py check-report`.
- [x] Сначала advisory/WARN.
- [ ] После чистки можно перевести в strict gate.

### T-next-5. CLI-risk batch 2

- [ ] Взять 5-8 маленьких read-only tools из `unsafe-sysargv`.
- [ ] Добавить `HELP` и `help_guard`.
- [ ] Расширить `test_cli.py`.
- [ ] Снизить `risky` ещё на 5-8.

## 6. Что нельзя делать без отдельного согласования

- [ ] Не делать массовую правку всех 39 CLI-risk файлов одним заходом.
- [ ] Не переводить report footer validator сразу в hard FAIL.
- [ ] Не включать execute sandbox без отдельного accepted decision.
- [ ] Не запускать широкую группу агентов для build-задач в одном shared tree.
- [ ] Не архивировать старые outbox-файлы через `--apply` без отдельного решения.
- [ ] Не коммитить чужие half-done изменения без selective-add и явного scope.

## 7. Метрики Alpha-3

Предлагаемые целевые показатели:

```text
Идея проекта:              80/100 -> 85/100
Архитектурная концепция:   70/100 -> 78/100
Методология полилога:      65/100 -> 75/100
Конвейер задач:            65/100 -> 75/100
Автоматизация проверок:    55/100 -> 70/100
Удобство для агентов:      50/100 -> 68/100
Удобство для человека:     35/100 -> 55/100
Готовность как продукт:    30/100 -> 45/100
```

В промилле для более тонкого контроля:

```text
Alpha-2 current: 520/1000 интегральной готовности
Alpha-3 target: 680/1000 интегральной готовности
```

## 8. Предлагаемое решение для согласования

Предлагаю принять этот roadmap как `proposed` и начать с Stage B, потому что он даёт самый быстрый эффект:

```text
top.py cli-risk
 топовый доступ к cli_inventory
 снижение ручной памяти агента
 база для следующих CLI-help батчей
```

После Stage B можно параллельно открыть Stage C и Stage E: машинный протокол и человеческая навигация.

## 8.1. Progress note 2026-06-26

Выполнено после первоначального roadmap:

- `tools/action_tracker.py` добавлен и подключён к `tools/conveyor.py recover`.
- `python tools\top.py actions` добавлен в верхнюю панель и `top.py buttons`.
- `tools/instructions.py check-report` использован для нормализации outbox evidence reports.
- Strict-gate для всех старых отчётов пока не включён: это должно оставаться отдельным решением, чтобы не сломать historical corpus.
## 9. Applied instructions

- AGENTS.md: не переписывать чужие сообщения, outbox для результатов, proposed вместо accepted.
- PROTOCOL.md / docs/protocol-machine-layer.md: план через чекбоксы, отчёт с Applied instructions и Checks.
- Пользовательское указание: сначала план, затем реализация только после согласования/продолжения.

Checks:
- python tools/generate.py -> OK
- python tools/validate.py -> OK
- python tools/generate.py --check -> OK