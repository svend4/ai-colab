---
id: zed-like-headless-workbench-mvp
type: doc
title: Headless Zed-like workbench MVP
status: proposed
owner: codex
date: 2026-06-26
related:
  - top-layer-throughput-methodology
  - workflow-orchestration-policy
  - independent-variant-stream-policy
  - repo-as-collaborative-dev-service-2026-06-26
  - inf-questionnaire-expanded-2026-06-26
---

# Headless Zed-like Workbench MVP

Этот документ фиксирует практический план: как использовать идеи Zed
Multiplayer/Parallel Agents без попытки сразу строить полноценный GUI-редактор.
Цель ближнего этапа - сделать в этом репозитории **file-native offline/headless
workbench**: несколько людей и агентов работают через задачи, треды, streams,
worktrees, MCP gateway, локальную модель и проверяемые отчеты.

Статус: `proposed`. Это не принятое архитектурное решение, а вариант Codex,
сверенный с read-only выводами Ptolemy, Goodall и Hegel.

## 0. Источники

- Внешняя статья: <https://www.digitalapplied.com/blog/zed-ai-coding-deep-dive-multiplayer-agents-2026>
- Zed GitHub: <https://github.com/zed-industries/zed>
- Zed Parallel Agents: <https://zed.dev/docs/ai/parallel-agents>
- Zed External Agents: <https://zed.dev/docs/ai/external-agents>
- Zed Terminal Threads: <https://zed.dev/docs/ai/terminal-threads>
- Zed local models: <https://zed.dev/docs/ai/use-a-local-model>
- Zed MCP: <https://zed.dev/docs/ai/mcp>
- Aider Ollama: <https://aider.chat/docs/llms/ollama.html>
- OpenCode providers: <https://opencode.ai/docs/providers/>
- Tabby GitHub: <https://github.com/TabbyML/tabby>

Примечание: статья Digital Applied полезна как обзор и набор тезисов, но
для архитектурных решений лучше опираться на первичные источники Zed docs/GitHub.

## 1. Независимый вариант Codex до сверки

Если бы я строил это заново для текущего репозитория, я бы не начинал с GUI.
Оптимальная первая версия - **control plane поверх файлового канона**.

Минимальные сущности:

1. `thread` - долговечная рабочая нить: тема, участники, модель/агент, контекст,
   история сообщений, выходные файлы, связанные задачи и worktree.
2. `terminal-thread` - особый thread, где исполняется внешний CLI/TUI агент
   или локальный runner, но transcript пишется в репозиторий как проверяемый
   Markdown/JSON.
3. `workspace-cell` - единая карточка состояния:
   `task + claim + stream + worktree + outbox + checks + commit status`.
4. `local-llm-adapter` - один тонкий OpenAI-compatible слой над Ollama, LM Studio,
   llama.cpp/vLLM или удаленным endpoint. По умолчанию только localhost.
5. `mcp-gateway` - read-only доступ к файлам, поиску, памяти, SQLite, repo-inspect.
6. `draft-code-sandbox` - место, куда агенты могут писать псевдокод, патчи и
   прототипы, которые не исполняются и не попадают в mainline без review.
7. `synthesis-gate` - механизм, который не стирает варианты: consensus отдельно,
   disagreements отдельно, adoption отдельно.

Ключевой тезис: Zed полезен не тем, что "у него есть чат с AI", а тем, что
он соединяет **thread history + worktree isolation + external agents + terminal
threads + MCP/local model routes** в одну рабочую поверхность. В нашем проекте
такая поверхность может быть файловой, а не графической.

## 2. Что у нас уже есть

| Zed-like функция | В Zed | В текущем репозитории | Gap |
|---|---|---|---|
| Thread registry | Threads Sidebar | `topics/`, `queues/`, `streams/`, `conveyor` | нет единой карточки thread/worktree/task |
| Parallel agents | multiple agent threads | `workflow`, subagents, `conveyor`, `pipeline` | нет durable thread object |
| Worktree isolation | linked Git worktrees | `tools/worktree.py`, `tools/flow.py --worktree`, `merge_gate.py` | нужен status/check/orphan view |
| External agents | ACP | `subagent-handoff`, platform subagents, future MCP/ACP bridge | нет ACP adapter |
| Terminal threads | CLI/TUI inside Zed thread | пока только обычный terminal + отчеты | нужен `tools/thread.py` или `tools/terminal_thread.py` |
| MCP | Zed MCP servers | `drivers/gateway/mcp_server.py`, files/repo/workbench drivers | read-only готов, execute закрыт |
| Local models | Ollama/LM Studio/OpenAI-compatible | пока нет unified local LLM adapter | нужен `drivers/local-llm` |
| UI panel | Agentic layout | `tools/top.py buttons`, docs, JSON | нужен dashboard/portal позже |

Вывод: архитектурно проект уже близок к headless Zed-like control plane. Самый
крупный практический пробел - не CRDT и не GUI, а **единая долговечная thread
карточка**, которая связывает разговор, файлы, агентский запуск, worktree, вывод
и проверки.

## 3. Offline/local аналоги и их роль

### 3.1. Zed

Zed открыт на GitHub, написан преимущественно на Rust и распространяется
в основном под GPL-3.0-or-later с отдельными Apache-2.0 компонентами. Это значит:
идеи можно изучать свободно, но копирование кода в этот проект требует отдельной
лицензионной проверки. Практически безопаснее брать **архитектурные паттерны**:
threads, terminal threads, worktree isolation, MCP routing, local model routing.

### 3.2. Aider

Aider - terminal-first coding assistant. Он полезен как пример `terminal-thread`
семантики: агент живет прямо в git repo и может работать с Ollama. Для нашего
проекта это не замена control plane, а один из возможных CLI-агентов, transcript
которого можно завернуть в `topics/.../messages/` и `queues/outbox/`.

### 3.3. OpenCode

OpenCode - open-source coding agent с TUI/CLI и поддержкой многих провайдеров,
включая local models. Для нас это кандидат на внешний terminal-thread agent.
Его не нужно встраивать жестко: достаточно сделать runner-карточку, где команда,
cwd, модель, ограничения и выходные файлы фиксируются явно.

### 3.4. Tabby

Tabby - self-hosted/on-prem AI coding assistant. Его полезно рассматривать как
пример локального сервера/службы для autocomplete/chat/context, но не как готовую
замену Zed-like multiplayer. Для нашего проекта Tabby ближе к слою "локальный
провайдер возможностей", а не к слою orchestration/governance.

### 3.5. Локальные модели

Ollama, LM Studio, llama.cpp/vLLM/LocalAI лучше не вшивать по одному. Нужен
один контракт:

```text
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen2.5-coder
LOCAL_LLM_API_KEY=optional
```

Runner не должен требовать локальную модель для обычной работы репозитория.
Если endpoint не задан, команды должны печатать понятный `NOT CONFIGURED`,
а не падать и не зависать.

## 4. MVP: что именно построить

### Stage A. Thread schema без модели

Сначала сделать thread как файловый объект, без LLM:

```text
topics/<topic>/threads/<thread-id>/THREAD.json
topics/<topic>/threads/<thread-id>/messages/YYYY-MM-DD-HHMM-<role>.md
topics/<topic>/threads/<thread-id>/artifacts/
```

Минимальная схема:

```json
{
  "schema": "thread.v1",
  "id": "thread-2026-06-26-001",
  "topic": "zed-like-headless-workbench",
  "status": "open",
  "agent": "codex",
  "mode": "read-only|draft|build|terminal",
  "task_id": null,
  "stream_id": null,
  "worktree": null,
  "model": null,
  "tools": ["gateway.files_search", "repo_inspect"],
  "outputs": [],
  "checks": []
}
```

Команды:

```powershell
python tools\thread.py init zed-like-headless-workbench --agent codex --mode read-only
python tools\thread.py add-message <thread-id> user --file queues\inbox\...
python tools\thread.py status <thread-id> --json
python tools\top.py thread <thread-id> --json
```

Зачем это нужно: появляется аналог Threads Sidebar, но файловый. Любой человек
или агент может увидеть, какие thread открыты, кто ведет работу, где outputs,
какие проверки и что дальше.

### Stage B. Terminal-thread transcript

Добавить режим, который фиксирует запуск внешнего CLI/TUI агента как managed
session descriptor. На первом этапе **не надо** автоматизировать интерактивный
PTY. Достаточно описать и логировать:

```json
{
  "schema": "terminal_thread.v1",
  "thread_id": "...",
  "cwd": "C:/Users/stefan/Documents/New project ai colab",
  "command": "aider --model ollama_chat/qwen2.5-coder",
  "env_policy": "redacted",
  "allowed_writes": ["sandbox/drafts/", "streams/<topic>/"],
  "forbidden_writes": ["decisions/* accepted", "mainline code without review"],
  "transcript": "messages/2026-06-26-....md"
}
```

Правило: terminal-thread может писать черновики, но не имеет права сам считать
изменения принятыми. Для кода: сначала `sandbox/drafts/` или отдельный worktree,
потом review, tests, merge_gate.

### Stage C. Local LLM adapter

Добавить `drivers/local-llm/` как thin adapter, но только после Stage A/B.
Минимальная приемка:

1. Если endpoint не задан - `NOT CONFIGURED`, exit 0/2 по принятому контракту.
2. Если задан mock endpoint - отправить короткий prompt и получить ответ.
3. Не логировать API key.
4. По умолчанию разрешить только localhost.
5. Не давать модели прямой write/execute доступ.

Команды будущего:

```powershell
python drivers\local-llm\openai_compat.py ping
python tools\thread.py ask <thread-id> "Сделай обзор..." --model local
```

### Stage D. MCP gateway как tool surface

Модель не должна сама читать диск произвольно. Runner собирает контекст через
белый список:

```text
files_search
files_read
files_summarize
repo_inspect
memory_query
```

Execute-tools остаются закрытыми до отдельного accepted decision и песочницы.
Это отличие от Zed/CLI-agents: здесь safety важнее скорости.

### Stage E. Draft-code sandbox

Для кода нужна не только внешняя песочница, но и внутренняя зона черновиков:

```text
sandbox/drafts/code/<topic>/<agent>/<timestamp>/
  PLAN.md
  PSEUDOCODE.md
  PATCH.diff
  NOTES.md
  REVIEW.md
```

Правила:

- агент может писать сюда альтернативный код или псевдокод;
- код не исполняется автоматически;
- review-agent или Codex оценивает diff;
- только после проверки создается task/worktree/mainline patch.

Это решает старый конфликт "агенту надо дать полностью развить свой вариант,
но нельзя давать всем писать в один hot file".

### Stage F. Workspace-cell dashboard

После thread schema сделать агрегатор:

```powershell
python tools\top.py workspace-cell <thread-or-task> --json
```

Карточка должна показывать:

```text
task_id
claim/lease
thread_id
stream_id
worktree path/branch
outbox outputs
checks
blocking risks
next recommended command
```

Это практический аналог Zed Threads Sidebar + Git Panel + Agent Panel, но без GUI.

## 5. Как это связано с .inf и CRDT

Hegel правильно указал: после анализа Zed нужно расширять не только "агентов",
но и информационную модель.

Ближний порядок:

1. **Stable block ids** в документах и thread messages.
2. **View slices**: сохраненные представления "какие блоки раскрыты".
3. **Typed links/backlinks**: `depends_on`, `contradicts`, `supports`, `derived_from`.
4. **Block-level reconcile** для hot files: сначала field/line, потом sequence sidecar.
5. **CRDT позже**: Automerge/Yjs полезны для истинно offline concurrent editing, но
   преждевременны до thread/workspace-cell слоя.

Главное: CRDT решает конфликт записи, но не решает вопрос истины, качества,
governance и принятия. Поэтому CRDT должен идти после или рядом с synthesis-gate,
а не вместо него.

## 6. Security policy

Минимальная безопасность MVP:

- Local LLM endpoint только `127.0.0.1` по умолчанию.
- API keys никогда не писать в transcript.
- MCP tools только read-only.
- Macro/effect blocks в `.inf` не исполнять как команды.
- `sandbox/drafts/` - write ok, execute no.
- mainline code - только через worktree/merge_gate.
- decisions `accepted` - только человек или явно назначенный интегратор.

## 7. План задач

Нужно заводить задачи через `tools/next_id.py`, когда инструмент доступен.
Предлагаемый порядок:

1. `thread schema MVP` - `tools/thread.py init/status/add-message`, тесты.
2. `workspace-cell read-only aggregator` - `top.py workspace-cell --json`.
3. `terminal-thread descriptor` - JSON schema + transcript convention.
4. `draft-code sandbox convention` - docs + optional validator.
5. `local-llm adapter` - OpenAI-compatible localhost ping + mock test.
6. `thread ask dry-run` - собирает prompt/context, но без модели пишет preview.
7. `thread ask local` - optional, если endpoint задан.
8. `MCP/thread acceptance` - transcript + gateway read-only tool result.
9. `thin dashboard` - static/report view над workspace-cell JSON.
10. `CRDT/block reconcile research` - только после 1-4.

## 8. Пропускная способность и верхний слой

Zed показывает важный принцип: много агентов не помогает, если человек/верхний
слой не успевает читать, сравнивать, принимать и сливать результаты. Для текущего
репозитория рабочая формула такая:

```text
agents_running <= synthesis_capacity + review_capacity + commit_capacity
```

Поэтому сначала нужно не запускать 20 writer-агентов, а сделать видимой очередь:

```text
open threads -> landed outputs -> needs synthesis -> accepted -> buildable -> committed
```

`workspace-cell` и `thread.py` должны уменьшить ручную стоимость этой очереди.

## 9. Сверка с агентами

### Ptolemy

Совпадение: Ptolemy подтвердил, что уже есть `top.py`, `pipeline.py`, `cohort.py`,
`worktree.py`, `flow.py`, `stream.py`, `merge_gate.py`, MCP gateway и файловые
threads. Его главный gap - нет durable terminal-session/thread object и единой
карточки `conversation + file diff + terminal + task`.

Вывод: Stage A/B/F - приоритет.

### Goodall

Совпадение: Goodall предложил именно offline/headless Zed-like stack:
local model, terminal-thread runner, local MCP, Markdown threads, SQLite/FTS,
strict sandbox gate. Он правильно отделил реалистичный MVP от полноценного
Zed GUI.

Вывод: не копировать GUI, строить terminal/file-native workbench.

### Hegel

Совпадение: Hegel нашел существующие вопросники и расширил Zed-анализ в сторону
CRDT, thin client board, verify-once/trust, block-level reconcile, governance UX,
security/capability layer.

Вывод: CRDT и `.inf` важны, но не должны опережать thread/workspace-cell слой.

## 10. Открытые вопросы

1. Должен ли `thread.py` быть полностью stdlib-only, как большинство текущих tools?
   Предварительный ответ: да.
2. Где хранить thread registry: в `topics/<topic>/threads/` или глобально
   `logs/threads.json`?
   Предварительный ответ: оба слоя; source-of-truth рядом с topic, глобальный
   индекс генерируемый.
3. Нужно ли сразу запускать локальные модели?
   Предварительный ответ: нет; сначала dry-run и mock acceptance.
4. Можно ли дать агентам писать код?
   Предварительный ответ: да, но сначала в `sandbox/drafts/code/` или отдельный
   worktree, не в mainline.
5. Нужен ли ACP adapter?
   Предварительный ответ: позже. Сейчас достаточно platform subagents и
   terminal-thread descriptors.
6. Нужно ли копировать код Zed?
   Предварительный ответ: нет. Лицензия и масштаб делают это нецелесообразным;
   полезнее перенести архитектурные принципы.

## 11. Критерий готовности MVP

MVP можно считать готовым, когда выполняется сценарий:

```powershell
python tools\thread.py init zed-like-headless-workbench --agent codex --mode read-only
python tools\thread.py add-message <thread-id> user --text "Разобрать Zed"
python tools\top.py workspace-cell <thread-id> --json
python tools\thread.py add-output <thread-id> queues\outbox\...
python tools\thread.py status <thread-id> --json
python tools\validate.py
```

И человек видит:

- кто работает;
- где thread;
- какие output files;
- что проверено;
- что спорно;
- что можно принять;
- что нужно отправить в worktree/sandbox.
## 12. Intake samples 2026-06-26

A read-only sandbox copy of the 2026-06-26 `.inf`/CRDT/context samples is stored in:

```text
sandbox/intake/2026-06-26-inf-zed-samples/
```

Use these samples as experimental evidence, not as mainline architecture:

- `infon.py` suggests a compact block graph, typed links, Q6 vector, walk, cluster and validation commands.
- `inf_crdt.py` is useful for convergence experiments, but its LWW body strategy is not acceptable for canon text unless conflicts are surfaced.
- `inf_accuracy.py` and `inf_falsify.py` are the strongest immediate lessons: context slices must be tested for recall, missing load-bearing facts and repeated-read reduction.
- `inf_collab.py` shows a local endpoint collaboration shape, but local model calls remain disabled until a separate adapter/preflight exists.

Next practical consequence: after `T-264 thread schema MVP`, add a `view/context recall` task. The test should prove that a terminal-thread or saved view does not silently drop an exception or dependency outside the first selected slice.
