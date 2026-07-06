---
id: orchestrator-cycle-proposal-review-codex-2026-07-06
type: report
title: "Рецензия Codex на orchestrator-cycle-proposal-2026-07-06"
status: proposed
date: 2026-07-06
author: codex
related:
  - orchestrator-cycle-proposal-2026-07-06
  - closed-loop-agent-cauldron-conveyor
  - T-273
  - T-274
  - T-275
  - T-276
  - D-011
  - D-017
  - D-018
  - D-027
  - D-031
  - D-035
---

# Рецензия Codex на orchestrator-cycle-proposal-2026-07-06

## 1. Общий вердикт

Предложение Claude технически сильное и в целом принимается как операционный слой поверх уже существующей closed-loop модели.

Мой вывод: документ не дублирует `docs/closed-loop-agent-cauldron-conveyor.md`, а добавляет недостающую организационную оболочку:

1. пакет-задание `PKG-*`;
2. общую повестку `kotel/agenda.md`;
3. статусы цикла для стратегических агентов;
4. риск-правила согласования;
5. вопрос к котлу по D-035.

Это полезно, потому что closed-loop runbook описывает поток состояний и техническую механику, а proposal Claude отвечает на вопрос: как нескольким главным агентам не мешать друг другу и как человеку видеть только компактную повестку.

Рекомендация: принять вариант (c) из §9 proposal — пилот на T-273, затем решение о полном принятии.

## 2. Что проверено фактически

### 2.1. Файл существует

Проверен файл:

```text
docs/orchestrator-cycle-proposal-2026-07-06.md
```

Документ имеет front matter, status `proposed`, author `claude`, links на D-035, D-011, D-027, D-031, D-018 и next-stage plan.

### 2.2. `kotel/` существует, но не как agenda/module

Проверено: каталог `kotel/` уже есть, но сейчас в нём найден один файл:

```text
kotel/independent-first-reconcile-consensus-2026-06-25.md
```

Значит предложение `kotel/agenda.md` и `kotel/packages/` не конфликтует с существующим каталогом, но это ещё не реализовано.

### 2.3. `risk_gate.py` существует

Проверено:

```powershell
python tools\risk_gate.py --help
```

Фактическая семантика совпадает с proposal:

```text
low    -> AUTO
medium -> REVIEW
high   -> HUMAN
```

Ограничение: текущий `risk_gate.py` работает по `T-*` или `D-*`, а не по `PKG-*`. Поэтому риск-правила пакетов пока методологические. Для полного внедрения нужен parser/check для package front matter или расширение risk gate.

### 2.4. Команды верхнего слоя есть

Проверенные ранее и подтверждённые инструменты поддерживают цикл:

```powershell
python tools\top.py subagent-handoff <agent> <task> [context...] [--worktree] [--json]
python tools\top.py conveyor [--target N] [--json]
python tools\top.py process-landed [--json] [--all] [--topic TOPIC]
python tools\top.py synthesize-docs [topic] [--json]
python tools\top.py cauldron-lanes [topic] [--json]
python tools\top.py work-mode <agent> <task> [--parallel] [--hot-files]
```

Пример для T-273:

```powershell
python tools\top.py work-mode codex T-273 --parallel --hot-files
```

Результат рекомендует Level 1 worktree, что хорошо согласуется с proposal: реальный parallel/build должен идти через изоляцию.

## 3. Сильные стороны proposal

### 3.1. Два слоя сформулированы правильно

Разделение на стратегический слой и исполнительный слой снимает главный конфликт многоагентной работы:

- главные агенты держат стратегию, согласование и интеграцию;
- субагенты делают массовую работу;
- человек принимает спорные/high-risk решения;
- отчёты возвращаются в общий котёл, а не остаются в частных чатах.

Это совпадает с практическим выводом последних работ: лимит системы не в числе агентов, а в synthesis/review/commit capacity верхнего слоя.

### 3.2. 8 тактов удобны для человека

Цикл:

```text
формулировка -> согласование -> исполнение -> перепроверка -> интеграция -> демонстрация -> сбор заданий -> ратификация
```

хорошо переводит сложную механику workflow/conveyor в понятный человеческий процесс.

### 3.3. Risk-based согласование снижает бутылочное горлышко

Идея не тащить все low-risk действия к человеку правильная. D-035 уже решает пакетную ратификацию, а risk gate позволяет не блокировать мелкие вспомогательные отчёты и proposed-документы.

### 3.4. `kotel/agenda.md` как единая поверхность полезна

Если сделать её генерируемой поверхностью, человек будет читать не весь репозиторий, а компактную доску:

1. какие пакеты в работе;
2. какие зоны пересекаются;
3. какие вопросы ждут котёл-дня;
4. какие демонстрации готовы;
5. какие решения требуют реакции.

Это ровно то, чего не хватает верхнему слою как продукту.

### 3.5. Proposal корректно не внедряет сам себя

Важно: Claude не пишет `accepted`, а выносит вопрос в котёл. Это соответствует D-018 и D-035.

## 4. Основные замечания

### 4.1. `PKG-*` не должен стать вторым источником истины

Пакет-задание полезен как операционная оболочка, но source of truth должны оставаться:

- `tasks/T-*.md`;
- `questions/Q-*.md`;
- `decisions/D-*.md`;
- accepted docs;
- pipeline/conveyor state.

Правило: каждый medium/high package обязан ссылаться на `T-*`, `Q-*` или `D-*`. Пакет без канонической связи допустим только для short-lived low-risk работы.

### 4.2. `risk_gate.py` пока не проверяет пакеты

Proposal пишет, что risk берётся по семантике `risk_gate.py`, но текущий инструмент не читает `kotel/packages/PKG-*.md`.

Нужен один из вариантов:

1. расширить `risk_gate.py`, чтобы он умел `PKG-*`;
2. сделать отдельный `package_gate.py`;
3. сделать agenda generator, который читает risk из package front matter и вызывает risk policy локально.

До этого нельзя считать package risk автоматическим gate.

### 4.3. `agreed_by` и окно молчания требуют механики времени

Раздел §4 предлагает 12 часов silence window для medium. Это разумно, но без инструмента оно будет ручным соглашением.

Для реализации нужны поля:

```yaml
posted_at: 2026-07-06T10:00:00+02:00
review_deadline: 2026-07-06T22:00:00+02:00
veto_by: []
review_state: open|ok|vetoed|expired
```

И нужна проверка: expired medium package без veto может переходить в agreed.

### 4.4. Zone-overlap advisory пока не реализован

Proposal предлагает декларативный lock по zones. Идея правильная, но нужен checker:

- два `in-swarm` пакета с пересекающимися `zones` -> WARN;
- package zone пересекается с dirty mainline -> WARN;
- package zone затрагивает generated indexes -> worktree advice;
- package zone затрагивает deny-paths -> FAIL/HUMAN.

Это можно связать с `ownership.py`, `cohort.py`, `permissions.py`, `top.py work-mode`.

### 4.5. `kotel/agenda.md` должен быть generated, не ручной

Proposal это говорит, и я поддерживаю. Важно зафиксировать жёстко: руками правятся `PKG-*` и source questions, а agenda собирается генератором. Иначе появится ещё один stale-файл.

### 4.6. Формулировка про потолок Claude workflow environment-specific

Фраза про "~5 агентов на воркфлоу из-за потолка ядер" может быть верной для конкретной среды, но её нельзя делать общим правилом репозитория. Лучше записать как observed example, а не invariant.

### 4.7. Нужно связать proposal с T-276

T-276 сейчас про cauldron task materializer. Proposal добавляет слой `PKG-*` и agenda. Эти вещи должны быть связаны:

- materializer читает synthesis/cauldron;
- package/agenda показывает lifecycle;
- future package tool может создавать packages из task candidates или связывать package с T-id.

## 5. Как совместить с closed-loop runbook

Моя предлагаемая композиция:

### 5.1. `docs/closed-loop-agent-cauldron-conveyor.md`

Это базовый технический runbook:

```text
brief -> DAG -> subagents -> landed -> verify -> synthesize -> cauldron -> tasks -> refill
```

### 5.2. `docs/orchestrator-cycle-proposal-2026-07-06.md`

Это организационный пакетный слой:

```text
PKG-* -> agenda -> agreement -> swarm -> demonstration -> kotel-day
```

### 5.3. `T-276`

Это технический мост:

```text
synthesis/cauldron output -> dry-run task candidates -> explicit apply -> tasks/T-*.md
```

### 5.4. Следующая недостающая задача после T-276

После T-276 логично добавить отдельную задачу на package/agenda pilot:

```text
Orchestrator package/agenda pilot — PKG template + generated kotel/agenda.md + zone-overlap advisory
```

Я не создаю её автоматически в этой рецензии, потому proposal сам просит котёл-решение. Но если Stefan скажет "да, пилот", это должен быть следующий T-id.

## 6. Рекомендация по решению

Я рекомендую вариант (c) из proposal:

1. провести пилот на T-273;
2. не создавать сразу полный bureaucracy layer;
3. для пилота создать один `PKG-*`;
4. вручную или полуавтоматически собрать agenda;
5. проверить, помогает ли это человеку видеть работу;
6. после пилота принять вариант (a) или упростить до (b).

## 7. Минимальный пилот без лишнего риска

### 7.1. Выбрать T-273

T-273 подходит, потому что это первый живой L2 payload и он требует координации, но может быть read-only.

### 7.2. Создать один package

```text
kotel/packages/PKG-20260706-pilot-t273.md
```

### 7.3. Package должен ссылаться на T-273

Поля:

```yaml
id: PKG-20260706-pilot-t273
type: package
status: draft
orchestrator: codex|claude
risk: medium
tasks: [T-273]
zones:
  - reports/
  - tmp-work/
  - docs/
```

### 7.4. Agenda пока можно сделать вручную как proposed

```text
kotel/agenda.md
```

Но в тексте agenda нужно явно написать: "manual pilot, future generated".

### 7.5. После пилота сделать решение

На котёл-дне выбрать:

- принять package/agenda слой;
- оставить только runbook без packages;
- перенести package-идею в T-276/T-277.

## 8. Итог

Документ Claude стоит сохранить как proposed и вынести в котёл. Я не вижу причин отклонять его. Основная поправка: package/agenda — это не замена pipeline, а временная операционная оболочка над T/Q/D и conveyor.

Моя позиция:

```text
Принять для пилота: да.
Сразу принимать как обязательный стандарт: рано.
Нужно реализовать без auto-accepted decisions: обязательно.
Нужно связать с T-276 и future agenda generator: да.
```
