# PIPELINE

Автоматический снимок конвейера. Генерируется командой `python tools/pipeline.py snapshot`.

## В работе

| Задача | Агент | Claim | Lease epoch | Название |
|---|---|---|---|---|
| — | — | — | — | — |

## Готовы к взятию

| Задача | Приоритет | Owner | Название |
|---|---|---|---|
| T-124 | high | pool | Quickstart pipeline cleanup — убрать legacy queue.py из входных инструкций |
| T-127 | normal | pool | Larger safe corpus — применить L6 workflow к 50-200 read-only файлам |
| T-130 | normal | pool | C2 drift detector — tools/drift_check.py (консенсус) |
| T-131 | normal | pool | C3 onboard-команда — tools/onboard.py (консенсус) |

## Заблокированы

| Задача | Причина | Название |
|---|---|---|
| T-020 | doing without active claim | AI-OS Bridge — исследовать репозитории svend4 и спроектировать коннектор |
