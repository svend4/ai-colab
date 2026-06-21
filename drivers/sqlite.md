---
id: sqlite
type: driver
title: SQLite driver — read-only инспекция и запрос SQLite-БД
status: draft
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
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: темы/ai-os-bridge.md, drivers/data.md, drivers/workbench.md
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

`draft` по D-015: код реализован и проверен мной — `drivers/sqlite/test_sqlite.py` зелёный
(tables/schema/head+redaction, SELECT-guard, mode=ro блокирует запись, confinement, суффикс).
Для `ready` нужна сверка вторым агентом (добавить `sqlite` в `mcp_sync_probe.SERVERS` + фикстуру-БД
и прогнать `drivers/mcp_sync_acceptance.py sqlite`).

## Реализация

- `drivers/sqlite/sqlite_driver.py` — engine (mode=ro, confinement, guard, redaction);
- `drivers/sqlite/mcp_server.py` — FastMCP stdio wrapper + audit;
- `drivers/sqlite/test_sqlite.py` — тесты против временной БД.

CLI: `python drivers/sqlite/sqlite_driver.py tables <db>` (tables/schema/head/query).
