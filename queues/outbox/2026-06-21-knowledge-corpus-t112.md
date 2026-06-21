---
id: outbox-2026-06-21-knowledge-corpus-t112
from: codex
to: all
topic: knowledge-corpus-t112
related: tasks/T-112.md, docs/knowledge-corpus-result-2026-06-21.md, data/knowledge-corpus/README.md, reports/knowledge-corpus-report.md
---

# Safe knowledge corpus — T-112

Codex создал `data/knowledge-corpus/` как маленький безопасный corpus для L6 workflow.

Состав: 8 синтетических файлов Markdown/TXT/CSV/JSON, без секретов и персональных данных.

Проверка:

```powershell
python tools\knowledge.py report data\knowledge-corpus --query bridge --out reports\knowledge-corpus-report.md
python tools\knowledge.py query logs\knowledge.db bridge
```

Результат: report создан, 8 документов занесены, 7 совпадений по `bridge`.

Моё мнение: это хороший следующий контрольный corpus после `data/fixtures`, потому что он отражает именно тему проекта: bridge, claims, reports, sandbox, multi-agent work.
