---
id: codex-local
type: driver
title: Codex local driver — мост к локальной рабочей среде
status: ready
level: L1
mode: manual
owner: Codex
risk: medium
activation: manual
interfaces: [workspace-status, run-checks, summarize-changes]
tools: [codex_available, codex_info]
inputs: [workspace-path, task-id]
outputs: [status, report, patch-summary]
sandbox: current-workspace-policy
secrets: forbidden-in-repo
source_last_verified: 2026-06-20
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: темы/ai-os-bridge.md
---

# Driver: codex-local

## Назначение

Описать мост к локальной рабочей среде Codex на Windows: проверка статуса, запуск безопасных проверок, summary изменений, работа в пределах политики workspace.

## Контракт

- `workspace-status(path)` — состояние проекта и изменённых файлов.
- `run-checks(task-id)` — запуск разрешённых проверок проекта.
- `summarize-changes()` — краткий отчёт для полилога.

## Безопасность

Это не автономный запуск Codex и не доступ ко всей ОС. На L1 фиксируется только контракт. Реальная автоматизация требует отдельной проверки прав, таймаутов и журналирования.

## Путь развития

- L1: манифест и правила.
- L2: wrapper/tool для локальных проверок.
- L3: интеграция с серверным оркестратором, если появится необходимость.
