---
id: data
type: driver
title: Data driver — таблицы, JSON, SQLite и индексы
status: ready
level: L1
mode: read-only
owner: Codex
risk: medium
activation: manual
interfaces: [inspect, query, classify, export-summary]
tools: [list_tables, columns, head, summarize]
inputs: [csv, json, sqlite, index-json]
outputs: [schema, rows, aggregates, summary]
sandbox: required-before-write-or-code-exec
secrets: forbidden-in-repo
source_last_verified: 2026-06-20
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: темы/ai-os-bridge.md
---

# Driver: data

## Назначение

Слой для больших объёмов структурированной информации: таблицы, JSON, SQLite, будущие embedding-индексы. На первом этапе драйвер только читает и строит summary/schema.

## Контракт

- `inspect(source)` — определить формат, поля, размер, качество.
- `query(source, request)` — выполнить безопасный read-only запрос.
- `classify(source, taxonomy)` — предложить классификацию.
- `export-summary(source)` — создать краткий отчёт для агента.

## Безопасность

Запись в БД, миграции, удаление строк и выполнение произвольного SQL вне read-only режима требуют отдельного решения и проверки.

## Путь развития

- L1: описание форматов и ограничений.
- L2: локальный MCP-драйвер поверх SQLite/CSV/JSON.
- L3: серверный индекс для больших архивов.
