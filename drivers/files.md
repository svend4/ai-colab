---
id: files
type: driver
title: Files driver — безопасное чтение и инвентаризация файлов
status: ready
level: L1
mode: read-only
owner: Codex
risk: low
activation: manual
interfaces: [list, read, search, summarize]
inputs: [path, pattern]
outputs: [file-list, snippets, summary]
sandbox: not-required-for-read-only
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: false
related: темы/ai-os-bridge.md
---

# Driver: files

## Назначение

Дать агентам стандартный способ описывать работу с файлами: список, чтение, поиск, краткое резюме. Это базовый кандидат для первого L2 PoC, потому что режим read-only безопаснее запуска кода.

## Контракт

- `list(path)` — показать дерево или список файлов.
- `read(path)` — прочитать файл в пределах разрешённой зоны.
- `search(pattern, path)` — найти текст.
- `summarize(path)` — кратко описать набор файлов.

## Безопасность

Первый режим только read-only. Запись, переименование и удаление не входят в этот драйвер без отдельного решения.

## Путь развития

- L1: markdown-манифест.
- L2: локальный MCP/stdout-инструмент read-only.
- L3: не требуется, если хватает локального режима.

## Текущее состояние реализации

На 2026-06-20 уже есть L2-draft код:

- `drivers/files/files_driver.py` — engine `list/read/search/summarize`;
- `drivers/files/inventory.py` — подробная инвентаризация файлов;
- `drivers/files/mcp_server.py` — FastMCP stdio wrapper;
- `drivers/files/test_files.py` и `drivers/files/test_inventory.py` — тесты.

После `T-047` MCP-wrapper использует allowed-root через `FILES_DRIVER_BASE`, лимиты `max_files/max_hits`, redaction и пропуск шумных директорий. Статус манифеста остаётся `draft`, потому что Codex не смог повторно прогнать тесты из-за runtime-блокера `T-039`; приёмка вынесена в `T-048`.
