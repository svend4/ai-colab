---
id: codex-local
type: driver
title: Codex local driver — мост к локальной рабочей среде
status: ready
level: L2
mode: manual
owner: Codex
risk: medium
activation: manual
interfaces: [codex_available, codex_info, workspace-status, run-checks, summarize-changes]
implemented: [codex_available, codex_info]
planned: [workspace-status, run-checks, summarize-changes]
tools: [codex_available, codex_info]
inputs: [workspace-path, task-id]
outputs: [status, report, patch-summary]
sandbox: current-workspace-policy
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md
---

# Driver: codex-local

## Назначение

Мост к локальной рабочей среде Codex на Windows. Проверка статуса, запуск безопасных проверок, summary изменений — работа в пределах политики workspace.

## Уровень реализации

- **L2:** есть рабочий CLI-wrapper (`codex_local.py`) и MCP-сервер (`mcp_server.py`) с 2 зарегистрированными `@mcp.tool()`.
- Контракт L3/L4 (workspace-status, run-checks, summarize-changes) — в разработке, не реализованы.

## Реализованные инструменты

- `codex_available()` — проверка доступности Codex в среде.
- `codex_info()` — базовая информация о Codex.

## Контракт (полный, включая планируемые)

- `workspace-status(path)` — состояние проекта и изменённых файлов. [planned]
- `run-checks(task-id)` — запуск разрешённых проверок проекта. [planned]
- `summarize-changes()` — краткий отчёт для полилога. [planned]

## Безопасность

Это не автономный запуск Codex и не доступ ко всей ОС. Риск: medium. Аудит: включён. Реальная автоматизация требует отдельной проверки прав, таймаутов и журналирования.

**Примечание по аудиту:** CLI-вызовы (`python codex_local.py available/info`) пишут в лог через `audit.py` на уровне MCP-сервера. Прямой вызов CLI минует аудит — Known Limitation.

## Путь развития

- L1: манифест и правила.
- L2: wrapper/tool для локальных проверок. ✅ реализовано
- L3: интеграция с серверным оркестратором, если появится необходимость.

## Доработка 2026-07-06

По замечаниям верификации D-015:
1. ✅ `level: L1` → `level: L2` (есть код)
2. ✅ Добавлено поле `implemented:` — отмечены реализованные инструменты
3. ✅ Добавлено поле `planned:` — отмечены планируемые
4. ℹ️ CLI audit: Known Limitation, не блокирующее

## Верификация 2026-07-06 — статус

**Первая проверка (C3a):** расхождение проходов → `verified_by` не проставлен, WARN D-015 сохраняется.

**Доработка 2026-07-06:** замечания от `passed=false` учтены:
1. ✅ `level: L1` → `L2` (код есть)
2. ✅ Добавлены поля `implemented:` и `planned:`
3. ✅ Аудит: Known Limitation задокументирована

**Ожидает:** повторная верификация по D-038 для снятия WARN D-015.

**Примечание:** STALE навигации (generate.py) — repo-wide issue, не дефект драйвера.
