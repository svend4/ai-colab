---
id: workbench
type: driver
title: Workbench DB driver — SQLite-память корпуса и audit log
status: ready
level: L2
mode: safe-write
owner: Codex
risk: medium
activation: manual
interfaces: [init, add_document, query_documents, log, audit, ingest_repo]
inputs: [db-path, document-record, repo-scan-report]
outputs: [sqlite-db, document-list, audit-list]
sandbox: workspace-write-only
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: темы/ai-os-bridge.md, tasks/T-052.md, tasks/T-054.md
---

# Driver: workbench

## Назначение

Локальная SQLite-память для корпуса: таблица `documents` хранит обработанные файлы/репозитории, `audit_log` хранит события агентов и драйверов. Это L6 memory layer для повторяемого поиска, отчётности и анализа больших объёмов информации.

## Контракт

- `init(db_path)` — создать или открыть SQLite DB и применить схему.
- `add_document(...)` — upsert записи документа.
- `query_documents(...)` — поиск по `type`, `risk`, тексту пути/summary.
- `log(...)` — запись audit-события.
- `audit(...)` — чтение audit-событий.
- `ingest_repo(scan_report)` — импорт структуры из `repo-runner` отчёта.

## Безопасность

- Режим: `safe-write`, потому что драйвер создаёт/изменяет `.db`.
- CLI ограничивает путь через `WORKBENCH_BASE` или текущую рабочую папку.
- Разрешённые расширения БД: `.db`, `.sqlite`, `.sqlite3`.
- `query_documents` и `audit` имеют лимит выдачи.
- `ingest_repo` имеет лимит числа импортируемых документов.
- Секреты в БД не должны храниться без отдельного решения.
- Для стабильной приёмки требуется `T-055`, потому что runtime сейчас заблокирован `T-039`.

## Путь развития

- L2: локальный SQLite driver на stdlib.
- L2/MCP: отдельная MCP-обёртка только после runtime-приёмки.
- L3: миграции, FTS5, chunks/entities/topics, но только после базовой проверки.

