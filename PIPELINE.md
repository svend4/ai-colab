# PIPELINE

Автоматический снимок конвейера. Генерируется командой `python tools/pipeline.py snapshot`.

## В работе

| Задача | Агент | Claim | Lease epoch | Название |
|---|---|---|---|---|
| — | — | — | — | — |

## Готовы к взятию

| Задача | Приоритет | Owner | Название |
|---|---|---|---|
| T-087 | high | pool | Реализовать sync MCP stdio probe без asyncio для acceptance |
| T-088 | high | pool | Gateway driver cleanup — audit, tools manifest, status policy |
| T-089 | normal | pool | Files driver cleanup — общий redaction helper и tools manifest |
| T-090 | high | pool | Driver status reconciliation — draft/ready матрица после acceptance |
| T-091 | normal | pool | Очистить placeholder/stale-work слой без svend4 |

## Заблокированы

| Задача | Причина | Название |
|---|---|---|
| T-020 | doing without active claim | AI-OS Bridge — исследовать репозитории svend4 и спроектировать коннектор |
| T-048 | status: blocked | Runtime-приёмка files driver и MCP wrapper после восстановления Python |
| T-051 | status: blocked | Runtime-приёмка repo-runner MCP wrapper после hardening |
| T-062 | placeholder task | (зарезервировано — заполните) |
| T-063 | placeholder task | (зарезервировано — заполните) |
| T-064 | placeholder task | (зарезервировано — заполните) |
