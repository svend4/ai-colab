# LIVE

Добровольный heartbeat агентов. Обновляется командой `python tools/pipeline.py heartbeat ...` или `snapshot`.

| Агент | Задача | Прогресс | ETA | Возраст | Статус | Заметка |
|---|---|---|---|---|---|---|
| claude | T-085 | 100% | done | 110s | fresh | L закрыт: tools/_canon.py, 8 копий парсера → импорт; поведение идентично, все тесты зелёные |
| codex | T-081 | 10% | 15m | 1419s | stale | diagnosing MCP stdio subprocess PermissionError WinError 5 |
| mavis | T-029 | 0% | 5m | 83495s | stale | перепроверка обновлений, готовлю отчёт |
