---
id: gateway-inprocess-test-result-2026-06-21
title: Gateway in-process test result — T-094
status: done
owner: Codex
related: tasks/T-094.md, drivers/gateway/test_gateway.py, drivers/gateway/mcp_server.py, docs/stale-work-cleanup-policy-2026-06-21.md
---

# Gateway in-process test result — T-094

Дата: 2026-06-21.

## Контекст

После cleanup T-091 появился `tasks/T-093.md` как пустой placeholder, а параллельный коммит оформил реальную gateway-test работу как `T-094`. В рабочем дереве остался полезный follow-up: тест нужно было адаптировать с `tempfile.mkdtemp()` на общий `drivers/test_tmp.py`, потому что стандартная Windows temp-папка в этой среде даёт `PermissionError`.

## Что исправлено

- `T-093` оставлен retired placeholder; реальная задача — `T-094`.
- `drivers/gateway/test_gateway.py` переведён со стандартного `tempfile.mkdtemp()` на `drivers/test_tmp.py`, потому что в этом Windows runtime стандартный temp может создать директорию, недоступную для записи.
- Тест проверяет gateway без MCP stdio: импортирует серверный модуль и вызывает tool-функции напрямую.

## Проверка

Команда:

```powershell
python drivers\gateway\test_gateway.py
```

Результат:

```text
TESTS OK gateway: composition+redaction+confinement+audit (audit lines=6)
```

## Вывод

Тест полезен как регрессия для `T-088`: он не заменяет официальную MCP `call_tool` acceptance, но покрывает реальную композицию gateway, redaction, allowed-root confinement и audit без зависимости от Windows `asyncio` stdio blocker.
