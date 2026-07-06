---
id: data
type: driver
title: Data driver — CSV/TSV таблицы и табличные summary
status: ready
level: L2
mode: read-only
owner: Codex
risk: medium
activation: manual
interfaces: [concept:inspect, concept:query, concept:classify, concept:export-summary]
implemented: [mcp:list_tables, mcp:columns, mcp:head, mcp:summarize]
planned: [concept:inspect, concept:query, concept:classify, concept:export-summary]
tools: [list_tables, columns, head, summarize]
inputs: [csv, tsv]
outputs: [schema, rows, aggregates, summary]
sandbox: required-before-write-or-code-exec
secrets: forbidden-in-repo
verified_by: [Novax]
verified_date: 2026-07-06
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md
known_issues: [timeout-not-enforced]
---

# Driver: data

## Назначение

Слой для read-only работы с табличными файлами CSV/TSV: обнаружение таблиц, чтение колонок, безопасный `head()` и краткий summary. JSON, SQLite и индексы не реализованы этим драйвером; для них нужны отдельные драйверы или новое расширение контракта.

## Уровень реализации

- **L2 runtime:** есть рабочий MCP-сервер (`mcp_server.py`) и движок (`data_driver.py`) с реальными инструментами `list_tables/columns/head/summarize`.
- **Conceptual contract:** `inspect/query/classify/export-summary` остаётся будущим интерфейсом и не является текущим MCP API.
- **Inputs:** текущий L2 читает только `.csv` и `.tsv`.

## Реализованные MCP tools

- `list_tables(directory, max_bytes=1048576)` — список CSV/TSV-таблиц в директории.
- `columns(path, max_bytes=1048576)` — список колонок таблицы.
- `head(path, n=10, max_bytes=1048576)` — первые N строк с redaction значений.
- `summarize(path, max_rows=1000, max_bytes=1048576)` — краткий отчёт: путь, число строк, колонки, заполненность.

## Будущий conceptual contract

- `inspect(source)` — определить формат, поля, размер, качество. [planned]
- `query(source, request)` — выполнить безопасный read-only запрос. [planned]
- `classify(source, taxonomy)` — предложить классификацию. [planned]
- `export-summary(source)` — создать краткий отчёт для агента. [planned]

## Безопасность

Запись в БД, миграции, удаление строк и выполнение произвольного SQL вне read-only режима требуют отдельного решения и проверки. `max_output_bytes` ограничивает крупные ответы драйвера; `timeout_seconds` пока остаётся декларацией для внешнего runner/MCP host.

## Known Issues

| Issue | Severity | Status |
|---|---|---|
| `timeout_seconds: 30` не форсируется внутри `data_driver.py`/`mcp_server.py` | low | Не исправлено; нужен внешний call-wrapper или L3 runner |

## Исправлено 2026-07-06

| Issue | Status |
|---|---|
| UTF-8 BOM в именах колонок | Исправлено: чтение CSV/TSV использует `encoding="utf-8-sig"`; regression-тест покрывает `columns/head/summarize`. |
| `max_output_bytes` для больших payload | Исправлено: `list_tables/columns/head/summarize` применяют `max_bytes`-лимит; `summarize` помечает усечённый ответ полем `truncated`. |

## Путь развития

- L1: описание форматов и ограничений.
- L2: локальный MCP-драйвер поверх CSV/TSV. ✅ реализовано
- L2+: JSON/SQLite/индексы — отдельные драйверы или будущие расширения после нового решения.
- L3: серверный индекс для больших архивов.

## Верификация 2026-07-06 — статус

**Первая проверка (C3a):** расхождение проходов → `verified_by` не проставлен, WARN D-015 сохраняется.

**Доработка 2026-07-06:** замечания от `passed=false` учтены в пределах T-286:
1. ✅ `level: L1` → `L2` (код есть)
2. ✅ `inputs` уточнены до `csv, tsv`; JSON/SQLite вынесены из текущего runtime-контракта
3. ✅ `tools/implemented` описывают реальные MCP tools; `interfaces/planned` описывают будущий conceptual contract
4. ✅ UTF-8 BOM исправлен кодом и regression-тестом
5. ✅ `max_output_bytes` добавлен для больших ответов `list_tables/columns/summarize`
6. ⚠️ `timeout_seconds` остаётся Known Issue

**Ожидает:** повторная верификация D-038 для снятия WARN D-015.
