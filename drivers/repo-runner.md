---
id: repo-runner
type: driver
title: Repo runner — inventory репозиториев и будущий запуск в песочнице
status: ready
level: L1
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

- **L1 (текущий):** только read-only. Запуск `install`, `run`, `test`, shell-команд и сетевых действий — **строго запрещён**.
- **L2 (MCP):** inspect/summarize как инструменты для агента. Всё ещё read-only.
- **L3 (server):** запуск `test/run` только в изолированной песочнице (Docker, отдельный пользователь, limts CPU/памяти/сети, нет секретов).
- **Секреты:** запрещено хранить в репозитории. Если нужны ключи — через env/secret manager, не в коде.

## Реализация

- `drivers/repo-runner/inventory.py` — скрипт inventory (Python 3, no-deps).
- `drivers/repo-runner/test_inventory.py` — тесты (pytest).
- `drivers/repo-runner/fixtures/` — тестовые фикстуры (пример репозитория).

## Путь развития

- L1: read-only inventory (сейчас).
- L2: MCP-инструмент `inspect/summarize` для агента.
- L3: серверный sandbox-runner для ограниченного `test/run`.

## Текущее состояние реализации

На 2026-06-20 уже есть L2-draft код:

- `drivers/repo-runner/inventory.py` — engine `scan_repo`;
- `drivers/repo-runner/mcp_server.py` — FastMCP stdio wrapper;
- `drivers/repo-runner/test_inventory.py` — тесты scanner/hardening.

После `T-050` MCP-wrapper использует allowed-root через `REPO_RUNNER_BASE`, `max_files`, флаг `truncated` и запрет выхода за `base_dir`. Статус манифеста остаётся `ready` как L1/read-only manifest, но L2-runtime требует отдельной приёмки `T-051`.

## Верификация 2026-07-06 — НЕ пройдена (расхождение проходов)

Батч C3a (D-015, отмашка Stefan 2026-07-06). Два независимых прохода **разошлись** (`passed = [false, true]`), поэтому `verified_by` во front-matter НЕ проставлен и advisory-WARN D-015 сохраняется намеренно. Вердикты восстановлены из транскриптов после бага интерполяции в исходном писаре.

Замечания прохода, вернувшего `passed=false` (actionable-долг, файл:строка):

- `drivers/repo-runner.md:52` — заявлено «`drivers/repo-runner/fixtures/` — тестовые фикстуры (пример репозитория)», но каталог отсутствует и НИКОГДА не существовал в git-истории (`git log --all -- drivers/repo-runner/fixtures` пуст; `git ls-files` показывает только 4 файла). Тесты используют temp-каталоги (`drivers/test_tmp.py`), MCP-приёмка — `data/fixtures`. Единственное жёсткое расхождение манифеста с реальностью.
- `drivers/repo-runner.md:68` (и `:6, :10`) — примечание «L2-runtime требует отдельной приёмки `T-051`» устарело: `tasks/T-051.md:5` `status: done` (sync acceptance pass=23 fail=0). Манифест держит `level: L1` / `activation: manual` при живом принятом L2 MCP-runtime (`drivers/repo-runner/mcp_server.py`); занижение возможностей — безопасное направление дрейфа, но `drivers/index.json:72,78` из-за этого расходится с фактическим режимом работы.
- `drivers/repo-runner.md:18-19` — `timeout_seconds: 30` и `max_output_bytes: 1048576` задекларированы, но нигде не форсируются в `mcp_server.py` (нет серверного таймаута и ограничения размера вывода; вывод ограничен лишь косвенно `max_files=1000`). Для L1-манифеста соответствует SCHEMA.md:80, но L2-runtime уже принят (T-051) — advisory на доработку.
- (repo-wide, не дефект драйвера) `python tools/generate.py --check` → exit 1, STALE `STATUS.md, board.md, TASKS.md, DECISIONS.md, index.json` — §3 чек-листа сейчас невыполним; индексы не перегенерированы после `decisions/D-024..D-029` (validate.py WARN про D-023). Не специфично для repo-runner.
- Минор: `drivers/repo-runner.md:51` описывает `test_inventory.py` как «тесты (pytest)», но pytest не установлен в текущем venv (`No module named pytest`); тесты полностью проходят standalone-запуском `python drivers\repo-runner\test_inventory.py` — сам файл pytest-совместим, расхождение только со средой.
