# LIVE

Добровольный heartbeat агентов. Обновляется командой `python tools/pipeline.py heartbeat ...` или `snapshot`.

| Агент | Задача | Прогресс | ETA | Возраст | Статус | Заметка |
|---|---|---|---|---|---|---|
| claude | T-092 | 100% | done | 816s | fresh | G: execute-sandbox gate в validate (ERROR без реальной изоляции) |
| codex | T-081 | 10% | 15m | 2831s | stale | diagnosing MCP stdio subprocess PermissionError WinError 5 |
| mavis | T-029 | 0% | 5m | 84907s | stale | перепроверка обновлений, готовлю отчёт |
