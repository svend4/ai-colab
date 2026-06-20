# PIPELINE

Автоматический снимок конвейера. Генерируется командой `python tools/pipeline.py snapshot`.

## В работе

| Задача | Агент | Claim | Lease epoch | Название |
|---|---|---|---|---|
| — | — | — | — | — |

## Готовы к взятию

| Задача | Приоритет | Owner | Название |
|---|---|---|---|
| — | — | — | — |

## Заблокированы

| Задача | Причина | Название |
|---|---|---|
| T-020 | doing without active claim | AI-OS Bridge — исследовать репозитории svend4 и спроектировать коннектор |
| T-029 | status: blocked | Реализовать read-only files inventory driver |
| T-039 | status: blocked | Разблокировать Python runtime и закрыть T-029 |
| T-048 | T-039 | Runtime-приёмка files driver и MCP wrapper после восстановления Python |
| T-051 | T-039 | Runtime-приёмка repo-runner MCP wrapper после hardening |
| T-055 | T-039 | Runtime-приёмка workbench.db driver после hardening |
| T-057 | T-039 | Runtime-приёмка ingest pipeline после hardening |
| T-059 | status: blocked | File inventory driver — no-deps Python, карта файлов проекта |
| T-062 | placeholder task | (зарезервировано — заполните) |
| T-063 | placeholder task | (зарезервировано — заполните) |
| T-064 | placeholder task | (зарезервировано — заполните) |
| T-067 | status: blocked | Pipeline placeholder gating — не выдавать резервные задачи агентам |
| T-068 | status: blocked | Pipeline orphan doing detection — показывать doing без claim как проблему |
