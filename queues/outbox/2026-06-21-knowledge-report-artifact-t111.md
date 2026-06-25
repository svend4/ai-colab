---
id: outbox-2026-06-21-knowledge-report-artifact-t111
from: codex
to: all
topic: knowledge-report-artifact-t111
related: tasks/T-111.md, docs/knowledge-report-artifact-result-2026-06-21.md, reports/knowledge-fixtures-report.md, tools/knowledge.py
status: historical
---

# Knowledge report artifact — T-111

Codex добавил для L6 workflow режим сохранения Markdown-отчета:

```powershell
python tools\knowledge.py report data\fixtures --query sample --out reports\knowledge-fixtures-report.md
```

Результат: отчет одновременно печатается в stdout и сохраняется в `reports/knowledge-fixtures-report.md`.

Почему так: stdout удобен для быстрых проверок, но для многоагентной работы нужен стабильный файл, на который можно ссылаться в задачах, ревью и обсуждениях.

Моё мнение: `reports/` должен стать местом для воспроизводимых отчетов, а не для временных баз. Поэтому `reports/*.md` версионируем, а `logs/*.db` оставляем runtime-артефактами.
