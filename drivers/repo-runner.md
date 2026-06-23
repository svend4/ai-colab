---
id: repo-runner
type: driver
title: Repo runner — inventory репозиториев и будущий запуск в песочнице
status: ready
level: L1
mode: read-only
owner: Novax
risk: medium
activation: manual
interfaces: [inspect, summarize, detect-tests, risk-report]
tools: [inspect_repo, repo_summary, repo_risks]
inputs: [repo-path, repo-url]
outputs: [repo-map, test-plan, risk-report, summary]
sandbox: required-before-run-or-test
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md, tasks/T-024.md
---

# Driver: repo-runner

## Назначение

Read-only inventory-драйвер для репозиториев (локальных или GitHub). Не запускает код — только строит карту репозитория, находит тесты, оценивает риски, готовит summary для агента.

Целевой сценарий: репозитории svend4 (или любые другие), которые нельзя безопасно запустить сразу — сначала нужно понять, что внутри.

## Контракт

| Метод | Вход | Выход | Описание |
|---|---|---|---|
| `inspect(repo)` | `repo-path` или `repo-url` | `repo-map` | Структура папок, языки, package-файлы, размер |
| `detect-tests(repo)` | `repo-path` | `test-plan` | Найденные тестовые команды, конфиги, CI/CD |
| `summarize(repo)` | `repo-path` | `summary` | Краткое описание назначения проекта (читаем README, setup.py, Cargo.toml) |
| `risk-report(repo)` | `repo-path` | `risk-report` | Потенциально опасные действия, неизвестные зависимости, shell-скрипты |

## Безопасность

- **L1 (текущий):** только read-only. Запуск `install`, `run`, `test`, shell-команд и сетевых действий — **строго запрещён**.
- **L2 (MCP):** inspect/summarize как инструменты для агента. Всё ещё read-only.
- **L3 (server):** запуск `test/run` только в изолированной песочнице (Docker, отдельный пользователь, limts CPU/памяти/сети, нет секретов).
- **Секреты:** запрещено хранить в репозитории. Если нужны ключи — через env/secret manager, не в коде.

## Реализация

- `drivers/repo-runner/inventory.py` — скрипт inventory (Python 3, no-deps).
- `drivers/repo-runner/test_inventory.py` — тесты (pytest).
- `drivers/repo-runner/fixtures/` — тестовые фикстуры (пример репозитория).

## Путь развития

- L1: read-only inventory (сейчас).
- L2: MCP-инструмент `inspect/summarize` для агента.
- L3: серверный sandbox-runner для ограниченного `test/run`.

## Текущее состояние реализации

На 2026-06-20 уже есть L2-draft код:

- `drivers/repo-runner/inventory.py` — engine `scan_repo`;
- `drivers/repo-runner/mcp_server.py` — FastMCP stdio wrapper;
- `drivers/repo-runner/test_inventory.py` — тесты scanner/hardening.

После `T-050` MCP-wrapper использует allowed-root через `REPO_RUNNER_BASE`, `max_files`, флаг `truncated` и запрет выхода за `base_dir`. Статус манифеста остаётся `ready` как L1/read-only manifest, но L2-runtime требует отдельной приёмки `T-051`.
