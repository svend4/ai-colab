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
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md
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

## Верификация 2026-07-06 — НЕ пройдена (расхождение проходов)

Батч C3a (D-015, отмашка Stefan 2026-07-06). Два независимых прохода **разошлись** (`passed = [false, true]`), поэтому `verified_by` во front-matter НЕ проставлен и advisory-WARN D-015 сохраняется намеренно — это правильный сигнал. Вердикты восстановлены из транскриптов после бага интерполяции в исходном писаре.

Замечания прохода, вернувшего `passed=false` (actionable-долг, файл:строка):

- `drivers/codex-local.md:6` — `level: L1` занижен: по `drivers/SCHEMA.md:57` L1 = «Markdown-манифест, без runtime», но в `drivers/codex-local/` есть рабочий CLI-wrapper (`codex_local.py`) и MCP-сервер (`mcp_server.py`) с 2 зарегистрированными `@mcp.tool()` — это L2. Текст манифеста («На L1 фиксируется только контракт», строка 38) не отражает наличие кода.
- `drivers/codex-local.md:11,32-34` — `interfaces` `[workspace-status, run-checks, summarize-changes]` и секция «Контракт» описывают функции, которых в коде нет; реально реализованы только detect-функции `available()`/`info()` (tools `codex_available`/`codex_info`). SCHEMA.md допускает `interfaces` как концептуальный контракт, но манифест не помечает эти функции как нереализованные/будущие — риск ввести агента в заблуждение.
- `drivers/codex-local/codex_local.py:64-76` — CLI-путь (`main`: available/info) не пишет аудит-записи, хотя манифест декларирует `audit: true` при `risk: medium` (строки 9, 20); правило 5 `docs/driver-safety-policy.md:11` выполняется только на MCP-слое (`mcp_server.py:29,36`). Прямой вызов `python codex_local.py info` не журналируется.
- (repo-wide, не дефект драйвера) `docs/driver-schema-acceptance-checklist.md:41` §3 — `python tools/generate.py --check` FAIL: STALE `STATUS.md`, `board.md`, `TASKS.md`, `DECISIONS.md`, `index.json`; общая устарелость навигации (validate.py WARN D-023), не специфично для codex-local — запись codex-local в `index.json` актуальна и согласована с манифестом.
