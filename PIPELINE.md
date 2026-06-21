# PIPELINE

Автоматический снимок конвейера. Генерируется командой `python tools/pipeline.py snapshot`.

## В работе

| Задача | Агент | Claim | Lease epoch | Название |
|---|---|---|---|---|
| — | — | — | — | — |

## Готовы к взятию

| Задача | Приоритет | Owner | Название |
|---|---|---|---|
| T-055 | high | pool | Runtime-приёмка workbench.db driver после hardening |
| T-057 | high | pool | Runtime-приёмка ingest pipeline после hardening |
| T-059 | high | pool | File inventory driver — no-deps Python, карта файлов проекта |
| T-085 | normal | pool | Единый tools/_canon.py — убрать 8 копий парсера front-matter (P1, находка L) |

## Заблокированы

| Задача | Причина | Название |
|---|---|---|
| T-020 | doing without active claim | AI-OS Bridge — исследовать репозитории svend4 и спроектировать коннектор |
| T-048 | status: blocked | Runtime-приёмка files driver и MCP wrapper после восстановления Python |
| T-051 | status: blocked | Runtime-приёмка repo-runner MCP wrapper после hardening |
| T-062 | placeholder task | (зарезервировано — заполните) |
| T-063 | placeholder task | (зарезервировано — заполните) |
| T-064 | placeholder task | (зарезервировано — заполните) |
