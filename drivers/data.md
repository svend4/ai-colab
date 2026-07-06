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
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md
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

## Верификация 2026-07-06 — НЕ пройдена (расхождение проходов)

Батч C3a (D-015, отмашка Stefan 2026-07-06). Два независимых прохода **разошлись** (`passed = [true, false]`), поэтому `verified_by` во front-matter НЕ проставлен и advisory-WARN D-015 сохраняется намеренно. Вердикты восстановлены из транскриптов после бага интерполяции в исходном писаре.

Замечания прохода, вернувшего `passed=false` (actionable-долг, файл:строка):

- `drivers/data.md:13` — `inputs: [csv, json, sqlite, index-json]` завышены: код поддерживает только `.csv/.tsv` (`drivers/data/data_driver.py:31` `TABLE_EXT = {".csv", ".tsv"}`); `json/sqlite/index-json` в этом драйвере не реализованы (sqlite — отдельный драйвер), а поддержанный `tsv` в `inputs` не заявлен.
- `drivers/data.md:6` — `level: L1` занижен: фактически существует L2-реализация (`data_driver.py:4` докстринг «data driver (L2, read-only)»; `mcp_server.py` — FastMCP-сервер); тело манифеста (строки 43-45) называет L2 «путём развития», хотя L2 уже написан и проходит приёмку.
- `drivers/data.md:32-35` — секция «Контракт» (`inspect/query/classify/export-summary`) не реализована под этими именами; фактические инструменты — `list_tables/columns/head/summarize` (`mcp_server.py:25-50`); поле `tools` с кодом сходится, но контрактный текст и `interfaces` (строка 11) дрейфуют.
- `drivers/data.md:18` — `timeout_seconds: 30` нигде не форсируется (ни в `data_driver.py`, ни в `mcp_server.py` нет механизма таймаута), хотя драйвер уже L2/MCP.
- `drivers/data/data_driver.py:77,86,107` — `open(..., encoding="utf-8")` вместо `utf-8-sig`: UTF-8 BOM просачивается в имя первой колонки (воспроизведено smoke: колонка «﻿name»); типовой случай для Windows/Excel CSV, ломает адресацию колонок по имени.
- `drivers/data/data_driver.py:81-99` — `max_output_bytes` форсируется только в `head()`; `columns()/list_tables()/summarize()` байтового лимита не имеют (низкая серьёзность).
- `docs/driver-safety-policy.md:11` vs `drivers/audit.py:23,30-31` — политика требует журнал «per-agent/per-task, не в общий горячий файл», а `audit.py` пишет все драйверы в один общий `logs/driver-audit.jsonl` (осознанное решение ревью T-078/E, но текст политики не обновлён) — низкая серьёзность.
- (repo-wide, не дефект драйвера) `tools/generate.py --check` — exit 1, STALE `STATUS.md/board.md/TASKS.md/QUESTIONS.md/DECISIONS.md/index.json`; §3 чек-листа не выполнен на момент проверки, но состояние repo-wide, не специфично для драйвера data.
