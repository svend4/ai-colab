---
id: outbox-2026-06-23-top-conveyor-status
status: proposed
agent: codex
related: T-163, tools/conveyor.py, tools/top.py, docs/workflow-conveyor-policy.md
---

# Top conveyor status — отчёт Codex

Codex поднял runtime-надзирателя workflow-конвейера в верхний слой:

```powershell
python tools\top.py conveyor
python tools\top.py conveyor --json
python tools\conveyor.py next
```

Смысл: человек и агент теперь видят `REFILL` / `PROCESS` / `IDLE` через ту же панель, где уже есть `status`, `health`, `agent-start`, `subagent-handoff` и `work-mode`.