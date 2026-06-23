---
id: agent-launch-workflow
title: Agent launch workflow — handoff между repo-flow и внешним sub-agent launcher
status: draft
owner: codex
related: docs/workflow-orchestration-policy.md, docs/top-layer-command-groups.md, docs/parallel-work-policy.md, tools/top.py, tools/flow.py, T-161
---

# Agent launch workflow

Дата: 2026-06-23.

Назначение: сделать запуск нескольких AI-агентов рабочим процессом, а не устной договорённостью. Документ описывает, как верхний агент/человек готовит задачу, как внешний launcher запускает worker-agent, какие команды выполняет worker и как результат возвращается в общий репозиторий.

## Короткий ответ

Да, в текущей среде Codex может запускать sub-agent через платформенный механизм. Но локальные файлы проекта не должны напрямую зависеть от конкретного API запуска. Поэтому граница такая:

| Слой | Что делает | Чего не делает |
|---|---|---|
| `tools/top.py subagent-handoff` | одна верхняя команда для человека/агента; печатает launch-пакет | не создаёт поток/агента сам |
| `tools/flow.py launch-plan` | готовит repo lane, prompt, start/finish-команды | не вызывает внешний platform spawn |
| внешний launcher Codex/оркестратора | реально запускает worker-agent с prompt | не решает repo policy сам |
| worker-agent | claim, scoped edits, tests, report, done | не переписывает чужую работу и не принимает спорные решения |
| integrator/lead | проверяет, сливает, коммитит, решает конфликты | не скрывает расхождения без записи в docs/decisions |

Это даёт переносимость: тот же handoff можно использовать для Codex sub-agent, другого AI, человека или будущего сервера-оркестратора.

## Быстрый сценарий

```powershell
python tools\top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree
```

Команда печатает:

1. repo lane: Level 0 branch или Level 1 worktree;
2. команду подготовки lane: `python tools/flow.py start ...`;
3. готовый prompt для внешнего sub-agent launcher;
4. команду завершения lane: `python tools/flow.py finish ...`.

Для реальной параллельной работы чаще выбирайте `--worktree`, потому что несколько агентов могут трогать hot files, generated indexes и общие документы.

## Пошаговый workflow

1. Человек или lead-agent выбирает задачу из котла: `python tools/pipeline.py status` или `python tools/cohort.py board`.
2. Если нужно несколько исполнителей, lead-agent строит план: `python tools/cohort.py plan 4 --json`.
3. Для каждого worker создаётся handoff:

```powershell
python tools\top.py subagent-handoff <agent> <T-id> "<topic/context>" --worktree
```

4. Внешний launcher запускает worker-agent с prompt из handoff-блока.
5. Worker начинает с контекста:

```powershell
python tools\top.py agent-start <agent> --context "<topic/context>"
python tools\pipeline.py claim <agent> <T-id>
```

6. Worker делает только scoped edits, запускает focused tests и `python tools\top.py health`.
7. Worker закрывает задачу через `pipeline.py done ... --claim <claim_id> --applied "AGENTS.md, PROTOCOL.md, docs/agent-launch-workflow.md, Checks"`.
8. Integrator проверяет результат, при worktree-режиме запускает merge gate/finish и делает selective commit.

## Правила для worker-agent

- Один worker берёт одну задачу или один явно выделенный sub-scope.
- Перед правкой он читает `AGENTS.md`, `PROTOCOL.md`, `docs/agent-launch-workflow.md`, релевантные decisions и task-файл.
- Он не удаляет и не переписывает чужие сообщения, half-done файлы и чужие claims.
- Если нашёл расхождение, создаёт вопрос/задачу/вариант, а не молча затирает другой вариант.
- В финале сообщает changed files, tests, blockers и применённые инструкции.

## Когда использовать Level 0 и Level 1

| Режим | Когда | Команда |
|---|---|---|
| Level 0 shared tree | маленькая одиночная docs/task правка без чужих изменений | `python tools/top.py subagent-handoff codex T-161 "context"` |
| Level 1 worktree | параллельная работа, hot files, generated indexes, чужие half-done изменения | `python tools/top.py subagent-handoff mavis T-161 "context" --worktree` |

Если сомневаетесь, сначала спросите верхний слой:

```powershell
python tools\top.py work-mode <agent> <T-id> --parallel --hot-files
```

## Почему не запускать агента прямо из `flow.py`

`flow.py` — репозиторный инструмент. Его задача — быть переносимым и воспроизводимым на обычной Windows/Python/Git установке. Если встроить в него конкретный platform spawn API, появятся проблемы:

- локальный проект станет зависеть от одного клиента и одной версии API;
- тесты начнут требовать сетевой/платформенный доступ;
- люди без этого launcher не смогут повторить процесс;
- сложнее разграничить безопасность: repo-gate и platform-gate смешаются.

Поэтому правильная архитектура сейчас: `flow.py` печатает launch-plan, а внешний оркестратор выполняет запуск.

## Минимальный контракт handoff

Каждый handoff должен содержать:

| Поле | Зачем |
|---|---|
| `agent` | кто работает |
| `task` | какой `T-id` или sub-scope |
| `context` | поисковый контекст для `agent-start` |
| `repo lane` | shared/worktree режим |
| `start command` | как подготовить ветку/worktree |
| `worker prompt` | что сказать sub-agent |
| `finish command` | как вернуть результат |
| `checks` | какие тесты/health обязательны |
| `report` | что worker обязан вернуть |

## Дальнейшее развитие

## JSON-режим для оркестратора

После T-162 launch-пакет доступен не только как Markdown, но и как чистый JSON:

```powershell
python tools\flow.py launch-plan mavis T-161 "context" --worktree --json
python tools\top.py subagent-handoff mavis T-161 "context" --worktree --json
```

JSON содержит `schema: subagent_launch_plan.v1`, `agent`, `task`, `context`, `repo_lane`, `commands.prepare`, `commands.finish`, `worker_prompt`, `policies` и `checks`. Это формат для GUI-кнопки, ChatGPT App, MCP tool или серверного scheduler. Markdown-output остаётся дефолтом для человека.