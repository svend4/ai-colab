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
tools: [list_files, read_file, search, summarize]
inputs: [path, pattern]
outputs: [file-list, snippets, summary]
sandbox: not-required-for-read-only
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: false
related: topics/ai-os-bridge.md
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

На 2026-06-21 есть рабочий read-only L2-код:

- `drivers/files/files_driver.py` — engine `list/read/search/summarize`;
- `drivers/files/inventory.py` — подробная инвентаризация файлов;
- `drivers/files/mcp_server.py` — FastMCP stdio wrapper;
- `drivers/files/test_files.py` и `drivers/files/test_inventory.py` — тесты.

После `T-089` `files_driver.py` использует общий `drivers/redaction.py`, а manifest содержит `tools:` для статической сверки с `drivers/files/mcp_server.py`. Unit tests зелёные. `T-048` остаётся отдельной MCP acceptance-задачей не из-за логики files driver, а из-за известного Windows/asyncio stdio runtime blocker.

## Верификация 2026-07-06 — НЕ пройдена (расхождение проходов)

Батч C3a (D-015, отмашка Stefan 2026-07-06). Два независимых прохода **разошлись** (`passed = [true, false]`), поэтому `verified_by` во front-matter НЕ проставлен и advisory-WARN D-015 сохраняется намеренно. Вердикты восстановлены из транскриптов после бага интерполяции в исходном писаре.

Замечания прохода, вернувшего `passed=false` (actionable-долг, файл:строка):

- (repo-wide, не дефект драйвера) `docs/driver-schema-acceptance-checklist.md:42` — пункт «`generate.py --check` не показывает устаревшие индексы» НЕ выполняется: `tools/generate.py --check` завершается exit 1, STALE `STATUS.md, board.md, TASKS.md, DECISIONS.md, index.json`. Устарела репозиторная навигация после недавних коммитов, не логика files; лечится запуском `python tools/generate.py`.
- `drivers/files/mcp_server.py:41-43` (ADVISORY) — MCP-инструмент `read_file` принимает `max_bytes` от клиента без верхнего клампа к манифестному `max_output_bytes=1048576` (`drivers/files.md:19`): клиент может передать `max_bytes` сколь угодно большим, и `files_driver.read_file` (`files_driver.py:116-126`) прочитает столько в память. Дефолт `1_000_000` ниже лимита (безопасное направление), нарушение только в отсутствии принудительной отсечки. Аналогично `max_files/max_hits`. Низкая серьёзность: локальный доверенный клиент, read-only.
- `drivers/files.md:18` (ADVISORY) — `timeout_seconds: 30` нигде не форсируется в L2-коде (`files_driver.py`, `mcp_server.py`). По `drivers/SCHEMA.md:35` поле декларируется «для будущего L2/L3 вызова», так что для текущего уровня допустимо; наблюдение зафиксировано, чтобы при L2-acceptance (T-048) лимит был реализован на стороне вызова.

## Hardening 2026-07-06 — T-287

Codex addressed the concrete `files` finding from the 2026-07-06 D-015 verification notes:

- `drivers/files/mcp_server.py` now clamps MCP client-supplied `max_bytes`, `max_files`, and `max_hits` to the engine/manifest limits before calling the read-only engine.
- `python drivers\files\test_files.py` passes.
- `python -m py_compile drivers\files\mcp_server.py` passes.

`verified_by` is intentionally still absent. D-015/D-038 require a follow-up multi-agent reverification; this change only removes the low-risk limit-clamping finding. The `timeout_seconds` observation remains advisory and belongs to a broader call-wrapper/runner timeout policy, not to this narrow `files` engine patch.