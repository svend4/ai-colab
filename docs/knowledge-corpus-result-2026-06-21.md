---
id: knowledge-corpus-result-2026-06-21
title: Safe knowledge corpus result — T-112
status: done
owner: Codex
related: tasks/T-112.md, data/knowledge-corpus/README.md, reports/knowledge-corpus-report.md, tools/knowledge.py
---

# Safe knowledge corpus result — T-112

Дата: 2026-06-21.

## Что сделано

Создан безопасный локальный corpus:

```text
data/knowledge-corpus/
```

Внутри 8 синтетических файлов: Markdown, TXT, CSV и JSON. Корпус не содержит персональных данных, секретов, токенов, чужого исполняемого кода или внешних материалов.

## Проверка

Команда:

```powershell
python tools\knowledge.py report data\knowledge-corpus --query bridge --out reports\knowledge-corpus-report.md
```

Результат:

- занесено документов: 8;
- типы: 4 Markdown, 2 TXT, 1 CSV, 1 JSON;
- риск: 8 low;
- query `bridge`: 7 совпадений в report;
- создан `reports/knowledge-corpus-report.md`.

Дополнительная проверка:

```powershell
python tools\knowledge.py query logs\knowledge.db bridge
```

Результат: 7 совпадений.

## Мнение Codex

Этот corpus нужен не как “данные ради данных”, а как стабильный тестовый слой для будущих агентов. Теперь можно менять `tools/knowledge.py`, FTS5, reporting или corpus rules и сразу видеть, сломался ли базовый сценарий ingest → query → report.
