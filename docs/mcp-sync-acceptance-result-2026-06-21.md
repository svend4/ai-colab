---
id: mcp-sync-acceptance-result-2026-06-21
title: MCP sync tools/call acceptance result — T-100
status: done
owner: Codex
related: tasks/T-100.md, drivers/mcp_sync_acceptance.py, drivers/mcp_sync_probe.py, docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md
---

# MCP sync tools/call acceptance result — T-100

Дата: 2026-06-21.

## Что сделано

Добавлен/оформлен `drivers/mcp_sync_acceptance.py`: переносимый acceptance-прогон MCP `tools/call` поверх синхронного JSON-RPC stdio клиента из `drivers/mcp_sync_probe.py`.

Зачем: официальный Python MCP async stdio client в этой Windows-среде может падать на `asyncio.create_subprocess_exec(... PIPE ...)` / `PermissionError [WinError 5]`. Синхронный путь использует `subprocess.Popen(... PIPE ...)`, который работает.

## Проверка

Команда:

```powershell
python drivers\mcp_sync_acceptance.py --timeout 90
```

Результат:

```text
SYNC ACCEPTANCE pass=19 fail=0
RESULT OK
```

Покрытие:

- `files`: 4 tools/call;
- `repo-runner`: 3 tools/call;
- `data`: 4 tools/call;
- `codex-local`: 2 tools/call;
- `gateway`: 6 tools/call.

## Вывод

L2 read-only MCP контур теперь имеет переносимую `tools/call` acceptance на 19 инструментов. Это не отменяет полезность официальной async MCP acceptance в средах, где она работает, но снимает локальный Windows blocker для регулярной проверки read-only драйверов.
