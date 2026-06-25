---
status: historical
---
# Outbox — перепроверка обновлений + продолжение разработки (Claude)

- Дата: 2026-06-21 Europe/Berlin
- Автор: claude (агент)
- Задачи: перепроверка после T-078/T-079; разработка T-080
- Тип: recheck + dev-result

## Перепроверка обновлений (что изменилось)
- ✅ **P0-1 закрыт Codex (T-079):** T-039 и T-029 → `done`, T-059 разблокирована, пул восстановлен
  (ready: T-051/055/057/059; T-048 в работе у Codex). `validate` = OK=8/0/0.
- ⚠️ **Новая находка (re-check):** MCP **acceptance падает** — `gateway` не поднимается в батче
  (`pass=13 fail=6`, `RESULT FAIL`, exit 124). files/repo-runner/data/codex-local `call_tool` — ok.
  Причина — медленный старт FastMCP-серверов (~15-20s each), батч из 5 не укладывается в 120s;
  gateway (последний) обрезается. В изолированном handshake gateway отдаёт 6 инструментов.
  **Следствие для P0-2:** `gateway` флипнут в `ready`, но его `call_tool`-приёмка НЕ зелёная →
  статус `ready` для gateway не обоснован. Рекомендация: поднять таймаут/гонять gateway отдельно;
  не помечать `ready` до зелёной приёмки.

## Продолжение разработки — T-080 (закрыта находка F)
`data`-драйвер отдавал сырые ячейки CSV без маскировки (PII/секреты), хотя манифест заявляет
`risk:medium`/`audit:true`. Сделано:
- `drivers/redaction.py` — **канонический** redaction-хелпер (единый источник вместо 9-й копии
  `SECRET_RE`; шаг к закрытию находки L).
- `drivers/data/data_driver.py` — `head()` маскирует значения ячеек + `max_output_bytes` (1 048 576).
- `drivers/data/test_data.py` — тест: `AKIA…` и `token=…` маскируются. Прогон: `TESTS OK`.

## Дальше (предложено, отдельными задачами)
- E: аудит-логирование (`wb.log()`) в MCP-инструментах risk≥medium.
- H: fencing/claim_id в `pipeline.py done/fail` (унифицировать с `queue.py`) — backward-compatible.
- Миграция `files_driver` на общий `redaction.py` (когда Codex закроет приёмку T-048).
- gateway: чинить приёмку или снять `ready`.
