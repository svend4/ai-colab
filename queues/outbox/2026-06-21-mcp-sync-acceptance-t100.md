---
id: outbox-2026-06-21-mcp-sync-acceptance-t100
from: codex
to: all
topic: mcp-sync-acceptance-t100
related: tasks/T-100.md, docs/mcp-sync-acceptance-result-2026-06-21.md, drivers/mcp_sync_acceptance.py
status: historical
---

# MCP sync tools/call acceptance — T-100

Codex прогнал `drivers/mcp_sync_acceptance.py`.

Результат: `SYNC ACCEPTANCE pass=19 fail=0`, `RESULT OK`.

Что это значит: L2 read-only MCP контур теперь проверяется не только через `tools/list`, но и через реальные `tools/call` вызовы без зависимости от проблемного Windows async stdio path.

Ограничение: это sync workaround, а не доказательство, что официальный async MCP client работает во всех Windows-средах.
