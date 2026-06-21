---
id: gateway
type: driver
title: Gateway — единый MCP над files/repo/workbench (композиция)
status: ready
level: L2
mode: read-only
owner: Claude
risk: medium
activation: mcp
interfaces: [files_list, files_read, files_search, files_summarize, repo_inspect, memory_query]
tools: [files_list, files_read, files_search, files_summarize, repo_inspect, memory_query]
inputs: [path, repo-path, query]
outputs: [listing, content, search-hits, repo-summary, memory-hits]
sandbox: not-required-for-read-only
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: темы/ai-os-bridge.md, decisions/D-013.md, drivers/files.md, drivers/repo-runner.md, drivers/workbench.md
---

# Driver: gateway (ai-os-bridge)

## Назначение

`gateway` — это не leaf-драйвер, а **композиция**: один MCP-сервер (`drivers/gateway/mcp_server.py`, имя сервера `ai-os-bridge`), который сводит три уже существующих драйвера за единым разъёмом для AI-агента:

- `files` — безопасное чтение и инвентаризация файлов;
- `repo-runner` — read-only inventory репозиториев;
- `workbench` — SQLite-память корпуса (только запрос).

Цель — дать агенту одну точку входа в «средний слой» (файлы + репозитории + память), не подключая три отдельных сервера. Композиция собирается через явную загрузку модулей по пути (`_load`), чтобы не было конфликта имён (в репозитории два разных `inventory.py`).

## Контракт

- Инструменты (tools/list = 6, подтверждено handshake 2026-06-20 и sync-probe 2026-06-21):
  - `files_list`, `files_read`, `files_search`, `files_summarize` — поверх `files_driver`;
  - `repo_inspect` — поверх `repo-runner/inventory`;
  - `memory_query` — read-only запрос к `workbench.db`.
- Входы: `path` (для files), `repo-path` (для repo_inspect), `query` (для search/memory_query); `Optional[str]` параметры типизированы.
- Выходы: листинг файлов, содержимое (с redaction), search-hits, repo-summary, memory-hits.
- Ошибки: `PathAccessError` при выходе за allowed-root; пустой результат при отсутствии совпадений.

## Безопасность

- Режим по умолчанию: **read-only** — gateway не пишет ни в файлы, ни в БД (`memory_query` только читает).
- Песочница: не требуется для read-only композиции.
- Allowed-root: `GATEWAY_BASE` (env) ограничивает зону так же, как `FILES_DRIVER_BASE` / `REPO_RUNNER_BASE` / `WORKBENCH_BASE` у leaf-драйверов. Policy должна протекать сверху вниз: gateway обязан пробрасывать `base_dir`/лимиты в каждый вложенный драйвер, а не обходить их.
- Секреты: запрещены в репозитории; чтение файлов идёт через redaction нижнего `files`-драйвера.
- Audit: `true` (risk: medium) — вызовы композиции журналировать через общий `drivers/audit.py`.
- Timeout / max output: 30 c / 1 МБ (наследуются как контракт будущего L2/L3 вызова).
- Источник последний раз проверен: 2026-06-21 (`tools=6`, `RESULT OK`; прямой audit smoke-test: `gateway files_summarize .`).
- Действия, требующие человека: перевод `status: draft → ready` (после полного прогона приёмочных наборов, а не только handshake); любое расширение за пределы read-only.

## Статус на 2026-06-21

Предложение Codex по T-088: оставить front-matter `status: ready`, потому что статический контракт gateway согласован с кодом (`tools:` сверяются валидатором), режим остаётся read-only, а audit wiring проверен прямым вызовом. При этом operational-оговорка остаётся обязательной: gateway **не считается прошедшим полную `call_tool` MCP acceptance** в официальном async stdio-клиенте Windows, пока не закрыт отдельный runtime-блокер или не добавлена синхронная `tools/call` приёмка.

Короткая формула для других агентов: `ready` как манифест и tools-list контракт; `ready-except-mcp-stdio-call-acceptance` как runtime-статус.

Дополнительная регрессия T-093: `drivers/gateway/test_gateway.py` проверяет gateway in-process без MCP stdio: composition, redaction, allowed-root confinement и audit. Это усиливает доверие к логике gateway, но не заменяет официальную MCP `call_tool` acceptance.

## Путь развития

- L1: манифест зафиксирован (этот файл), внесён в каталог как композиция.
- L2/MCP: `drivers/gateway/mcp_server.py` поднимается по stdio, handshake/tools-list пройден. Дальше — приёмочные тесты вызовов (`tools/call` по каждому инструменту), не только `initialize`/`tools/list`.
- L3/server: при выносе на сервер — отдельное решение; добавляются сетевые риски и, возможно, `execute`-режим у вложенных драйверов (тогда меняется risk-класс и нужен sandbox).

## Примечание по классификации

В схеме драйверов v1 (D-013) поле `level` допускает только `L1/L2/L3`, поэтому композиция оформлена как **L2** (локальный MCP). Концептуальный «оркестрационный» уровень (L7 в `docs/agent-layer-design.md`) — это про роль узла, а не про значение поля `level`. Чтобы не путать gateway с leaf-драйверами L2, его природа («композиция») зафиксирована в заголовке и в этом разделе.
