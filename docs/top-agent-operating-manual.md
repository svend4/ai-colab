---
id: top-agent-operating-manual
title: Top Agent Operating Manual — чистовая инструкция вершины пирамиды
status: accepted
owner: Codex
last_verified: 2026-06-23
related: docs/bridge-usage.md, docs/layers-coverage.md, docs/architecture-docs-recheck-2026-06-21.md, AGENTS.md, PROTOCOL.md
---

# Top Agent Operating Manual

Дата: 2026-06-21.

Назначение: дать человеку или AI-агенту на "вершине пирамиды" чистовую инструкцию: что эта система умеет сейчас, как ей пользоваться, где лежат функции, что автоматизировано, что запрещено, какие вопросы уже возникали и как развивать середину пирамиды дальше.

Это не история разработки. История остаётся в `topics/`, `tasks/`, `queues/`, commit log. Этот документ — текущая operational-карта.

Связанный человеко-читабельный онбординг: `docs/agent-onboarding.md`. Если нужно быстро понять систему за 5-10 минут, начинайте с него. Если нужно действовать как агент и выбирать команды/микро-инструкции, используйте этот manual.

## 1. Короткие метаданные

```yaml
system_name: AI-OS Bridge / Information Workbench Layer
purpose: Средний слой между AI-клиентом и Windows/файлами/репозиториями/данными
current_stage: Рабочий read-only прототип, не execute-платформа
safe_default: read-only
control_plane: [AGENTS.md, PROTOCOL.md, TASKS.md, pipeline.py, validate.py, generate.py]
capability_plane: [drivers/, skills/, tools/, docs/, reports/]
dialog_plane: [topics/, queues/outbox/, docs/*result*.md]
memory_plane: [drivers/workbench, tools/knowledge.py, tools/repo_search.py, reports/, logs/*.db runtime]
driver_acceptance: D-015, tests + MCP acceptance + second-agent verification
current_l2_acceptance: sync MCP tools/call 27/27
current_l6: SQLite workbench, text_extract .md/.txt/.html, FTS5 search, report --out, safe corpus, regression test
execute_policy: forbidden_until_sandbox_and_accepted_decision
main_blocker: T-020 svend4/orphan claim, no read-only source provided
```

Минимальный health-check:

```powershell
python tools\top.py buttons
python tools\top.py status codex
python tools\top.py agent-start codex --context "<task topic>"
python tools\top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree
python tools\top.py health
python tools\pipeline.py status
python tools\validate.py
python tools\generate.py --check
python drivers\mcp_sync_acceptance.py
python tools\test_knowledge.py
```

## 2. Где лежит описание функций

| Что искать | Где лежит | Зачем |
|---|---|---|
| Правила агентов | `AGENTS.md`, `PROTOCOL.md` | кто что может делать |
| Быстрый старт | `docs/quickstart.md`, `docs/agent-quickstart.md` | первые шаги |
| Что умеет средний слой | `docs/bridge-usage.md` | текущие drivers, команды, acceptance |
| Карта слоёв | `docs/layers-coverage.md` | L0-L7, стадия проекта |
| Роли | `docs/agent-roles-matrix.md` | люди, агенты, скрипты |
| Драйверы | `drivers/CATALOG.md`, `drivers/index.json`, `drivers/*.md` | способности системы |
| Skills | `skills/README.md`, `docs/skills-usage.md` | переносимые процедуры |
| Safety | `docs/driver-safety-policy.md`, `drivers/SCHEMA.md`, `docs/execute-sandbox-preflight.md` | ограничения и запреты |
| Knowledge workflow | `tools/knowledge.py`, `data/knowledge-corpus/`, `reports/` | обработка корпуса и отчёты |
| Canon search | `tools/top.py repo-search`, `tools/repo_search.py` | быстрый поиск по docs/decisions/questions/темам/tasks |
| Top command panel | `tools/top.py` | сценарии/кнопки для людей и агентов |
| Sub-agent handoff | `tools/top.py subagent-handoff`, `tools/flow.py launch-plan` | repo lane + prompt для внешнего launcher |
| Doc consensus semantic runtime | `tools/doc_consensus.py`, `docs/doc-consensus-agent-runtime.md` | безопасный opt-in `$DOC_CONSENSUS_AGENT`, budget guard, proposed output |
| Text extraction | `tools/text_extract.py` | redacted `.md/.txt/.html` text для поиска и порталов |
| История обсуждения | `topics/ai-os-bridge.md`, `topics/*.md` | полилог и решения |
| Итоги задач | `docs/*result*.md`, `queues/outbox/`, `queues/done/` | что уже сделано |

## 3. Что может делать агент на вершине пирамиды

Агент на вершине не должен напрямую "жить в ОС". Он управляет средним слоем.

Разрешено по умолчанию:

- читать канон, индексы, задачи и темы;
- брать одну задачу через `pipeline.py next`;
- делать read-only анализ файлов, git history, CSV/TSV, SQLite-БД и repository inventory;
- создавать docs/reports/outbox/task updates;
- запускать проверенные tests/tools внутри workspace;
- добавлять proposed tasks/questions/decisions;
- улучшать validation, reports, docs refresh и regression tests.

Запрещено без отдельного решения:

- запускать чужой/непроверенный код;
- делать `install`, `run`, `test`, `docker compose up` в чужом репозитории;
- писать за пределы workspace;
- хранить секреты в репозитории;
- принимать `accepted` решения от имени человека;
- удалять чужие сообщения и переписывать историю;
- включать `mode: execute` без песочницы.

## 4. Рабочий цикл агента

```text
read current state
  -> pipeline.py status
  -> pipeline.py next <agent>
  -> top.py repo-search "<topic/query>" --limit 5
  -> inspect task and related docs
  -> make small scoped change
  -> write docs/outbox/topic rationale
  -> run focused tests
  -> generate.py
  -> validate.py
  -> pipeline.py done <agent> <task> --claim <claim_id>
  -> pipeline.py snapshot
  -> commit if coherent
```

Если готовых задач нет:

1. Не трогать `T-020` автоматически.
2. Найти следующий маленький improvement из current docs.
3. Создать task через `tools/next_id.py`.
4. Заполнить task как `owner: pool`.
5. Обновить индекс.
6. Взять задачу через pipeline.

## 5. Что уже автоматизировано

| Функция | Реализация | Стадия |
|---|---|---|
| Задачи/вопросы/решения | `tasks/`, `questions/`, `decisions/`, generated Markdown | рабочее |
| Claim/lease | `tools/pipeline.py`, `queues/claimed` | рабочее |
| Индексы | `tools/generate.py`, `index.json`, `drivers/index.json` | рабочее |
| Проверки | `tools/validate.py`, pre-commit hook | рабочее |
| Driver catalog | `drivers/*.md`, `drivers/CATALOG.md`, schema v1 | рабочее |
| MCP acceptance | `drivers/mcp_sync_acceptance.py` | рабочее, 27/27 |
| Read-only safety | allowed-root, mode guards, redaction | рабочее |
| Audit | `drivers/audit.py`, JSONL для risk>=medium | рабочее |
| L6 memory | `drivers/workbench`, `tools/knowledge.py`, `tools/text_extract.py` | рабочее на малых corpus |
| Reports | `reports/*.md`, `report --out`, regression test | рабочее |
| Sub-agent handoff | `top.py subagent-handoff`, `flow.py launch-plan` | рабочее как read-only launch-пакет |
| Skills | `skills/*/SKILL.md` | рабочее как project-local procedures |
| Execute sandbox | `docs/execute-sandbox-preflight.md` | только preflight |
| Plugin packaging | `docs/skills-usage.md` | будущий уровень |
| Real svend4 source | `T-020` | blocked/orphan |

## 6. Что мне не нравится в текущем устройстве

Если бы я начинал заново, я бы изменил следующее:

1. **Разделил current и history.** Сейчас рядом лежат актуальные инструкции и исторические отчёты. Новому агенту трудно понять, что читать первым.
2. **Убрал двойственность `queue.py` vs `pipeline.py`.** Актуальный путь — `pipeline.py`, но часть quickstart ещё говорит через старую очередь.
3. **Сделал единый machine-readable system manifest.** Есть `drivers/index.json`, но нет одного `system-capabilities.json` с commands, risks, docs links, maturity.
4. **Добавил drift detector.** Документы уже несколько раз отставали от фактов.
5. **Сделал onboarding command.** Новый агент должен запускать одну команду, а не читать 10 файлов вручную.
6. **Перевёл длинные темы в folder-topic режим.** Для большого полилога лучше `messages/` + `summary.md`, чем один длинный файл.
7. **Сделал task templates.** Driver, docs refresh, regression, corpus, review должны создаваться по шаблону.

## 7. Вопросы Stefan и ответы Codex

### 7.1. Где сейчас "середина пирамиды"?

Она не в одном файле. Она распределена:

- control plane: `AGENTS.md`, `PROTOCOL.md`, `TASKS.md`, `pipeline.py`;
- capability plane: `drivers/`, `skills/`, `tools/`;
- memory plane: `workbench`, `knowledge.py`, `reports/`;
- dialog plane: `topics/`, `queues/outbox/`;
- safety plane: `drivers/SCHEMA.md`, `driver-safety-policy.md`, `execute-sandbox-preflight.md`.

### 7.2. Это уже движок или набор файлов?

Это уже маленький движок, но file-native. Он не является серверной платформой. Его двигатель:

- generated indexes;
- pipeline claims;
- validation;
- driver acceptance;
- reports;
- commit history.

То есть система работает через файлы, но эти файлы уже имеют состояние, правила и автоматические проверки.

### 7.3. Может ли он улучшать себя?

Да, в безопасных границах.

Он уже может:

- находить stale docs;
- создавать tasks;
- брать задачи;
- менять tools/docs/drivers;
- запускать tests;
- закрывать задачи;
- коммитить результат;
- оставлять отчёты другим агентам.

Он не должен сам:

- принимать high-level accepted decisions;
- открывать execute;
- работать с секретами;
- запускать чужой код;
- подключать внешние серверы без человека.

Стадия: контролируемый self-improvement, не автономная AI-OS.

### 7.4. Как сделать общение агентов живее?

Нужно меньше свободного текста и больше маленьких машинных сигналов:

- `logs/events.jsonl`;
- `system-capabilities.json`;
- `agent heartbeat`;
- `what changed since last check`;
- `report diff`;
- topic summaries;
- priority broker;
- stale docs detector.

Живость должна идти через observable state, а не через бесконечный чат.

### 7.5. Какие проблемы коллективной работы уже были?

| Проблема | Как проявилась | Решение | Метод на будущее |
|---|---|---|---|
| Mojibake PowerShell | Русский текст отображался битым | UTF-8 setup | `docs/powershell-utf8-output.md` |
| Runtime hangs | shell/Python зависали | timeout wrappers | long commands с timeout |
| Temp permissions | тесты писали в запрещённый `%TEMP%` | `drivers/test_tmp.py`, `tmp-work/` | workspace-safe temp |
| Async MCP blocker | WinError 5 в async stdio | sync MCP probe/acceptance | sync path как regular gate |
| Orphan tasks | `doing` без claim | pipeline показывает blocker | не закрывать чужое молча |
| Placeholder noise | резервные задачи засоряли pipeline | placeholder gating | фиктивные задачи не ready |
| Docs drift | roadmap отставал | docs refresh tasks | drift detector |
| Driver status drift | `ready` без приёмки | D-015 | unit + MCP + second agent |
| Secret risk | files/data могли показать секреты | общий redaction helper | redaction в каждом read driver |
| Write-path risk | `report --out` пишет файл | safe path + suffix + regression | write tools требуют path tests |

### 7.6. Как автоматизировать середину дальше?

Реалистично:

1. `tools/onboard.py <agent>` — единая команда входа.
2. `tools/capabilities.py snapshot` — единый manifest возможностей.
3. `tools/drift_check.py` — искать stale statements и старые acceptance числа.
4. `tools/backlog_suggest.py` [planned] — предлагать новые tasks из current roadmap.
5. `tools/report_diff.py` — сравнивать Markdown reports между запусками.
6. `tools/topic_summarize.py` [planned] — обновлять summary без перезаписи истории.
7. `tools/safety_gate.py` [planned] — единая проверка перед network/write/execute.

Более концептуально:

- **Blackboard architecture:** общий слой карточек фактов, гипотез, задач и решений.
- **Cybernetic loop:** measure -> compare -> decide -> act -> verify.
- **Kanban + Andon:** ошибка validation/orphan task должна поднимать явный стоп-сигнал.
- **Library card catalog:** каждый driver/report/doc имеет карточку purpose, owner, freshness, commands.
- **Scriptorium model:** роли разделены: writer, reviewer, cataloguer, maintainer, runner.
- **Capability router:** агент описывает intent, router выбирает 1-3 drivers/skills.
- **Proof-carrying reports:** каждый отчёт содержит команду воспроизведения, входы, commit hash и ожидаемый минимум.

## 8. Микро-инструкции

### recheck-current-state

```powershell
git status --short --untracked-files=all
python tools\top.py buttons
python tools\top.py status codex
python tools\top.py agent-start codex --context "<task topic>"
python tools\top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree
python tools\top.py health
python tools\pipeline.py status
python tools\validate.py
python tools\generate.py --check
```


### choose-work-mode

```powershell
python tools\top.py work-mode <agent> <T-id>
python tools\top.py work-mode <agent> <T-id> --parallel --hot-files
```

Правило D-021: Level 0 shared tree остаётся дефолтом; Level 1 worktree включается явно, если задача параллельная, mainline грязная или ожидаются конфликты generated files.

### launch-subagent-handoff

```powershell
python tools\top.py subagent-handoff <agent> <T-id> "<topic/context>" --worktree
```

Использовать, когда нужно дать задачу внешнему worker-agent. Команда печатает repo lane, prompt, start/finish-команды и не делает side effects. Реальный запуск выполняет Codex/platform launcher или человек.

### take-one-task

```powershell
python tools\pipeline.py next <agent>
```

Сохранить `claim_id`; закрывать через `pipeline.py done ... --claim`.

### create-small-task

```powershell
python tools\next_id.py task --agent <agent>
```

Task должен иметь `owner: pool`, зависимости, `next` и конкретный критерий done.

### write-clean-report

Создать:

- `docs/<result>-YYYY-MM-DD.md`;
- `queues/outbox/YYYY-MM-DD-<short>.md`;
- запись в профильной теме, если изменение архитектурное.

### docs-refresh

Проверить:

- `docs/layers-coverage.md`;
- `docs/bridge-usage.md`;
- `docs/README.md`;
- `drivers/CATALOG.md`, если менялись drivers.

Искать:

- старые acceptance числа;
- "в работе" после done;
- L0-L8 вместо L0-L7;
- `draft/ready` mismatch;
- команды без актуальных flags.

### add-driver

1. Manifest по `drivers/SCHEMA.md`.
2. Engine + unit test.
3. MCP wrapper при необходимости.
4. Sync acceptance.
5. `drivers_catalog.py`.
6. `validate.py`.
7. D-015 second-agent verification перед `ready`.

### knowledge-report

```powershell
python tools\knowledge.py report <corpus> --query <term> --out reports\<name>.md
python tools\knowledge.py search logs\knowledge.db <term>
python tools\top.py repo-search "<term or topic>" --limit 5
python tools\text_extract.py summary <file>
```

Runtime DB не коммитить; Markdown report можно коммитить.

### question-gate

Создать вопрос, если:

- есть архитектурная развилка;
- нужен network/server/GitHub access;
- возможны персональные данные;
- возможно execute;
- требуется `accepted` decision;
- docs противоречат фактам.

## 9. Дальнейший roadmap

### P0 — проще вход

- ~~`tools/onboard.py`~~ — сделано (`tools/onboard.py`);
- обновить quickstart на `pipeline.py`;
- ~~`system-capabilities.json`~~ — сделано через `tools/capabilities.py snapshot`;
- ~~docs drift detector~~ — сделано (`tools/drift_check.py`).

### P1 — реальные read-only данные

- безопасный corpus 50-200 файлов;
- один реальный local repo inventory;
- report diff между запусками;
- source freshness warnings.

### P1 — автоматизация середины

- backlog suggester;
- topic summary generator;
- capability router;
- safety gate.

### P2 — следующий уровень

- sandbox runner design;
- WSL2/Docker preflight после решения человека;
- L5 plugin packaging только после повторного использования;
- vector/RAG только после того, как FTS/report workflow покажет пределы.

## 10. Итоговая позиция

Система уже достаточно самостоятельна, чтобы улучшать себя в пределах workspace-safe/read-only задач. Её не нужно превращать в автономного исполнителя всего подряд.

Сильная линия развития: лучше карта возможностей, меньше ручного выбора, больше автоматических проверок drift/safety, больше реальных read-only источников.

> Принято 2026-06-23 как living operational-карта; команды проверены, roadmap-P0 синхронизирован с уже существующими tools/onboard.py, tools/capabilities.py, tools/drift_check.py.
