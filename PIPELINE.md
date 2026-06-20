# PIPELINE

Автоматический снимок конвейера. Генерируется командой `python tools/pipeline.py snapshot`.

## В работе

| Задача | Агент | Claim | Lease epoch | Название |
|---|---|---|---|---|
| T-020 | ? |  |  | AI-OS Bridge — исследовать репозитории svend4 и спроектировать коннектор |
| T-058 | Novax | 7afececbd229 | 1781969390 | Driver schema v1 — валидатор и генератор каталога драйверов |

## Готовы к взятию

| Задача | Приоритет | Owner | Название |
|---|---|---|---|
| — | — | — | — |

## Заблокированы

| Задача | Причина | Название |
|---|---|---|
| T-029 | status: blocked | Реализовать read-only files inventory driver |
| T-039 | status: blocked | Разблокировать Python runtime и закрыть T-029 |
| T-048 | depends_on: T-039 blocked | Runtime-приёмка files driver и MCP wrapper после восстановления Python |
| T-051 | depends_on: T-039 blocked | Runtime-приёмка repo-runner MCP wrapper после hardening |
| T-055 | depends_on: T-039 blocked | Runtime-приёмка workbench.db driver после hardening |
| T-057 | depends_on: T-039 blocked | Runtime-приёмка ingest pipeline после hardening |
| T-059 | status: blocked | File inventory driver — no-deps Python, карта файлов проекта |
