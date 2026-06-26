---
id: information-refactoring-cycle-3-2026-06-25
type: topic
status: proposed
owner: codex
related: [T-249, T-248, Q-023]
created: 2026-06-25
---

# Information Refactoring Cycle 3 - action-plan, status-backfill и новые вопросы

## 0. Карточка файла

- Назначение: продолжить обработку накопившихся методологических вопросов через измеримый action-plan.
- Исходный документ: `topics/information-refactoring-question-tree-2026-06-25.md`.
- Новый инструментальный режим: `python tools/top.py question-tree --action-plan`.
- Статус: proposed; это рабочий синтез Codex, не accepted decision.

## 1. Что изменилось технически

Добавлен режим action-plan:

```powershell
python tools\question_tree.py topics\information-refactoring-question-tree-2026-06-25.md --action-plan
python tools\top.py question-tree --action-plan --limit 20
python tools\top.py question-tree --action-plan --json --limit 20
```

Смысл: вопросник теперь не только показывает список вопросов, но и раскладывает их по дорожкам:

1. `requires-decision` -> decision-lane.
2. `open` -> answer-or-question-lane.
3. `unknown` -> status-backfill-lane.
4. `partial` -> implementation-lane.
5. `solved` -> reference-or-archive-lane.

## 2. Что изменилось содержательно

До backfill:

```text
questions: 32
unknown: 9
open: 4
requires-decision: 3
partial: 14
solved: 2
```

После backfill:

```text
questions: 32
unknown: 0
open: 4
requires-decision: 4
partial: 16
solved: 8
```

Главный результат: исчезла машинная неопределённость `unknown`. Это не значит, что все вопросы решены; это значит, что каждый вопрос теперь попал в понятную дорожку обработки.

## 3. Какие старые вопросы получили статус

### 3.1. Удалять ли старую историю?

Ответ: нет. История хранит причины решений, ошибки, варианты и доказательства.

Статус: решено как принцип. Удалять историю нельзя; омоложение делать через статусы, индексы и активную поверхность.

### 3.2. Между чем ищется золотая середина?

Ответ: между верхушкой, где работает человек/агент, и основанием, где лежит ОС, файлы, скрипты, sandbox, логи и внешние материалы.

Статус: решено концептуально; техническое развитие продолжается через `top.py`, инструменты, индексы и sandbox.

### 3.3. Нужно ли сохранять ошибки и старые попытки?

Ответ: да, если они объясняют происхождение решения или дают контрпример.

Статус: частично решено; нужен enforcement через `historical`/`superseded` и верхний слой.

### 3.4. Когда старый документ помогает?

Ответ: когда он добавляет provenance, evidence, variant, error или counterexample.

Статус: решено как критерий triage.

### 3.5. Когда старый документ мешает?

Ответ: когда он выглядит активной рекомендацией, но уже заменён decision/tool/synthesis.

Статус: решено как критерий triage: помечать `historical` или `superseded`.

### 3.6. Когда validator полезен?

Ответ: после повторяемой ошибки, playbook и понятного recipe.

Статус: решено как критерий.

### 3.7. Когда validator вреден?

Ответ: когда он ломает старый корпус без staged adoption и advisory-mode.

Статус: решено как ограничение.

### 3.8. Что должен решать человек?

Ответ: accepted decisions, execute sandbox, массовые изменения истории, политика архивации, commit чужой работы.

Статус: requires decision. Создан Q-023.

### 3.9. Что может делать агент?

Ответ: read-only диагностика, proposed plans, scoped edits, tests, outbox reports, synthesis drafts, top wrappers.

Статус: частично решено; нужна escalation/approval matrix.

## 4. Новые уточняющие вопросы

### 4.1. Governance

1. Какие действия всегда требуют человека?
2. Какие действия может делать главный агент без подтверждения?
3. Какие действия может делать scout-agent?
4. Какие действия может делать observer-agent?
5. Когда observer имеет право рекомендовать consensus?
6. Кто переводит proposed decision в accepted?

### 4.2. Большой объём информации

1. Когда action-plan должен показывать все вопросы, а когда только первые N?
2. Нужно ли считать `open + requires-decision` как главный показатель cognitive debt?
3. Нужно ли делать отдельный `top.py actions`, который объединит tasks/questions/question-tree/friction?
4. Как автоматически находить старые документы, которые мешают активной поверхности?
5. Нужно ли вводить `historical`/`superseded` как обязательные machine statuses?

### 4.3. Большая группа агентов и людей

1. Как распределять агентов по дорожкам action-plan?
2. Может ли один observer обслуживать 3 scout-агентов стабильно?
3. Когда нужен второй observer?
4. Как предотвращать ситуацию, где много агентов создают больше текста, чем верхний слой способен обработать?
5. Какой формат отчёта должен быть обязательным для scout, observer и integrator?

## 5. Инновационная модель: information refinery lanes

Предлагаемая модель обработки большого корпуса:

```text
raw material
  -> status-backfill lane
  -> answer lane
  -> decision lane
  -> implementation lane
  -> reference/archive lane
```

Это похоже на нефтепереработку или medallion architecture, но применено к знаниям:

- raw: текст, мнения, старые отчёты;
- status-backfill: вопрос получил статус;
- answer: вопрос получил объяснение;
- decision: спорный вопрос вынесен в governance;
- implementation: решение стало кодом, tool, skill, validator;
- reference/archive: старый материал не удалён, но не мешает активной поверхности.

## 6. Как использовать это агентам

### Scout-agent

Берёт одну дорожку и пишет короткий отчет:

```text
lane: open
source: question-tree
found: Q2.3.1, Q5.3.1
proposal: answer draft / split / route to decision
risk: ...
```

### Observer-agent

Сравнивает 2-3 scout-отчета:

```text
consensus: ...
divergence: ...
needs evidence: ...
recommended next action: ...
```

### Integrator-agent

Делает маленькую проверяемую правку:

```text
action: create Q/D/task/tool/test
checks: ...
status: proposed/done
```

## 7. Следующий по порядку шаг

Предлагаю следующим циклом сделать один из двух вариантов:

1. `tools/top.py actions` - общий action dashboard из tasks/questions/question-tree/friction.
2. `docs/agent-approval-matrix.md` + proposed decision по Q-023.

Моё мнение: сначала нужен `docs/agent-approval-matrix.md`, потому что масштабирование агентов без матрицы полномочий опасно. После этого `top.py actions` будет знать, какие действия можно делать автоматически, а какие только предлагать.

## Applied instructions

- AGENTS.md: чужая история не удалялась; отчёт вынесен в `queues/outbox/`.
- PROTOCOL.md: работа оформлена через T-249 и pipeline claim.
- `docs/protocol-machine-layer.md`: добавлен проверяемый CLI-режим и раздел Checks.
- cauldron-synthesis: спорные governance-вопросы не утверждены, а вынесены как Q-023/proposed.

## Checks

- OK: `python -m py_compile tools\question_tree.py tools\top.py tools\test_question_tree.py tools\test_top.py`
- OK: `python tools\test_question_tree.py`
- OK: `python tools\test_top.py`
- OK: `python tools\top.py question-tree --action-plan --limit 4`
- OK: `python tools\top.py question-tree --action-plan --json --limit 4`
- OK: `python tools\question_tree.py topics\information-refactoring-question-tree-2026-06-25.md --json` -> `unknown: 0`, `requires-decision: 4`, `open: 4`, `partial: 16`, `solved: 8`
- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> OK=12 WARN=0 ERROR=0
- OK: `python tools\generate.py --check`
