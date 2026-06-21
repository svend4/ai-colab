# MCP handshake result

Дата: 2026-06-21

Источник: ручной запуск пользователем в Windows PowerShell.

Связано:

- `T-039`
- `T-074`
- `docs/driver-acceptance-batch-2026-06-21.md`

## Команда

```powershell
Invoke-Timed "mcp handshake" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\mcp_handshake_test.py
} 60 @($repo)
```

## Результат

```text
OK data tools=4 ['columns', 'head', 'list_tables', 'summarize']
OK codex-local tools=2 ['codex_available', 'codex_info']
OK gateway tools=6 ['files_list', 'files_read', 'files_search', 'files_summarize', 'memory_query', 'repo_inspect']
RESULT OK
```

PowerShell также показал `NativeCommandError`, связанный с stderr-логами MCP/FastMCP:

```text
Processing request of type ListToolsRequest
NativeCommandError
```

Так как итоговая строка `RESULT OK`, smoke-handshake считается пройденным.

## Что подтверждено

Batch D из `docs/driver-acceptance-batch-2026-06-21.md` пройден для текущего среза:

- `data` MCP server поднимается и отдаёт 4 tools;
- `codex-local` MCP server поднимается и отдаёт 2 tools;
- `gateway` MCP server поднимается и отдаёт 6 tools.

## Что не закрыто этим результатом

Этот результат не закрывает весь driver acceptance batch.

Остаются:

- Batch A: `validate.py`, `drivers_catalog.py` repeat, если нужен полный пакет за 2026-06-21;
- Batch B: driver tests для `files`, `repo-runner`, `workbench`, `workbench-db`, `file-inventory`;
- Batch C: pipeline guards `ready_sorted == []` и `T-020` как `doing without active claim`.

После прохождения Batch B/C можно будет принимать решения по `T-048`, `T-051`, `T-055`, `T-057`, `T-059`, `T-067`, `T-068`.

