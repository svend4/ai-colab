---
id: 20260625-1818-codex
topic: code-variant-sandbox
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
task: T-257
phase: independent-before-comparison
---

# Stream: code-variant-sandbox / Codex independent variant

## 00. Причина независимого варианта

Этот stream создан как исправление методологического сбоя. По новой политике содержательный вопрос нельзя начинать с “есть ли уже готовый механизм, чтобы не дублировать”. Сначала агент должен раскрыть свой вариант полностью, потому только после этого можно понять, что является настоящим дублем, что является независимым подтверждением, а что является новым вариантом.

Тема: как работать с предварительным кодом, псевдокодом и черновыми изменениями так, чтобы несколько агентов могли предлагать варианты, но mainline-код не превращался в конфликтный хаос.

## 01. Условия применимости

Мой вариант применяется, когда:

1. Агент или человек хочет предложить изменение программного кода, но ещё не ясно, стоит ли менять `tools/`, `drivers/`, `core/`, `portals/` или другой mainline-каталог.
2. Есть несколько возможных решений одной code-задачи.
3. Код может быть опасным, непроверенным, неполным, зависимым от внешних библиотек или просто спорным.
4. Нужна зона, где можно писать псевдокод, прототип, тестовую реализацию, заметки и diff-план без немедленного выполнения и без загрязнения основного дерева.
5. Требуется сравнить варианты разных агентов не по названию задачи, а по условиям, tradeoffs, tests, risks, promotion cost и maintainability.

## 02. Независимый ответ агента

Я предлагаю пятиступенчатую модель предварительной работы с кодом:

```text
idea card -> pseudocode variant -> draft code packet -> static review -> promotion task
```

### 02.1. Idea card

Самый ранний уровень. Агент пишет не код, а намерение:

- какую проблему решает;
- какие файлы предположительно затронет;
- какие входы/выходы будут у функции или команды;
- какие риски видит;
- почему mainline менять рано.

Формат:

```text
streams/<topic>/<stream-id>/STREAM.md
```

### 02.2. Pseudocode variant

Здесь агент раскрывает алгоритм без привязки к финальному API:

```text
streams/<topic>/<stream-id>/pseudocode.md
```

Псевдокод должен быть достаточно точным, чтобы другой агент мог реализовать альтернативу, но не должен считаться исполняемым кодом.

Минимальный состав:

1. Data model.
2. Control flow.
3. Error cases.
4. Test scenarios.
5. Integration points.
6. Reasons not to implement directly yet.

### 02.3. Draft code packet

Если псевдокода недостаточно, агент может написать реальный черновой код, но не в mainline. Черновой код живёт в отдельном пакете:

```text
sandbox/drafts/<draft-id>/
  manifest.json
  README.md
  pseudocode.md
  src/
  tests/
  notes.md
```

Главное правило:

```text
draft code is evidence, not implementation
```

Файл в draft-зоне не является разрешением на запуск, импорт, установку зависимостей или promotion.

### 02.4. Static review

До любого выполнения черновик проходит только read-only/static проверки:

- manifest validity;
- path safety;
- secret scan / no credentials;
- dependency risk;
- AST/static inspection для Python;
- link/path checks;
- review of test intent, not execution.

Результат review — не merge, а один из статусов:

| Статус | Значение |
|---|---|
| `reject` | идея слабая/опасная/дублирует без пользы |
| `needs-more-variant` | нужен второй независимый вариант |
| `needs-human-question` | есть governance/safety вопрос |
| `ready-for-promotion-task` | можно заводить отдельную задачу на реализацию |
| `keep-as-reference` | полезно как пример, но не строить сейчас |

### 02.5. Promotion task

Только после review создаётся обычная задача на mainline-реализацию:

```text
tasks/T-XXX.md -> claim -> edit tools/.. -> tests -> validate -> report
```

Promotion task не копирует draft вслепую. Она реализует принятое решение заново или аккуратно переносит выбранные части с тестами. Draft остаётся evidence и историей выбора.

## 03. Потенциал, который нужно раскрыть до синтеза

Мой вариант специально разделяет четыре разных сущности, которые раньше легко смешивались:

1. `variant` — смысловой вариант решения.
2. `pseudocode` — алгоритмическая форма варианта.
3. `draft code` — неисполняемый код-доказательство.
4. `implementation` — проверенный mainline-код в рабочем инструменте.

Если эти уровни смешать, возникают типовые проблемы:

- агент пишет код прямо в `tools/`, хотя решение ещё спорное;
- другой агент видит “дубль” и не раскрывает свой вариант;
- черновой код случайно попадает в commit;
- кто-то запускает код без preflight;
- synthesis сравнивает не идеи, а случайные diff-фрагменты;
- promotion превращается в copy-paste вместо engineering implementation.

## 04. Сравнение с известными вариантами

После записи независимого варианта выполнена сверка с существующими материалами: `T-238`, `sandbox/drafts/README.md`, `sandbox/templates/draft-code-manifest.template.json`, `queues/outbox/2026-06-24-t238-draft-code-sandbox.md`, `queues/outbox/2026-06-24-sandbox-intake-chain-map.md` и `tools/sandbox_schema_validator.py`.

Совпадает:

1. `sandbox/drafts/` уже должен быть no-execute зоной.
2. Draft code — proposal/evidence, не implementation.
3. Нужен manifest.
4. Нужен static review.
5. Нужна отдельная promotion task.
6. Нельзя запускать, ставить зависимости, хранить secrets или напрямую переносить в mainline.

Мой вариант добавляет:

1. independent stream до обращения к draft code;
2. явный слой pseudocode variant;
3. сравнение вариантов по conditions/tradeoffs/tests/risks/promotion cost;
4. запрет на преждевременное “это уже есть” до раскрытия варианта;
5. будущий вопрос про отдельный статус `ready-for-static-review`.

Не является конфликтом: существующий `sandbox/drafts/` остаётся полезным. Мой вариант уточняет вход в эту зону и критерий сравнения нескольких кодовых вариантов.

### 04.1. Мой рекомендуемый workflow

### 04.1. Для агента-автора

```powershell
# 1. Создать stream-вариант
python tools\top.py variant-start codex <topic> --task T-id

# 2. Заполнить STREAM.md как независимый ответ
# 3. Если нужен алгоритм, добавить pseudocode.md
# 4. Если нужен черновой код, создать draft packet в sandbox/drafts/<draft-id>/
# 5. Не запускать draft code
# 6. Пометить stream ready-for-synthesis только когда раскрыты условия, риски, evidence
python tools\stream.py mark <stream-id> ready-for-synthesis "variant completed"
```

### 04.2. Для reviewer/observer

```powershell
python tools\top.py synthesize-docs <topic> --ready-only --json
python tools\stream.py check --max-age-days 7
# read-only review draft manifest, pseudocode, src, tests
```

Reviewer не обязан выбирать победителя сразу. Его задача — отделить:

- consensus candidates;
- divergence candidates;
- unsafe drafts;
- ready-for-promotion drafts.

### 04.3. Для integrator

Integrator создаёт отдельную promotion task только после synthesis:

```text
T-new: Promote selected draft/variant into tools/<name>.py with tests
```

Promotion task должна иметь:

- ссылки на все варианты;
- почему выбран этот вариант;
- что отвергнуто;
- какие tests обязательны;
- какие safety gates пройдены;
- какие файлы mainline можно трогать.

## 05. Evidence / проверки

Evidence для этого варианта:

- независимый вариант записан до сверки: `streams/code-variant-sandbox/20260625-1818-codex/STREAM.md`;
- существующий механизм после сверки: `tasks/T-238.md`, `sandbox/drafts/README.md`, `sandbox/templates/draft-code-manifest.template.json`;
- outbox-свидетельства: `queues/outbox/2026-06-24-t238-draft-code-sandbox.md`, `queues/outbox/2026-06-24-sandbox-intake-chain-map.md`, `queues/outbox/2026-06-24-unused-advice-audit.md`;
- tools-свидетельства: `tools/sandbox_schema_validator.py`, `tools/sandbox_intake_chain.py`;
- проверка synthesis route: `python tools\top.py synthesize-docs code-variant-sandbox --ready-only --json`.

### 05.1. Кодовая песочница как “средний слой”

Моё мнение: кодовая песочница должна быть не мусорной папкой и не вторым mainline, а средним слоем между мыслью и реализацией.

```text
streams/          = смысл, условия, reasoning, synthesis contract
sandbox/drafts/   = черновой код, псевдокод, fixtures, review material
tools|drivers|... = mainline implementation after promotion
```

То есть `streams/` отвечает на вопрос “почему и какой вариант”, а `sandbox/drafts/` отвечает на вопрос “как это могло бы выглядеть технически”.

## 06. Что должно быть запрещено

1. Запуск draft code без отдельного accepted run plan.
2. Установка зависимостей из draft-зоны.
3. Импорт draft code из mainline.
4. Автоматическое promotion из `sandbox/drafts/` в `tools/`.
5. Commit raw draft folders по умолчанию.
6. Замена independent variant на ссылку “это уже есть”.
7. Сравнение вариантов только по названию файла или задачи.
8. Закрытие divergence простым большинством без evidence.

## 07. Что должно быть автоматизировано позже

Я бы строил автоматизацию в таком порядке:

1. `top.py code-variant-start` — создаёт stream + optional draft skeleton, но не пишет mainline.
2. `tools/draft_code.py create/check/list` — управляет `sandbox/drafts/` как no-execute пакетами.
3. `doc_synthesis.py --ready-only` — уже есть для stream maturity.
4. `draft_code.py review` — read-only статическая сводка manifest/src/tests/risks.
5. `top.py code-variant-review` — верхняя команда для observer.
6. `promote.py` — принимает только reviewed draft + accepted/approved promotion task.

## 06. Вопросы другим агентам и людям

1. Должен ли псевдокод жить рядом со stream (`streams/.../pseudocode.md`) или рядом с draft code (`sandbox/drafts/.../pseudocode.md`)?
2. Нужно ли хранить raw draft folders в Git, или только manifest/report, а сырой код держать ignored до promotion?
3. Нужен ли отдельный статус `ready-for-static-review`, отличающийся от `ready-for-synthesis`?
4. Может ли observer редактировать draft code, или только оставлять review notes?
5. Как сравнивать два code-варианта: по tests, complexity, risk, API clarity, portability, dependency footprint?
6. Когда draft code можно считать “мертвым грузом” и архивировать?

## 07. Synthesis contract

- consensus candidates: preliminary code must not go straight to mainline; stream reasoning and draft code packet should be separate; execution remains off; promotion is a separate task.
- divergence candidates: exact folder for pseudocode; whether raw draft code is tracked; whether `ready-for-static-review` is a separate status; whether top command creates draft skeleton automatically.
- adoption target: docs/policy first, then optional `top.py code-variant-start` and `tools/draft_code.py` only after comparison.
- reject/supersede condition: if existing `sandbox/drafts/` policy already covers all necessary layers and only needs documentation, this stream becomes independent confirmation plus minor amendments, not a competing implementation.

## 08. Self-critique note

This stream intentionally starts with a complete Codex variant before comparing with existing repo mechanisms. That corrects the previous error where Codex searched existing mechanisms first and prematurely collapsed the topic into “do not duplicate”.