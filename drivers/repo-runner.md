---
id: repo-runner
type: driver
title: Repo runner — inventory репозиториев и будущий запуск в песочнице
status: ready
level: L2
mode: read-only
owner: Novax
risk: medium
activation: manual
interfaces: [inspect, summarize, detect-tests, risk-report]
tools: [inspect_repo, repo_summary, repo_risks]
inputs: [repo-path, repo-url]
outputs: [repo-map, test-plan, risk-report, summary]
sandbox: required-before-run-or-test
secrets: forbidden-in-repo
verified_by: [Novax]
verified_date: 2026-07-06
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md, tasks/T-024.md
---

# Driver: repo-runner

## Назначение

Read-only inventory-драйвер для репозиториев (локальных или GitHub). Не запускает код — только строит карту репозитория, находит тесты, оценивает риски, готовит summary для агента.

Целевой сценарий: репозитории svend4 (или любые другие), которые нельзя безопасно запустить сразу — сначала нужно понять, что внутри.

## Контракт

| Метод | Вход | Выход | Описание |
|---|---|---|---|
| `inspect(repo)` | `repo-path` или `repo-url` | `repo-map` | Структура папок, языки, package-файлы, размер |
| `detect-tests(repo)` | `repo-path` | `test-plan` | Найденные тестовые команды, конфиги, CI/CD |
| `summarize(repo)` | `repo-path` | `summary` | Краткое описание назначения проекта (читаем README, setup.py, Cargo.toml) |
| `risk-report(repo)` | `repo-path` | `risk-report` | Потенциально опасные действия, неизвестные зависимости, shell-скрипты |

## Безопасность

- **L1/L2 (текущий):** read-only inventory + MCP wrapper. Запуск `install`, `run`, `test`, shell-команд и сетевых действий — **строго запрещён**.
- **L2 (MCP):** `inspect_repo`, `repo_summary`, `repo_risks` как инструменты для агента. Всё ещё read-only.
- **L3 (server):** запуск `test/run` только в изолированной песочнице (Docker, отдельный пользователь, limts CPU/памяти/сети, нет секретов).
- **Секреты:** запрещено хранить в репозитории. Если нужны ключи — через env/secret manager, не в коде.

## Реализация

- `drivers/repo-runner/inventory.py` — скрипт inventory (Python 3, no-deps).
- `drivers/repo-runner/test_inventory.py` — standalone/pytest-compatible тесты.
- Тестовые фикстуры создаются во временном каталоге через `drivers/test_tmp.py`; постоянного `drivers/repo-runner/fixtures/` в репозитории нет.

## Путь развития

- L1: read-only inventory manifest (done).
- L2: MCP-инструменты `inspect_repo` / `repo_summary` / `repo_risks` для агента (accepted by T-051).
- L3: серверный sandbox-runner для ограниченного `test/run`.

## Текущее состояние реализации

На 2026-06-20 уже есть L2-draft код:

- `drivers/repo-runner/inventory.py` — engine `scan_repo`;
- `drivers/repo-runner/mcp_server.py` — FastMCP stdio wrapper;
- `drivers/repo-runner/test_inventory.py` — тесты scanner/hardening.

После `T-050` MCP-wrapper использует allowed-root через `REPO_RUNNER_BASE`, `max_files`, флаг `truncated` и запрет выхода за `base_dir`. L2-runtime acceptance закрыта в `T-051`; execute/test/run по-прежнему вне scope и требует отдельной L3-песочницы.

## Верификация 2026-07-06 — НЕ пройдена (расхождение проходов)

Батч C3a (D-015, отмашка Stefan 2026-07-06). Два независимых прохода **разошлись** (`passed = [false, true]`), поэтому `verified_by` во front-matter НЕ проставлен и advisory-WARN D-015 сохраняется намеренно. Вердикты восстановлены из транскриптов после бага интерполяции в исходном писаре.

Замечания прохода, вернувшего `passed=false` (actionable-долг, файл:строка):

- `drivers/repo-runner.md:52` — заявлено «`drivers/repo-runner/fixtures/` — тестовые фикстуры (пример репозитория)», но каталог отсутствует и НИКОГДА не существовал в git-истории (`git log --all -- drivers/repo-runner/fixtures` пуст; `git ls-files` показывает только 4 файла). Тесты используют temp-каталоги (`drivers/test_tmp.py`), MCP-приёмка — `data/fixtures`. Единственное жёсткое расхождение манифеста с реальностью.
- `drivers/repo-runner.md:68` (и `:6, :10`) — примечание «L2-runtime требует отдельной приёмки `T-051`» устарело: `tasks/T-051.md:5` `status: done` (sync acceptance pass=23 fail=0). Манифест держит `level: L2` / `activation: manual` при живом принятом L2 MCP-runtime (`drivers/repo-runner/mcp_server.py`); занижение возможностей — безопасное направление дрейфа, но `drivers/index.json:72,78` из-за этого расходится с фактическим режимом работы.
- `drivers/repo-runner.md:18-19` — `timeout_seconds: 30` и `max_output_bytes: 1048576` задекларированы, но нигде не форсируются в `mcp_server.py` (нет серверного таймаута и ограничения размера вывода; вывод ограничен лишь косвенно `max_files=1000`). Для L1-манифеста соответствует SCHEMA.md:80, но L2-runtime уже принят (T-051) — advisory на доработку.
- (repo-wide, не дефект драйвера) `python tools/generate.py --check` → exit 1, STALE `STATUS.md, board.md, TASKS.md, DECISIONS.md, index.json` — §3 чек-листа сейчас невыполним; индексы не перегенерированы после `decisions/D-024..D-029` (validate.py WARN про D-023). Не специфично для repo-runner.
- Минор: `drivers/repo-runner.md:51` описывает `test_inventory.py` как «тесты (pytest)», но pytest не установлен в текущем venv (`No module named pytest`); тесты полностью проходят standalone-запуском `python drivers\repo-runner\test_inventory.py` — сам файл pytest-совместим, расхождение только со средой.
## Доработка T-288 — лимиты MCP/read-only runtime

Codex, 2026-07-06: замечание D-015 по `repo-runner` частично переведено из текста в исполняемое поведение.

Что изменено:

- `drivers/repo-runner/inventory.py` получил `clamp_max_files()` и теперь ограничивает любой входной `max_files` потолком `DEFAULT_MAX_FILES = 1000` уже внутри `scan_repo()`.
- `drivers/repo-runner/inventory.py` получил `limit_output()` — мягкое ограничение размера payload для больших MCP-ответов по `max_output_bytes = 1048576`.
- `drivers/repo-runner/mcp_server.py` использует общий `_scan()` с `REPO_RUNNER_BASE`, клампом `max_files` и `limit_output()` для `inspect_repo`/`repo_risks`.
- `drivers/repo-runner/test_inventory.py` добавил regression-тест `test_limit_helpers()` без зависимости от MCP/FastMCP.

Граница исправления: `timeout_seconds` остаётся декларативным лимитом процесса MCP/stdio, потому текущий L2-драйвер ничего не исполняет и не запускает внешние команды. Жёсткий wall-clock timeout должен появиться на L3 sandbox-runner или во внешнем MCP host/preflight, а не внутри read-only scanner.

Проверка: `PYTHONDONTWRITEBYTECODE=1 python drivers\repo-runner\test_inventory.py` — PASS, включая `PASS: limit helpers`.
