---
id: gateway-inprocess-test-result-2026-06-21
title: Gateway in-process test result — T-093
status: done
owner: Codex
related: tasks/T-093.md, drivers/gateway/test_gateway.py, drivers/gateway/mcp_server.py, docs/stale-work-cleanup-policy-2026-06-21.md
---

# Gateway in-process test result — T-093

Дата: 2026-06-21.

## Контекст

После cleanup T-091 появился `tasks/T-093.md` как пустой placeholder, но в рабочем дереве также был `drivers/gateway/test_gateway.py` с пометкой `T-093`. Это означало не пустой резерв, а незавершённую синхронизацию task-файла и артефакта кода.

## Что исправлено

- `T-093` превращён в реальную done-задачу.
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
