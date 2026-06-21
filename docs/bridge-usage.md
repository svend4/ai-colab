# AI-OS Bridge — как пользоваться средним слоем (usage)

Операционный гайд: как **запустить** и **подключить** уже построенный «средний слой»
(драйверы + gateway), что он умеет сегодня и что в работе. Концепция — в
`docs/middle-layer-guide.md`; карта слоёв — в `docs/layers-coverage.md` (канон нумерации).

## 1. Что это даёт за один раз — демо

Самый быстрый способ увидеть слой в действии (работает в любой среде, без MCP-сервера):

```bash
python tools/demo_bridge.py            # на data/fixtures
python tools/demo_bridge.py <папка>    # на своей папке (allowed-root)
```

Показывает 4 способности на реальной папке: карта файлов, поиск (с маскировкой секретов),
инвентаризация репозитория (языки/тесты/риски, код не запускается), память
(`workbench.db`: занести документы и найти по запросу).

## 2. Драйверы (что есть)

| Драйвер | Что делает | Режим | Инструменты (MCP) |
|---|---|---|---|
| `files` | чтение/инвентаризация файлов, поиск, redaction секретов | read-only | `list_files, read_file, search, summarize` |
| `repo-runner` | inventory репозитория (структура/языки/тесты/риски), **код не запускается** | read-only | `inspect_repo, repo_summary, repo_risks` |
| `data` | таблицы CSV/TSV: список/колонки/срез/сводка, redaction | read-only | `list_tables, columns, head, summarize` |
| `codex-local` | наличие/версия локального Codex | manual | `codex_available, codex_info` |
| `workbench` | SQLite-память корпуса (`documents`+`audit_log`), запрос | safe-write | (через `gateway.memory_query`) |
| `gateway` | **композиция** — один MCP-сервер над files/repo/workbench | read-only | `files_*, repo_inspect, memory_query` |

Манифесты — `drivers/<id>.md` (front-matter с `risk`/`mode`/`tools`/`audit`/`source_last_verified`);
машинный каталог — `drivers/CATALOG.md` и `drivers/index.json` (генерируются `tools/drivers_catalog.py`).

## 3. Подключить gateway к AI-клиенту (MCP)

`gateway` — один stdio MCP-сервер (`drivers/gateway/mcp_server.py`, имя `ai-os-bridge`),
дающий AI-клиенту 6 инструментов сразу. Пример для Codex (`~/.codex/config.toml`):

```toml
[mcp_servers.ai-os-bridge]
command = "python"
args = ["<repo>/drivers/gateway/mcp_server.py"]
env = { GATEWAY_BASE = "<allowed-root>" }
```

`GATEWAY_BASE` ограничивает зону доступа (allowed-root). Без него — текущая рабочая папка.

## 4. Безопасность (что гарантировано)

- **allowed-root confinement**: выход за `*_BASE` → `PathAccessError` (`resolve()+relative_to`).
- **redaction секретов** в выдаче файлов (`api_key=`/`AKIA…` → `***`) через общий `drivers/redaction.py`.
- **аудит** вызовов risk≥medium-драйверов (`data`/`repo-runner`/`codex-local`/`gateway`) в
  `logs/driver-audit.jsonl` через `drivers/audit.py` (`python drivers/audit.py tail`).
- **лимиты**: `max_files`/`max_hits`/`max_output_bytes`; **read-only** — код репозиториев не запускается.
- **execute-гард**: `mode: execute` без реальной изоляции (container/nsjail/...) — ERROR валидатора (D-015/находка G).

## 5. Проверка/приёмка

```bash
python tools/validate.py                         # канон + манифесты + tools↔сервер
python drivers/gateway/test_gateway.py           # gateway in-process (быстро, любая среда)
python drivers/mcp_handshake_test.py             # MCP handshake (async stdio)
python drivers/mcp_acceptance_test.py            # MCP call_tool 19/19 (async stdio)
python drivers/mcp_sync_probe.py gateway         # MCP через sync subprocess (обход WinError 5)
```

**Замечание по среде:** официальный async MCP stdio-клиент на части Windows-сред падает с
`PermissionError [WinError 5]` (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md`). Поэтому есть
**синхронный** путь (`drivers/mcp_sync_probe.py` и sync-приёмка) — переносимый между средами.

## 6. Что сегодня работает / что в работе

- ✅ Работает: read-only драйверы (files/repo-runner/data/codex-local), gateway-композиция,
  workbench-память, демо, in-process тесты, manifest↔tools сверка, аудит.
- 🟡 В работе: устойчивая `tools/call` MCP-приёмка во всех средах (sync-путь), knowledge workflow
  (corpora→ingest→query report), переносимые project skills (L3).
- ⛔ Отдельно (с песочницей): запуск непроверенного кода (svend4) — требует контейнера/изоляции,
  `mode: execute` закрыт гардом до её реализации.

Связано: `docs/middle-layer-guide.md`, `docs/layers-coverage.md`, `темы/ai-os-bridge.md`,
`decisions/D-010.md`, `decisions/D-013.md`, `decisions/D-015.md`.
