---
id: 20260625-1942-codex
topic: code-variant-draft-manager
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
task: T-260
phase: independent-plus-subagent-review
---

# Stream: code-variant-draft-manager / Codex variant

## 00. Причина независимого варианта

T-257 уже зафиксировал принцип `draft code is evidence, not implementation`, но оставил автоматизацию на потом. T-260 делает следующий малый шаг: не execute runner, не promotion tool, а no-execute manager для черновых code packets.

## 01. Условия применимости

Этот вариант применим, когда агент хочет предложить кодовую идею, псевдокод, адаптер, тестовый фрагмент или prototype, но mainline (`tools/`, `drivers/`, `core/`, `portals/`) менять рано.

Условия:

1. Решение спорное или имеет несколько вариантов.
2. Нужно сохранить потенциал агента, не схлопывая работу словами "это уже есть".
3. Код нельзя запускать автоматически.
4. Требуется manifest, static review и separate promotion task.
5. Нужно дать людям и агентам одну короткую команду для безопасного draft packet.

## 02. Независимый ответ агента

Мой вариант: сделать маленький `tools/draft_code.py`, который управляет только quarantine packet lifecycle:

```text
create -> check -> review -> list
```

Он не должен:

- запускать draft code;
- импортировать draft modules;
- ставить зависимости;
- писать в mainline;
- создавать promotion автоматически;
- подменять synthesis.

Он должен:

- создавать `sandbox/drafts/<draft-id>/manifest.json`;
- создавать `README.md`, `pseudocode.md`, `notes.md`, `src/`, `tests/`;
- валидировать manifest через `sandbox_schema_validator.py`;
- запускать только read-only `sandbox_intake_chain.scan(..., kind="agent-draft")`;
- возвращать machine-readable JSON;
- всегда печатать `execution_allowed: false`.

## 03. Потенциал, который нужно раскрыть до синтеза

Нужно раскрыть не только папку, но и смысловой контракт:

- `streams/<topic>/<stream>/STREAM.md` объясняет why/conditions/tradeoffs;
- `streams/.../pseudocode.md` может быть смысловым псевдокодом варианта;
- `sandbox/drafts/<draft-id>/pseudocode.md` описывает конкретный draft packet;
- `manifest.json` является машинным карантинным контрактом;
- `review` не даёт merge-разрешения, а даёт route: keep-quarantine / create-promotion-task / ask-agent-revision.

## 04. Сравнение с известными вариантами

Consensus:

1. Нужен quarantine manager, а не runner.
2. Draft code не implementation, а evidence.
3. Execute, dependency install, network и import запрещены.
4. Manifest `draft-code-proposal.v1` обязателен.
5. Raw drafts по умолчанию не попадают в Git.
6. Promotion только отдельной claimed задачей.
7. Static review read-only.
8. `sandbox_intake_chain.py` уже правильный нижний слой review.

Divergence / открытые вопросы:

1. Нужен ли отдельный статус `ready-for-static-review` в stream lifecycle.
2. Нужен ли top-wrapper сразу или после core manager. Codex принял компромисс: core first, затем только тонкий proxy `top.py draft-code ...` после зелёных тестов.
3. Хранить ли selected review bundle в Git. Сейчас: raw draft ignored, отчёты и manifest examples можно коммитить отдельно.
4. Кто утверждает accepted run plan для исполнения draft. Сейчас: никто из агентов автоматически.

## 05. Evidence / проверки

Использованные материалы:

- `queues/outbox/2026-06-25-independent-code-variant-policy.md`
- `streams/code-variant-sandbox/20260625-1818-codex/STREAM.md`
- `sandbox/drafts/README.md`
- `sandbox/templates/draft-code-manifest.template.json`
- `tools/sandbox_intake_chain.py`
- `tools/sandbox_schema_validator.py`

Sub-agents:

- Averroes подтвердил quarantine manager и два уровня псевдокода.
- Kierkegaard рекомендовал сначала отдельный `tools/draft_code.py`, а `top.py` трогать позже из-за hot-file риска.

## 06. Вопросы другим агентам и людям

1. Нужен ли статус `ready-for-static-review` как отдельный этап между draft и synthesis?
2. Нужно ли делать export review bundle для Git, если raw draft ignored?
3. Когда top-wrapper считать обязательным: после одного зелёного core теста или после второго agent variant?
4. Можно ли observer-у редактировать draft, или только писать review notes / fork?

## 07. Synthesis contract

- consensus candidates: draft manager no-execute; manifest required; review read-only; promotion separate task.
- divergence candidates: stream status, Git export bundle, top-wrapper timing, observer edit rights.
- adoption target: `tools/draft_code.py`, tests, docs, thin `top.py draft-code` proxy; richer lifecycle statuses as follow-up.
- reject/supersede condition: если `sandbox_intake_chain.py` будет расширен до полного draft manager, этот stream можно закрыть как historical confirmation.

## 08. Обоснование правок

Правки делаются в два шага: core lifecycle вынесен в отдельный `tools/draft_code.py`, а `top.py` получает только тонкий proxy без дублирования правил. Это снижает конфликтность общего дерева и соответствует новой политике: сначала раскрыть вариант, затем сравнить, затем внедрять минимально достаточный consensus.