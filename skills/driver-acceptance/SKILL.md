---
name: driver-acceptance
description: Принять новый/изменённый драйвер AI-OS Bridge до статуса ready — прогнать unit + MCP-приёмку, сверить манифест, поднять статус по D-015. Использовать при добавлении драйвера или изменении его engine/MCP-сервера.
---

# Skill: приёмка драйвера (driver-acceptance)

Повторяемая процедура доведения драйвера `drivers/<id>/` до `status: ready` по **D-015**
(код работает + сверка ≥2 агентами), без ожидания ручной подписи человека.

## Шаги

1. **Unit-тест движка:**
   `python drivers/<id>/test_<id>.py` → должно быть `TESTS OK`.
   (используйте `from test_tmp import temp_dir` для временных папок внутри `tmp-work/`.)

2. **Манифест ↔ сервер:** в `drivers/<id>.md` укажите `tools: [...]` = реальные имена `@mcp.tool()`
   из `drivers/<id>/mcp_server.py`. Проверка: `python tools/validate.py` → строка
   `drivers tools: N манифестов сверены` без ERROR.

3. **MCP `tools/call`-приёмка (переносимая):** добавьте сервер в `drivers/mcp_sync_probe.py`
   `SERVERS` и набор вызовов в `drivers/mcp_sync_acceptance.py` `CALLS`, затем
   `python drivers/mcp_sync_acceptance.py <id>` → `pass=N fail=0 RESULT OK`.
   (sync-путь работает там, где async stdio падает WinError 5.)

4. **Безопасность (risk≥medium):** обвяжите вызовы `from audit import audit` (см. `data`/`gateway`);
   `git`/subprocess-вызовы внутри MCP-сервера — с `stdin=subprocess.DEVNULL` (иначе Windows-дедлок).

5. **Статус → ready:** когда п.1-3 зелёные и сверены ≥2 агентами — в `drivers/<id>.md`
   `status: draft → ready`, `source_last_verified: <дата>`; затем
   `python tools/drivers_catalog.py && python tools/validate.py` (ERROR=0).

## Готово, если

`validate OK ERROR=0`, sync-приёмка драйвера зелёная, манифест `tools` сверен, статус `ready`
с записью о двухагентной верификации в `## Статус` манифеста.

Связано: `decisions/D-015.md`, `drivers/SCHEMA.md`, `docs/bridge-usage.md`.
