---
id: repo-runner
type: driver
title: Repo runner — inventory репозиториев и будущий запуск в песочнице
status: draft
level: L1
mode: read-only
owner: Novax
risk: medium
activation: manual
interfaces: [inspect, summarize, detect-tests, risk-report]
inputs: [repo-path, repo-url]
outputs: [repo-map, test-plan, risk-report, summary]
sandbox: required-before-run-or-test
secrets: forbidden-in-repo
related: темы/ai-os-bridge.md
---

# Driver: repo-runner

## Назначение

Драйвер для сценария Sven4/local repos. На первом этапе он не запускает код: только строит карту репозитория и помогает понять, что можно безопасно тестировать позже.

## Контракт

- `inspect(repo)` — структура, языки, package-файлы, размер.
- `detect-tests(repo)` — найти тестовые команды и конфиги.
- `summarize(repo)` — кратко описать назначение проекта.
- `risk-report(repo)` — отметить потенциально опасные действия и неизвестные зависимости.

## Безопасность

Запуск `install`, `run`, `test`, shell-команд и сетевых действий запрещён на L1. Для этого нужна отдельная песочница: отдельный пользователь/контейнер, лимиты CPU/памяти/сети, отсутствие секретов.

## Путь развития

- L1: read-only inventory.
- L2: MCP-инструмент `inspect/summarize`.
- L3: серверный sandbox-runner для ограниченного `test/run`.
