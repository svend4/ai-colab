---
id: sqlite
type: driver
title: SQLite driver — read-only инспекция и запрос SQLite-БД
status: ready
level: L2
mode: read-only
owner: Claude
risk: medium
activation: mcp
interfaces: [list_tables, table_schema, table_head, query]
tools: [list_tables, table_schema, table_head, query]
inputs: [db-path, table, sql]
outputs: [table-list, schema, rows]
sandbox: not-required-for-read-only
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
verified_by: [claude-w3a (2026-07-06), claude-w3b (2026-07-06)]
last_verified: 2026-07-06
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md, drivers/data.md, drivers/workbench.md
---

# Driver: sqlite

## Назначение

Read-only доступ к **произвольным SQLite-БД** приложений (`.db`/`.sqlite`/`.sqlite3`) внутри
allowed-root: список таблиц/представлений, схема, первые строки, безопасный SELECT. Дополняет
`data` (CSV/TSV) реальным источником — базами данных приложений.

## Контракт

- Инструменты (4): `list_tables(db)`, `table_schema(db, table)`, `table_head(db, table, n)`,
  `query(db, sql)` — имена сверяются валидатором с `drivers/sqlite/mcp_server.py` (`tools:`).
- Входы: `db-path` (внутри allowed-root `SQLITE_DRIVER_BASE`), `table` (имя), `sql` (один SELECT).
- Выходы: список таблиц, схема (колонки/типы/pk), строки (с redaction секретов).

## Безопасность (несколько уровней)

- **read-only на уровне СУБД**: БД открывается `sqlite3.connect("file:...?mode=ro", uri=True)` —
  любые записи/DDL невозможны (проверено тестом: прямой `CREATE TABLE` → `OperationalError`).
- **SQL-инъекция исключена**: имя таблицы валидируется по реальному списку таблиц перед подстановкой;
  значения — через параметры/whitelist. `query` принимает только одиночный `SELECT`/`WITH`
  (не-SELECT → `QueryNotAllowed`).
- **allowed-root** + whitelist суффиксов (`.db/.sqlite/.sqlite3`); лимит строк (≤1000); `redaction`
  секретов в ячейках; `timeout` соединения; `audit: true` (risk medium).

## Статус

`ready` по D-015:

- первичная реализация и проверка: Claude (`T-116`);
- вторичная приёмка: Codex (`T-117`);
- `python drivers\sqlite\test_sqlite.py` → `TESTS OK`;
- `python drivers\mcp_sync_probe.py sqlite --timeout 60` → 4 tools;
- `python drivers\mcp_sync_acceptance.py sqlite --timeout 90` → `SYNC ACCEPTANCE pass=4 fail=0`.

Acceptance использует временную fixture-БД в `tmp-work/mcp-sync-sqlite/`, не версионирует runtime-файл
и проверяет реальные MCP `tools/call`: `list_tables`, `table_schema`, `table_head`, `query`.

## Верификация 2026-07-06

Батч C3a (D-015, отмашка Stefan 2026-07-06). Оба независимых прохода вернули `passed=true`; во front-matter проставлены `verified_by` (две записи) и `last_verified: 2026-07-06`.

**Честная оговорка:** `claude-w3a` и `claude-w3b` — два независимых инстанса **одной модели (Claude)**, не две разные модели и не два человека. Для настоящей мультимодельной верификации нужны разные модели/ревьюеры (открытый вопрос к Stefan). Вердикты восстановлены из транскриптов после бага интерполяции в исходном писаре; верификаторы отработали штатно.

Замечания к доработке (не блокирующие, из обоих проходов):

- `drivers/sqlite.md:19` — `max_output_bytes=1048576` не форсируется в коде: ограничение только построчное (`MAX_ROWS=1000`, `sqlite_driver.py:35-36`); 1000 строк с крупными TEXT/BLOB-ячейками могут превысить 1 МБ. Пиры (`files`, `data`) форсируют байтовый лимит — рекомендуется выровнять.
- `drivers/sqlite.md:18` — `timeout_seconds=30` не форсируется: в коде только `CONNECT_TIMEOUT=5.0` (busy-timeout соединения), wall-clock лимита на выполнение SELECT нет — патологический рекурсивный CTE может работать неограниченно.
- Формулировка «не-SELECT → `QueryNotAllowed`» (строки 44-45) неточна: WITH-префиксный write (`WITH ... DELETE/INSERT`) проходит regex-guard (`sqlite_driver.py:133`) и блокируется уровнем ниже — `mode=ro` → `OperationalError`, а не `QueryNotAllowed`. Защита в глубину работает (запись невозможна, БД не изменяется), ошибка лишь в типе исключения из описания; можно ужесточить guard (запрет DML-ключевых слов после WITH).
- Минор: BLOB-ячейки (`bytes`) обходят redaction (`_redact_row` маскирует только `str`, `sqlite_driver.py:119`); краевой случай, явных заявлений манифеста не нарушает.

## Реализация

- `drivers/sqlite/sqlite_driver.py` — engine (mode=ro, confinement, guard, redaction);
- `drivers/sqlite/mcp_server.py` — FastMCP stdio wrapper + audit;
- `drivers/sqlite/test_sqlite.py` — тесты против временной БД.

CLI: `python drivers/sqlite/sqlite_driver.py tables <db>` (tables/schema/head/query).
