---
status: historical
---
# Outbox: MCP handshake result

Адресаты: люди, AI-агенты, reviewer, summarizer.

Связанный документ: `docs/mcp-handshake-result-2026-06-21.md`.

## Кратко

Пользователь прогнал:

```powershell
python drivers\mcp_handshake_test.py
```

Результат:

- `data`: OK, 4 tools;
- `codex-local`: OK, 2 tools;
- `gateway`: OK, 6 tools;
- итог: `RESULT OK`.

`NativeCommandError` в PowerShell связан со stderr-логами MCP/FastMCP; по итоговой строке smoke-handshake считается пройденным.

Остальные части driver acceptance batch ещё нужно прогнать.

