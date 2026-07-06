# Верификация драйверов D-015 — сводный отчёт (батч C3a)

- Дата: 2026-07-06
- Автор: Claude (писарь верификации, батч C3a)
- Провенанс: отмашка Stefan 2026-07-06 (C3a); решение D-015 «status: ready требует перепроверки ≥2 агентами»
- Источник вердиктов: `tmp-work/audit-fix-checkpoint-20260702/driver-verdicts-recovered.json`

## Контекст

По D-015 каждый драйвер в `status: ready` должен иметь машинный след многоагентной
перепроверки — front-matter `verified_by` с ≥2 записями. `tools/validate.py` при отсутствии
поля или <2 агентов даёт advisory-WARN (обкатка по решению Stefan Q-W2-18b; перевод в ERROR —
отдельное будущее решение человека).

Для восьми ready-драйверов верификаторы отработали два независимых прохода на драйвер. Однако
исходный писарь из-за **бага интерполяции** не записал вердикты в манифесты — записи были
потеряны. Вердикты **восстановлены из транскриптов** верификаторов и сведены в
`driver-verdicts-recovered.json` (формат: `passes: [bool, bool]`, `both_pass`, `issues` по каждому
проходу). Сами верификаторы отработали штатно; проблема была только на слое записи.

Настоящий батч C3a — фиксация восстановленных вердиктов: для драйверов, где оба прохода прошли,
проставлен `verified_by`; для расходящихся — потерянные вердикты превращены в actionable-долг
в теле манифеста (без `verified_by`, чтобы WARN D-015 честно остался).

## Итоговая таблица

| Драйвер | Проход A | Проход B | Итог |
|---|---|---|---|
| `gateway` | pass | pass | **verified** (verified_by проставлен) |
| `git-log` | pass | pass | **verified** (verified_by проставлен) |
| `sqlite` | pass | pass | **verified** (verified_by проставлен) |
| `workbench` | pass | pass | **verified** (verified_by проставлен) |
| `codex-local` | fail | pass | **НЕ verified** (расхождение) |
| `data` | pass | fail | **НЕ verified** (расхождение) |
| `files` | pass | fail | **НЕ verified** (расхождение) |
| `repo-runner` | fail | pass | **НЕ verified** (расхождение) |

Раскладка: **4 verified** (оба прохода pass) / **4 НЕ verified** (проходы разошлись).

## Что изменено в манифестах

**4 verified драйвера** (`gateway`, `git-log`, `sqlite`, `workbench`):

- Front-matter: добавлены `verified_by: [claude-w3a (2026-07-06), claude-w3b (2026-07-06)]`
  и `last_verified: 2026-07-06`.
- Тело: секция «## Верификация 2026-07-06» с честной оговоркой (оба прохода — инстансы одной
  модели, не разные модели/люди) и перечнем не-блокирующих замечаний к доработке из проходов.

**4 НЕ verified драйвера** (`codex-local`, `data`, `files`, `repo-runner`):

- `verified_by` НЕ добавлен — advisory-WARN D-015 у них **должен остаться** и остался (правильно).
- Тело: секция «## Верификация 2026-07-06 — НЕ пройдена (расхождение проходов)» с перечнем
  замечаний от прохода, вернувшего `passed=false` (с координатами файл:строка) — потерянный
  вердикт превращён в actionable-долг.
- Статусы драйверов (`ready`) НЕ менялись — это решение человека.

## Замечания по НЕ-verified драйверам (проход с passed=false)

### codex-local (проход A = false)

- `level: L1` занижен: в `drivers/codex-local/` есть рабочий CLI-wrapper и MCP-сервер с 2
  `@mcp.tool()` — фактически L2 (`drivers/codex-local.md:6`).
- `interfaces` `[workspace-status, run-checks, summarize-changes]` и секция «Контракт» описывают
  нереализованные функции; реально есть только `codex_available`/`codex_info`
  (`drivers/codex-local.md:11,32-34`).
- CLI-путь `python codex_local.py info` не пишет аудит при `audit: true`/`risk: medium`; аудит
  только на MCP-слое (`drivers/codex-local/codex_local.py:64-76`).
- (repo-wide, не дефект драйвера) `generate.py --check` FAIL — STALE навигация.

### data (проход B = false)

- `inputs: [csv, json, sqlite, index-json]` завышены: код поддерживает только `.csv/.tsv`;
  `json/sqlite/index-json` не реализованы, `tsv` не заявлен (`drivers/data.md:13`).
- `level: L1` занижен — есть L2-реализация (`data_driver.py`, `mcp_server.py`) (`drivers/data.md:6`).
- Секция «Контракт» (`inspect/query/classify/export-summary`) не реализована под этими именами;
  фактические инструменты — `list_tables/columns/head/summarize` (`drivers/data.md:32-35`).
- `timeout_seconds: 30` не форсируется (`drivers/data.md:18`).
- UTF-8 BOM просачивается в имя первой колонки — `open(encoding="utf-8")` вместо `utf-8-sig`
  (`drivers/data/data_driver.py:77,86,107`).
- `max_output_bytes` форсируется только в `head()`; `columns/list_tables/summarize` без лимита.
- Политика per-agent-журнала vs общий `logs/driver-audit.jsonl` (`docs/driver-safety-policy.md:11`).
- (repo-wide, не дефект драйвера) `generate.py --check` exit 1 — STALE навигация.

### files (проход B = false)

- (repo-wide, не дефект драйвера) `generate.py --check` exit 1 — STALE навигация; лечится
  `python tools/generate.py` (`docs/driver-schema-acceptance-checklist.md:42`).
- MCP `read_file` принимает клиентский `max_bytes` без клампа к `max_output_bytes=1048576`;
  аналогично `max_files/max_hits` (advisory, `drivers/files/mcp_server.py:41-43`).
- `timeout_seconds: 30` не форсируется в L2-коде (advisory, `drivers/files.md:18`).

### repo-runner (проход A = false)

- `drivers/repo-runner/fixtures/` заявлен в манифесте, но каталога нет и он никогда не
  коммитился; тесты используют temp-каталоги — единственное жёсткое расхождение
  (`drivers/repo-runner.md:52`).
- Примечание «L2-runtime требует приёмки `T-051`» устарело — `T-051` `done`; манифест держит
  `level: L1`/`activation: manual` при живом принятом L2-runtime (`drivers/repo-runner.md:68`).
- `timeout_seconds`/`max_output_bytes` не форсируются в `mcp_server.py` (`drivers/repo-runner.md:18-19`).
- (repo-wide, не дефект драйвера) `generate.py --check` exit 1 — STALE навигация.
- Минор: pytest не установлен в venv; тесты проходят standalone-запуском (`drivers/repo-runner.md:51`).

## Важная оговорка: «2 инстанса Claude ≠ 2 разные модели»

Оба прохода на каждом драйвере (`claude-w3a`, `claude-w3b`) — это **два независимых инстанса
одной и той же модели (Claude)**, а не две разные модели и не два человека. Совпадение вердиктов
у 4 verified-драйверов повышает уверенность, но **не эквивалентно** мультимодельной или
межлюдской верификации: два инстанса одной модели разделяют одни и те же слепые зоны и
систематические ошибки. Для настоящей многоагентной перепроверки в духе D-015 нужны **разные
модели или разные ревьюеры-люди** — это отдельный открытый вопрос к Stefan (текущая реализация
D-015 засчитывает «≥2 агентов» без требования их разнородности).

## Рекомендации

1. **4 verified драйвера** (`gateway`, `git-log`, `sqlite`, `workbench`) — WARN D-015 снят
   (`verified_by` содержит 2 агента). Замечания в их секциях «Верификация» — не блокирующие,
   к плановой доработке.
2. **4 расходящихся драйвера** (`codex-local`, `data`, `files`, `repo-runner`) — WARN D-015
   сохранён намеренно; замечания прохода с `passed=false` зафиксированы в манифестах как
   actionable-долг. Предлагается **завести задачи** на их устранение (по одной на драйвер или
   сгруппировать однотипные: `level`-дрейф L1→L2, не-форсируемые `timeout/max_output_bytes`,
   расхождение `interfaces`/«Контракт» с кодом, missing `fixtures/` у repo-runner). Задачи
   **не заведены** — жду отмашки Stefan.
3. **Открытый вопрос про разнородность агентов** (см. оговорку выше) — вынести на решение Stefan
   отдельно: считать ли «2 инстанса Claude» достаточными для D-015 или требовать разные модели.

## Осталось нерешённым

- Задачи на 4 расходящихся драйвера не заведены (по правилам — без отмашки не завожу).
- Вопрос разнородности верификаторов (одна модель vs разные) — на решение Stefan.
- Repo-wide staleness навигации (`generate.py --check`) фигурирует в вердиктах как контекст, но
  это не дефект драйверов и вне scope данного батча (лечится регенерацией индексов владельцем).
