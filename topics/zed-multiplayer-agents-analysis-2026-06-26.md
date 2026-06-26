---
id: zed-multiplayer-agents-analysis-2026-06-26
type: topic
title: Zed multiplayer agents analysis and repo synthesis
status: proposed
owner: codex
date: 2026-06-26
related:
  - zed-like-headless-workbench-mvp
  - repo-as-collaborative-dev-service-2026-06-26
  - top-layer-throughput-methodology
  - workflow-orchestration-policy
---

# Zed Multiplayer Agents Analysis

## 1. Краткий вывод

Zed важен для этого проекта не как "еще один AI editor", а как внешний
пример архитектуры, где несколько людей, несколько агентов, thread history,
worktree isolation, terminal threads, external agents, MCP и local model routing
собраны в одну рабочую поверхность.

Для текущего репозитория наиболее полезная адаптация:

```text
не GUI-клон Zed
а headless/file-native Zed-like workbench
```

То есть:

- `topics/` и `streams/` = долговечные треды и варианты;
- `pipeline/conveyor` = очередь и lifecycle;
- `worktree/merge_gate` = изоляция writer-агентов;
- `drivers/gateway` = MCP-like tool surface;
- `top.py` = командная панель;
- будущий `thread.py` = недостающий Thread object;
- будущий `workspace-cell` = единая карточка состояния.

## 2. Что говорит Zed

По официальной документации Zed Parallel Agents запускает несколько agent threads
и terminal threads одновременно из Threads Sidebar; каждый thread имеет свой
context window и conversation history. Документация также описывает thread types:
Zed Agent thread, External Agent thread через ACP, Terminal Thread для CLI/TUI.

Worktree isolation в Zed решает проблему одновременного редактирования: если
две нити могут менять одни файлы, одну запускают в отдельном Git worktree, затем
review/merge идет обычным Git workflow.

Zed External Agents показывают важную границу ответственности: Zed держит thread
surface, а внешний агент владеет runtime, auth, model, tools и native config.
Terminal Threads еще жестче: Zed организует terminal-backed thread, а CLI сам
владеет ключами, моделью, tools, skills и MCP config.

Zed также поддерживает локальные модели через Ollama, LM Studio и OpenAI-compatible
server, а MCP используется как стандартный путь к внешним tools/data.

## 3. Что говорит статья Digital Applied

Статья полезно формулирует основной тезис: одиночный AI editor плохо переносит
командные сценарии, потому reasoning и tool traces остаются в личной сессии.
Zed делает ставку на общий рабочий слой: люди и агенты смотрят в общий buffer,
thread/channel history сохраняется, а работа становится коллективной.

Но это вторичный обзор, а не спецификация. Поэтому для реализации в нашем
репозитории статья используется как источник идей, а точные выводы сверяются
с официальными Zed docs.

## 4. Сравнение с текущим проектом

| Вопрос | Zed | Наш репозиторий сейчас | Следующий шаг |
|---|---|---|---|
| Где живет разговор? | Threads Sidebar / Agent Panel | `topics/`, `queues/`, `streams/` | `tools/thread.py` |
| Как виден статус? | sidebar indicators | `PIPELINE.md`, `LIVE.md`, `conveyor --json` | `workspace-cell` |
| Как не конфликтовать? | Git worktree isolation | `worktree.py`, `flow.py`, `merge_gate.py` | `worktree status/check` |
| Как подключать внешних агентов? | ACP / Terminal Threads | subagents + handoff packets | handoff v2 + terminal descriptor |
| Как подключать tools? | MCP | `drivers/gateway` | thread tool whitelist |
| Как работать оффлайн? | local models | пока нет local adapter | `drivers/local-llm` |
| Как хранить знания? | thread history | Markdown/JSON + SQLite/FTS | thread registry + generated index |

## 5. Почему не надо сразу делать GUI

GUI Zed решает проблему live buffer collaboration. У нас текущая проблема иная:
большая папка-проект, много Markdown/JSON/Python, несколько агентов и людей,
много старых вопросов, задач, потоков и синтезов.

Поэтому первый выигрыш даст не графический редактор, а:

1. единая thread-карточка;
2. единая workspace-cell карточка;
3. terminal-thread transcript;
4. локальная модель как optional adapter;
5. sandbox для чернового кода;
6. видимая очередь `open -> landed -> synthesis -> adoption -> commit`.

Это быстрее, переносимее и лучше соответствует текущей "середине пирамиды".

## 6. Offline/headless stack

Минимальная сборка:

```text
Windows filesystem / Git
  -> repo canon: docs/topics/tasks/questions/decisions
  -> top.py / pipeline / conveyor / stream / worktree / merge_gate
  -> drivers/gateway MCP-like read-only tools
  -> tools/thread.py
  -> optional local LLM endpoint
  -> optional CLI agents: Aider/OpenCode/Codex/Claude/etc.
  -> sandbox/drafts for code variants
```

Локальные/оффлайн компоненты:

- Aider может работать с Ollama и полезен как terminal-first agent.
- OpenCode поддерживает local models and many providers and can be a TUI/CLI agent.
- Tabby полезен как self-hosted coding assistant / server layer.
- Zed itself can be installed locally and source code is public, but direct code reuse
  needs license review because of GPL.

## 7. Связь с .inf, вопросниками и CRDT

Из Claude JSON и существующих topics видно, что параллельно развивается линия:
`.inf` format, macros, collapsible views, saved views, block IDs, CRDT,
Automerge/Yjs, Q6/Hamming semantics, verify-once, trust/provenance.

Мой вывод:

1. `.inf` и CRDT - не замена thread/worktree/governance.
2. Они должны стать более тонким слоем внутри thread messages и hot files.
3. Ближайший практический шаг - stable block IDs and view slices, не full CRDT.
4. CRDT нужен там, где есть реальное offline concurrent editing без merge-base.
5. Для кода CRDT опасен без review: он помогает слить текст, но не доказывает
   корректность программы.

## 8. Новый вопросник

### 8.1. Thread object

1. Что является source-of-truth thread: папка в `topics/` или глобальный JSON?
2. Как thread связывается с `task_id`, `stream_id`, `workflow_id`, `worktree`?
3. Какие статусы нужны: `open`, `running`, `blocked`, `landed`, `synthesis`,
   `accepted`, `archived`?
4. Кто имеет право закрыть thread?
5. Как хранить late messages после synthesis?

### 8.2. Terminal threads

1. Нужно ли реально управлять PTY или достаточно transcript descriptor?
2. Как фиксировать cwd/env без утечки секретов?
3. Какие CLI агенты разрешены в `read-only`, `draft`, `build` режимах?
4. Где хранить outputs: `queues/outbox`, `streams`, `sandbox/drafts`?
5. Как отличить "ответ агента" от "изменение, которое можно принять"?

### 8.3. Local LLM

1. Использовать Ollama напрямую или OpenAI-compatible abstraction?
2. Какой default context budget?
3. Как проверять, что контекст не был тихо обрезан?
4. Как отключить local model без поломки workflow?
5. Какие задачи можно давать local model: summarization/search/draft, но не
   governance acceptance?

### 8.4. MCP/tools

1. Какие tools read-only разрешены всегда?
2. Нужно ли давать модели прямой `files_read` или только curated context?
3. Как логировать tool calls в thread transcript?
4. Как version tools/capabilities, чтобы агент не работал по старым знаниям?
5. Когда execute-tools могут быть включены?

### 8.5. Sandbox for code variants

1. Где хранить code drafts?
2. Можно ли агенту писать patch diff вместо файлов?
3. Кто запускает тесты?
4. Как сравнивать два разных варианта кода?
5. Когда draft становится worktree task?

### 8.6. Governance

1. Как показать consensus vs disagreements в dashboard?
2. Как сохранить minority/late variants?
3. Как предотвратить "один агент написал - значит принято"?
4. Как хранить evidence для каждого принятого пункта?
5. Как сделать кнопки для человека: `accept`, `ask-more`, `send-to-sandbox`,
   `send-to-worktree`, `archive`?

## 9. Рекомендуемый порядок реализации

1. Создать задачу `thread schema MVP`.
2. Реализовать `tools/thread.py init/status/add-message` без LLM.
3. Добавить `tools/test_thread.py`.
4. Добавить `top.py thread` или `top.py workspace-cell`.
5. Описать terminal-thread descriptor.
6. Описать `sandbox/drafts/code` convention.
7. После этого добавлять local LLM adapter.
8. После local adapter добавлять optional `thread ask`.
9. После thread ask добавлять dashboard/static view.
10. После dashboard возвращаться к CRDT/block reconcile.

## 10. Что поручать агентам

### Read-only explorer

Задача: найти все существующие thread/workflow/worktree/stream команды и gaps.
Выход: `queues/outbox/<date>-thread-workbench-map.md`.

### Docs synthesizer

Задача: собрать из существующих вопросников пункты, связанные с `.inf`, CRDT,
view slices, trust, macros, terminal threads.
Выход: `topics/zed-workbench-question-synthesis-<date>.md`.

### Code worker

Только после утверждения: реализовать `tools/thread.py` stdlib-only.
Write scope: `tools/thread.py`, `tools/test_thread.py`, docs for command.

### Reviewer

Задача: проверить, что `thread.py` не запускает shell, не пишет вне root,
не логирует secrets and has stable JSON schema.

## 11. Резюме для котла

Consensus candidate:

- Копировать Zed как GUI сейчас не нужно.
- Нужен headless/file-native workbench.
- Первые build targets: `thread.py`, `workspace-cell`, terminal-thread descriptor.
- Local LLM should be optional and behind OpenAI-compatible adapter.
- Code-writing agents should first write to sandbox/worktree, not mainline.
- CRDT is useful later, after stable block/thread model.

Disagreements / open:

- где source-of-truth registry: local topic folders vs global log;
- насколько быстро включать local LLM;
- нужен ли ACP adapter before/after terminal-thread MVP;
- какой формат thread messages: Markdown-first, JSON-first or hybrid;
- когда moving from draft-code sandbox to executable sandbox is allowed.
## 12. Downloads / .inf sample synthesis

After the first Zed analysis, today's Downloads files were inventoried and selected samples were copied into:

```text
sandbox/intake/2026-06-26-inf-zed-samples/
```

Read-only subagent consensus from Russell, Lorentz and Rawls:

- `.inf` is useful as research vocabulary: stable block IDs, typed links, graph walk, territory+references, view slices and falsification harnesses.
- It should not become the canonical repository format now. Markdown + front-matter remains the canon.
- `infon.py` is a portable parser/graph/view prototype.
- `inf_accuracy.py` and `inf_falsify.py` are immediately valuable as method: context reduction must be tested against recall/answer quality, not assumed.
- `inf_crdt.py` is useful for structured block convergence research, but LWW body merge can silently drop meaning and must not be used for canon text without conflict surfacing.
- `inf_collab.py` demonstrates local endpoint collaboration, but all `--llama` paths stay disabled until a local-LLM adapter/preflight exists.

Practical adoption order:

1. T-264 `thread schema MVP`.
2. `workspace-cell` aggregator.
3. `view/context recall` acceptance test inspired by `inf_accuracy.py`.
4. `sandbox/drafts/code` convention for agent code variants.
5. Block-level reconcile research with explicit conflict flags.
6. CRDT/Automerge/Yjs only after the previous layers are stable.

Rejected for now:

- GUI clone of Zed;
- copying Zed source into this repo;
- making `.inf` canon;
- Hamming/Q6 as sole relevance mechanism;
- silent LWW body merge for canon text;
- macro/tool execution from text;
- executing Downloads scripts during intake.
