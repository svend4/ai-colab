---
id: knowledge-workflow-result-2026-06-21
title: Knowledge workflow result — T-107
status: done
owner: Codex
related: tasks/T-107.md, tools/knowledge.py, drivers/workbench.md, docs/layers-coverage.md
---

# Knowledge workflow result — T-107

Дата: 2026-06-21.

## Что сделано

`tools/knowledge.py` оформлен как практический L6 workflow поверх уже готовых `files` и `workbench` drivers:

```text
corpus → files.list/read(redaction) → workbench.documents → query → markdown report
```

Это не vector/RAG и не серверная память. Это минимальный воспроизводимый сценарий для работы с локальным корпусом: занести документы в SQLite-память, посмотреть состав по типам/рискам и выполнить текстовый запрос.

## Проверки

```powershell
python tools\knowledge.py report data\fixtures --query sample
```

Результат: 8 документов занесены, 4 совпадения по `sample`.

```powershell
python tools\knowledge.py query logs\knowledge.db sample
```

Результат: 4 совпадения.

Повторный `report` не плодит дубли: `documents = 8`, дублей по `path` нет. Это работает за счёт `UNIQUE(source,path)` и upsert в `drivers/workbench/workbench.py`.

## Runtime-артефакты

`logs/knowledge.db` добавлен в `.gitignore`, потому что это локальная runtime-БД, а не исходный код и не документация.

## Мнение Codex

Это правильный следующий шаг после L2 driver acceptance: не добавлять vector/RAG раньше спроса, а сначала получить простой, проверяемый knowledge workflow, который люди и агенты могут запускать одной командой.
