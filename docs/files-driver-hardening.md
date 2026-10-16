# Files driver hardening report

Дата: 2026-06-20
Автор: Codex
Связано: `T-043`, `T-046`, `T-047`, `T-048`, `docs/driver-safety-policy.md`

## Контекст

Claude закрыл `T-046`: добавлен `drivers/files/mcp_server.py`, done-marker сообщает `handshake OK`, `tools/list=4`, `summarize OK`.

После статической перепроверки Codex внёс hardening-правки, потому что MCP-wrapper напрямую передавал пути в `files_driver.py`. Для многоагентной среды это слишком широкий интерфейс: даже read-only инструмент должен иметь allowed-root и лимиты обхода.

## Что изменено

В `drivers/files/files_driver.py`:

- добавлен `base_dir` / allowed-root для `list_files`, `read_file`, `search`, `summarize`;
- добавлена ошибка `PathAccessError` при выходе за allowed-root;
- относительные пути при заданном `base_dir` теперь резолвятся относительно allowed-root;
- добавлены `DEFAULT_MAX_FILES` и `DEFAULT_MAX_HITS`;
- `list/search/summarize` получили лимиты обхода;
- добавлен пропуск шумных директорий: `.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build` и похожих;
- `read_file()` теперь маскирует secret-like значения по умолчанию;
- `search()` теперь по умолчанию делает substring-search, regex включается только явным флагом.

В `drivers/files/mcp_server.py`:

- добавлен `FILES_DRIVER_BASE` как allowed-root для MCP-сервера;
- если `FILES_DRIVER_BASE` не задан, сервер не стартует (fail-closed; это изменено, см. раздел «Изменение 2026-10-16» ниже);
- MCP-инструменты передают `base_dir`, `max_files`, `max_hits`, `include_hidden` в engine;
- MCP `read_file` всегда использует redaction;
- MCP `search` использует substring-search, regex не открыт в tool surface.

В `drivers/files/test_files.py`:

- добавлены проверки redaction в `read`;
- добавлены проверки `max_hits`, `max_files`;
- добавлена проверка запрета выхода за `base_dir`.

## Что осталось не проверено

Из-за `T-039` Codex не запускал:

```powershell
python drivers\files\test_files.py
python drivers\files\test_inventory.py
python tools\validate.py
python tools\generate.py --check
```

Поэтому `T-047` закрывает именно static hardening. Настоящая runtime-приёмка вынесена в `T-048`.

## Мнение Codex

Теперь направление правильнее: MCP-layer остаётся простым, но больше не должен видеть всю файловую систему по умолчанию. Для первого L2-драйвера это принципиально. Удобство можно расширять позже, а allowed-root и лимиты должны быть встроены сразу.

Оставшийся риск один: без реального runtime-прогона нельзя подтвердить, что FastMCP schema корректно отражает новые параметры и что тесты проходят в этой Windows-среде.

## Изменение 2026-10-16: fail-closed для `*_BASE`

Раньше каждая точка входа делала `X_BASE or os.getcwd()`: без переменной зона тихо становилась рабочей папкой процесса. Если процесс запускали из домашней папки, зоной оказывалась вся домашняя папка. Теперь переменная зоны обязательна.

| Переменная | Точка входа |
|---|---|
| `FILES_DRIVER_BASE` | `drivers/files/mcp_server.py` |
| `REPO_RUNNER_BASE` | `drivers/repo-runner/mcp_server.py` |
| `GIT_LOG_BASE` | `drivers/git-log/mcp_server.py` |
| `DATA_DRIVER_BASE` | `drivers/data/mcp_server.py` |
| `SQLITE_DRIVER_BASE` | `drivers/sqlite/mcp_server.py` |
| `GATEWAY_BASE` | `drivers/gateway/mcp_server.py` |
| `WORKBENCH_BASE` | `drivers/workbench/workbench.py`, `drivers/workbench/ingest.py` |
| `INGEST_SOURCE_BASE` | `drivers/workbench/ingest.py` |

- MCP-сервер без переменной завершается с кодом 1 и сообщением на stderr. Проверка стоит до импорта `mcp`, поэтому отказ виден даже без FastMCP.
- CLI без переменной печатает JSON `{"error": "ConfigError", ...}` и возвращает код 2.
- Пустая или пробельная переменная считается незаданной.
- Клиенты MCP (например, `~/.codex/config.toml`) должны передавать нужную переменную в `env`; иначе сервер не запустится.

Проверка: `tools/tests/test_base_env_fail_closed.py` (отказ каждой точки входа без переменной, пустое значение, позитивный прогон CLI с `WORKBENCH_BASE`).

После merge драйвер `files` перепроверяется по D-038 (решение участника проекта).
