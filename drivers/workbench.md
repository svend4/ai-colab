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
verified_by: [claude-w3a (2026-07-06), claude-w3b (2026-07-06)]
last_verified: 2026-07-06
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md, tasks/T-052.md, tasks/T-054.md
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
- CLI ограничивает путь через `WORKBENCH_BASE`; переменная обязательна (fail-closed: без неё код возврата 2).
- Разрешённые расширения БД: `.db`, `.sqlite`, `.sqlite3`.
- `query_documents` и `audit` имеют лимит выдачи.
- `ingest_repo` имеет лимит числа импортируемых документов.
- Секреты в БД не должны храниться без отдельного решения.
- Для стабильной приёмки требуется `T-055`, потому что runtime сейчас заблокирован `T-039`.

## Верификация 2026-07-06

Батч C3a (D-015, отмашка Stefan 2026-07-06). Оба независимых прохода вернули `passed=true`; во front-matter проставлены `verified_by` (две записи) и `last_verified: 2026-07-06`.

**Честная оговорка:** `claude-w3a` и `claude-w3b` — два независимых инстанса **одной модели (Claude)**, не разные модели и не разные люди. Полноценная мультимодельная/межлюдская верификация требует разных моделей или ревьюеров (открытый вопрос к Stefan). Вердикты восстановлены из транскриптов после бага интерполяции в исходном писаре; сами верификаторы отработали штатно.

Замечания к доработке (не блокирующие, из обоих проходов):

- Строка «Для стабильной приёмки требуется `T-055`, потому что runtime сейчас заблокирован `T-039`» устарела: `tasks/T-055.md` и `tasks/T-039.md` давно `status: done` (приёмка пройдена 2026-06-21), runtime работает. Формулировку стоит обновить.
- `drivers/SCHEMA.md:78` требует для `mode: safe-write` dry-run режим **или** отдельное объяснение, почему он невозможен: в `workbench.py` dry-run нет, а в разделе «Безопасность» явного объяснения его отсутствия нет. Правило мягкое (валидатором не проверяется); фактическая замена dry-run — containment allowed-root + лимиты, но по букве схемы объяснение должно быть записано.
- `interfaces` (строка 11) не отражают дополнительные входные точки папки драйвера — `drivers/workbench/ingest.py` (сквозной поток скан→БД) и `drivers/workbench/search.py` (TF-IDF rank), оба с проходящими тестами; манифест — superset. По SCHEMA.md `interfaces` концептуальны (машинно сверяется только `tools`), поэтому не ERROR, но дрейф «манифест уже кода» присутствует.

## Путь развития

- L2: локальный SQLite driver на stdlib.
- L2/MCP: отдельная MCP-обёртка только после runtime-приёмки.
- L3: миграции, FTS5, chunks/entities/topics, но только после базовой проверки.

