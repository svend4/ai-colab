---
id: agent-approval-matrix
type: doc
title: Матрица полномочий людей, AI-агентов, субагентов и скриптов
status: proposed
owner: codex
created: 2026-06-25
related: [Q-023, D-027, T-250, agent-roles-matrix, workflow-orchestration-policy, workflow-conveyor-policy, agent-launch-workflow, subagent-3to1-sandbox-policy]
---

# Матрица полномочий людей, AI-агентов, субагентов и скриптов

## 0. Карточка файла

- Назначение: ответить на Q-023 и закрепить, кто что может делать в большой группе людей, AI-агентов, субагентов, observer/coordinator ролей и скриптов.
- Статус: proposed. Это рабочая политика для обсуждения; она не переводит решения в `accepted` без человека.
- Практическая цель: увеличить скорость параллельной работы, не превратив репозиторий в конфликтующий поток правок.
- Основные источники: `AGENTS.md`, `PROTOCOL.md`, `docs/agent-launch-workflow.md`, `docs/workflow-orchestration-policy.md`, `docs/workflow-conveyor-policy.md`, `docs/subagent-3to1-sandbox-policy.md`, `docs/top-layer-throughput-methodology.md`, `questions/Q-023.md`.
- Связь с `docs/agent-roles-matrix.md`: старый документ отвечает на вопрос “какие участники и роли существуют”; этот документ отвечает на вопрос “какие действия этим функциональным ролям разрешены”.
- Scout evidence: `queues/outbox/2026-06-25-scout-planck-question-tree.md` и `queues/outbox/2026-06-25-scout-huygens-approval-policy.md`.

## 1. Главный принцип

Большое число агентов ускоряет только сбор и первичную обработку информации. Окончательное ограничение системы находится наверху:

```text
реальная_ширина_флота <= min(
  intake_bandwidth,
  verification_bandwidth,
  synthesis_bandwidth,
  commit_bandwidth,
  decision_bandwidth
)
```

Поэтому полномочия делятся не по “умности” агента, а по риску действия:

- читать можно широко;
- предлагать можно активно;
- писать можно только в scope;
- исполнять внешний/опасный код можно только через sandbox/preflight;
- утверждать governance и accepted decisions может только человек или явно назначенный человеком сборщик.

## 2. Роли

| Роль | Назначение | Типичный доступ | Главный риск |
|---|---|---|---|
| Human / Stefan | владелец решений и направления | accepted governance, approve high-risk | перегруз ручными решениями |
| Lead / main agent | оркестрация, интеграция, scoped edits | proposed policy, code/docs edits, tests | принять спорное как готовое |
| Integrator | проверка и перенос результатов в канон | synthesis, task closure, selective integration | смешать чужую half-done работу |
| Observer / coordinator | собрать 2-3 scout отчета | consensus/divergence report | спрятать расхождения |
| Scout / researcher | read-only разведка | files/docs/search/report | шум без evidence |
| Worker-agent | scoped реализация | конкретные файлы или sandbox/worktree | конфликт write-scope |
| Script/tool | повторяемая проверка/индекс | deterministic read/write generated files | strict-check раньше зрелости |
| External code agent | работа с чужим кодом | sandbox intake only | execute без preflight |

## 3. Матрица действий

| Действие | Scout | Observer | Worker | Integrator | Main agent | Human |
|---|---:|---:|---:|---:|---:|---:|
| Читать docs/code/tasks/questions | yes | yes | yes | yes | yes | yes |
| Писать read-only report в `queues/outbox/` | yes | yes | yes | yes | yes | yes |
| Создать proposed task/question | propose | propose | yes, scoped | yes | yes | yes |
| Создать proposed decision | no | propose | propose | yes | yes | yes |
| Перевести decision в `accepted` | no | no | no | no | no | yes |
| Изменять один scoped doc | no | no | yes, if assigned | yes | yes | yes |
| Изменять код в общем дереве | no | no | only assigned | limited | yes, scoped | yes |
| Изменять код в sandbox/worktree | no | no | yes | yes | yes | yes |
| Массово переносить/архивировать файлы | no | no | no | propose | propose | approve |
| Запускать execute sandbox | no | no | no | propose | propose with preflight | approve |
| Коммитить свои scoped изменения | no | no | maybe via lane | yes | yes | yes |
| Коммитить чужую или смешанную работу | no | no | no | only with explicit scope | only with explicit scope | yes |
| Повышать validator до strict | no | no | no | propose | propose | approve |
| Закрывать спор как consensus | no | propose | no | propose | propose | approve/appointed integrator |

Легенда:

- `yes` = можно делать в своём scope при соблюдении AGENTS/PROTOCOL.
- `propose` = можно предложить, но не утверждать.
- `approve` = решение человека или явно назначенного сборщика.
- `no` = роль не должна делать это действие.

## 4. Risk ladder

### 4.1. Green: можно автоматически или обычным агентом

- Read-only поиск, обзор, классификация.
- Отчёт в `queues/outbox/`.
- Proposed task/question.
- Advisory check.
- Генерация индексов через существующие tools после source changes.
- Маленькая scoped docs-правка в своей задаче.

### 4.2. Yellow: можно main/integrator, но с evidence и checks

- Scoped code edit.
- Новый tool с тестом.
- Правка `tools/top.py`, `tools/question_tree.py`, pipeline-adjacent scripts.
- Обновление generated indexes.
- Закрытие task через pipeline.
- Интеграция subagent report в docs/topics.

### 4.3. Orange: только proposed, нужен review/human или appointed integrator

- Governance policy.
- Proposed decision.
- Смена правил commit/pipeline/sandbox.
- Перевод advisory check ближе к strict.
- Изменение `AGENTS.md`, `PROTOCOL.md`, accepted docs.
- Коммит чужой half-done работы.

### 4.4. Red: без explicit approval нельзя

- Accepted decision.
- Execute sandbox для внешнего кода.
- Массовая физическая миграция файлов.
- Удаление истории, outbox, чужих сообщений.
- `git reset --hard`, destructive cleanup, force rewrite.
- Hidden fan-out, который пишет в общий tree без lane/worktree.

## 5. Workflow 3:1 для субагентов

Базовая ячейка:

```text
3 scouts -> 1 observer -> 1 integrator -> main/human
```

### 5.1. Scout contract

Scout получает одну lane или один вопрос:

```text
role: scout
mode: read-only
scope: Q-023 / question-tree lane / docs subset
output: queues/outbox/<date>-scout-<name>-<topic>.md
fields: scope, findings, evidence, proposal, risks, next
```

Scout не меняет файлы проекта, кроме отчёта, если ему явно не выдан write-scope.

### 5.2. Observer contract

Observer получает 2-3 scout отчёта:

```text
role: observer
mode: synthesis
input: scout reports
output: consensus/divergence report
fields: consensus, divergence, evidence gaps, recommended next action
```

Observer не утверждает `accepted`. Его задача — уменьшить шум перед integrator.

### 5.3. Integrator contract

Integrator получает observer report или один достаточно качественный scout report:

```text
role: integrator
mode: scoped-write
output: Q/D/task/doc/tool/test
checks: generate, validate, targeted tests
status: proposed unless already safe task done
```

Integrator делает маленькое проверяемое действие, а не “переписывает всё”.

## 6. Conveyor discipline

На каждом пробуждении:

```powershell
python tools\conveyor.py tick
python tools\conveyor.py status --json
```

Если `REFILL`: запускать только столько новых read-only scout workflow, сколько верхний слой успеет обработать.

Если `PROCESS`: сначала обработать landed outputs, а не запускать ещё.

Если `IDLE`: обновить heartbeat, проверить зависшие workflow, land/dismiss/ship.

Практическое правило для текущей стадии проекта:

```text
target 2-4 read-only workflow
max 1 shared-tree build workflow
build parallelism only through worktree/sandbox
```

## 7. Sandbox и worktree

| Ситуация | Куда писать |
|---|---|
| Внешний код / svend4 / неизвестный источник | `sandbox/intake` или `sandbox/external` read-only |
| Экспериментальный код агентов | `sandbox/ideas` или task-specific sandbox |
| Параллельный build с возможным конфликтом | Level 1 worktree |
| Docs/report/synthesis без риска | shared tree, scoped files |
| Accepted core artifact | только после review/checks/approval |

Execute external code запрещён без отдельного preflight и решения.

## 8. Advisory -> strict ladder

Новая проверка проходит стадии:

```text
idea -> playbook -> tool advisory -> repeated green runs -> proposed strict -> accepted strict
```

Переход к strict допустим только если:

1. проблема повторялась;
2. есть понятный recipe;
3. tool имеет тест;
4. false positives низкие;
5. старый корпус не ломается без staged adoption;
6. человек или appointed integrator принимает strict-mode.

## 9. Ответы на старые вопросы

### 9.1. Q4.3.1 - Что требует отдельного решения?

Отдельного решения требуют: accepted governance, execute sandbox, массовая миграция файлов, strict validators, коммит чужой half-done работы, изменение AGENTS/PROTOCOL, скрытый write fan-out.

### 9.2. Q7.2.1 - Какие изменения повышают зрелость?

Зрелость повышают изменения, которые уменьшают ручную память верхнего слоя: action-plan, approval matrix, landing rule, report schema, tests, generate/validate, clear human gate.

### 9.3. Q9.1.1 - Что делать первым?

Первым делать матрицу полномочий, потому что без неё нельзя безопасно масштабировать агентов, observer-группы, strict checks и sandbox promotion.

### 9.4. Q11.3.1 - Что должен решать человек?

Человек или явно назначенный человеком сборщик решает accepted governance, execute sandbox, массовые изменения истории, commit чужой/смешанной работы, strict enforcement и спорный consensus.

## 10. Новые вопросы

1. Кто может быть appointed integrator и как это фиксируется?
2. Нужно ли отдельное поле `approval_required: true/false` во front matter задач/решений?
3. Должен ли `tools/top.py actions` показывать action lane вместе с permission lane?
4. Когда scout report считается достаточно доказательным для observer?
5. Сколько landed reports можно держать до запрета нового REFILL?
6. Нужно ли автоматическое предупреждение, если `conveyor.py status` healthy=false больше N минут?
7. Как хранить human approval: в decision, task report, outbox или отдельном approval log?

## 11. Минимальный формат отчёта ролей

### Scout report

```md
## Scope
## Findings
## Evidence
## Proposal
## Risks
## Next
## 14. Checks
```

### Observer report

```md
## Inputs
## Consensus
## Divergence
## Evidence gaps
## Recommended next action
## 14. Checks
```

### Integrator report

```md
## Inputs
## Integrated changes
## Deferred disagreements
## Files changed
## 14. Checks
## Applied instructions
```

## 12. Scout synthesis

### 12.1. Consensus

Оба scout-отчёта сходятся в главном:

- Q-023 является ближайшим governance-долгом.
- Матрица полномочий должна быть proposed, а не accepted.
- Read-only fan-out можно масштабировать шире, чем build/write.
- Observer/coordinator нужен до расширения количества scouts.
- Accepted decisions, execute sandbox, strict enforcement и массовые изменения требуют человека или явно назначенного сборщика.
- Следующий dashboard `top.py actions` должен учитывать не только action lane, но и permission lane.

### 12.2. Divergence / дополнения

- Planck сильнее выделил старые вопросы question-tree и порядок следующих задач.
- Huygens сильнее выделил уже существующие policies и необходимость не дублировать `docs/agent-roles-matrix.md`.
- Эти позиции совместимы: `agent-roles-matrix` остаётся картой участников/ролей, а `agent-approval-matrix` становится permission-layer.

### 12.3. Result

На основе scout evidence этот документ фиксирует предложенную матрицу как рабочий proposed contract и отправляет формальное решение в D-027.
## 13. Applied instructions

- AGENTS.md: решения не переводятся в accepted без человека; чужая история не удаляется.
- PROTOCOL.md: работа идёт через T-250, Q-023 и D-027.
- docs/agent-launch-workflow.md: platform launcher отделён от repo-flow; worker получает scope.
- docs/workflow-conveyor-policy.md: conveyor используется как внешний журнал in-flight/landed/ship.
- docs/subagent-3to1-sandbox-policy.md: 3:1 scout/observer/main topology сохранена.
- cauldron-synthesis: разногласия не стираются, governance остаётся proposed.

## Checks

- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> OK=12 WARN=0 ERROR=0
- OK: `python tools\generate.py --check`
- OK: `python tools\conveyor.py land t250-planck --output queues\outbox\2026-06-25-scout-planck-question-tree.md`
- OK: `python tools\conveyor.py land t250-huygens --output queues\outbox\2026-06-25-scout-huygens-approval-policy.md`
- OK: `python tools\conveyor.py ship t250-planck`
- OK: `python tools\conveyor.py ship t250-huygens`
- NOTE: final `python tools\conveyor.py status --json` shows landed=0, shipped=52, deficit=2/REFILL for the next workflow wave.
