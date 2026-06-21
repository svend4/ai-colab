---
id: knowledge-report-artifact-result-2026-06-21
title: Knowledge report artifact result — T-111
status: done
owner: Codex
related: tasks/T-111.md, tools/knowledge.py, reports/README.md, reports/knowledge-fixtures-report.md
---

# Knowledge report artifact result — T-111

Дата: 2026-06-21.

## Что сделано

`tools/knowledge.py report` получил дополнительную опцию:

```powershell
python tools\knowledge.py report data\fixtures --query sample --out reports\knowledge-fixtures-report.md
```

Команда сохраняет тот же Markdown-отчет в файл и продолжает печатать отчет в stdout. Это сохраняет совместимость со старым режимом и добавляет версионируемый artifact для ревью.

## Границы безопасности

- `--out` разрешает писать только внутрь корня репозитория.
- Поддержаны только Markdown-расширения `.md` и `.markdown`.
- `reports/*.md` можно версионировать.
- `logs/*.db` остаются runtime-артефактами и не должны попадать в git.

## Результат проверки

Создан:

- `reports/README.md`;
- `reports/knowledge-fixtures-report.md`.

Содержимое отчета: 8 документов из `data/fixtures`, 4 совпадения по запросу `sample`.

## Мнение Codex

Это правильный следующий шаг для L6. Отчеты становятся не только выводом команды, но и предметом полилога: человек или другой агент может открыть файл, сравнить результат, ответить в `queues/outbox/` или предложить следующую задачу. При этом runtime-база остается локальной и не засоряет историю git.
