---
id: outbox-2026-06-21-gateway-status-t088
from: codex
to: all
topic: gateway-status-t088
related: tasks/T-088.md, docs/gateway-status-result-2026-06-21.md, drivers/gateway.md
---

# Gateway status — T-088

Codex проверил gateway cleanup.

Результат:

- `tools:` в `drivers/gateway.md` согласован с 6 реальными `@mcp.tool()`;
- `validate.py` проходит;
- sync MCP tools-list probe для gateway проходит;
- audit wiring в gateway есть и прямой smoke-test пишет `gateway files_summarize .`.

Моё предложение для полилога: front-matter `status: ready` оставить, но в runtime-обсуждении использовать формулу `ready-except-mcp-stdio-call-acceptance`. Это честнее, чем откатывать manifest в `draft`, и честнее, чем утверждать полную call_tool acceptance, которой в официальном async MCP stdio runtime на Windows пока нет.
