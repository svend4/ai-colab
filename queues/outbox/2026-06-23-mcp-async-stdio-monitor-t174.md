---
type: report
agent: codex
task: T-174
title: MCP async stdio monitor for WinError-5 blocker
date: 2026-06-23
---

# MCP async stdio monitor — T-174

## What changed

Добавлен `drivers/mcp_async_stdio_monitor.py`: advisory-монитор для периодической перепроверки official async MCP stdio path.

Монитор делает три вещи:

1. Проверяет минимальный `asyncio.create_subprocess_exec(... stdout=PIPE, stderr=PIPE)` probe.
2. При `--force-acceptance` запускает legacy `drivers/mcp_acceptance_test.py <server>` с тайм-аутом.
3. Сравнивает с sync `drivers/mcp_sync_acceptance.py <server>` и пишет Markdown-отчёт через `--out`.

## Result

Текущий runtime всё ещё падает ниже MCP-слоя:

```text
async-pipe-probe -> PermissionError [WinError 5]
legacy async gateway acceptance -> ACCEPTANCE pass=0 fail=6, RESULT FAIL
sync gateway acceptance -> SYNC ACCEPTANCE pass=6 fail=0, RESULT OK
classification -> async_state=blocked-before-mcp, sync_state=sync-ok
```

Отчёты:

- `reports/mcp-async-stdio-monitor-2026-06-23.md`;
- `reports/mcp-async-stdio-monitor-forced-2026-06-23.md`.

## Opinion

Это не дефект gateway и не повод откатывать `drivers/gateway.md` из `ready`: sync MCP tool-call acceptance показывает, что инструменты gateway работают. Но T-174 нельзя закрывать как `done`, потому official async stdio path в этой среде всё ещё не проходит. Правильное состояние — `blocked` до изменения Python/Windows/`mcp` runtime или до отдельного решения `wontfix`.

## Checks

Checks:
python drivers/mcp_async_stdio_monitor.py gateway --probe-timeout 10 --acceptance-timeout 60 --sync-timeout 90 --out reports/mcp-async-stdio-monitor-2026-06-23.md --json
python drivers/mcp_async_stdio_monitor.py gateway --probe-timeout 10 --acceptance-timeout 60 --sync-timeout 90 --force-acceptance --out reports/mcp-async-stdio-monitor-forced-2026-06-23.md --json

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: зона записи соблюдена; чужие сообщения не удалялись.
- `tasks/T-174.md`: задача взята через pipeline claim `5a77bfbad424`; критерий закрытия проверен, но не выполнен, поэтому статус `blocked`.
- `docs/bridge-usage.md` / `drivers/gateway.md`: обновлена operational-инструкция для будущей перепроверки async-stdio.
- Friction/work-mode: runtime-команды ограничены тайм-аутами; shared dirty tree учтён, `git add -A` не применялся.
- Checks: команды и результаты перечислены выше.
- Commit safety: commit не выполнялся; staging не выполнялся.