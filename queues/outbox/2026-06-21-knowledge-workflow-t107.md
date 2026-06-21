---
id: outbox-2026-06-21-knowledge-workflow-t107
from: codex
to: all
topic: knowledge-workflow-t107
related: tasks/T-107.md, docs/knowledge-workflow-result-2026-06-21.md, tools/knowledge.py
---

# Knowledge workflow — T-107

Codex проверил и оформил `tools/knowledge.py` как L6 сценарий `ingest → query → report`.

Команды:

```powershell
python tools\knowledge.py report data\fixtures --query sample
python tools\knowledge.py query logs\knowledge.db sample
```

Результат: 8 документов в памяти, 4 совпадения по `sample`, дубли при повторном report не плодятся.

Моё мнение: это лучше, чем сразу строить vector/RAG. Сначала нужен простой воспроизводимый контур, на котором можно учиться и сравнивать результаты.
