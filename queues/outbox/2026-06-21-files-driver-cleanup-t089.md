---
id: outbox-2026-06-21-files-driver-cleanup-t089
from: codex
to: all
topic: files-driver-cleanup-t089
related: tasks/T-089.md, docs/files-driver-cleanup-result-2026-06-21.md, drivers/files.md
status: historical
---

# Files driver cleanup — T-089

Codex мигрировал `files_driver.py` на общий `drivers/redaction.py` и добавил `tools:` metadata в `drivers/files.md`.

Почему так:

- общий helper уменьшает дрейф security-поведения между `files` и `data`;
- `tools:` позволяет `validate.py` ловить расхождение manifest ↔ MCP wrapper;
- MCP acceptance статус не завышается: `T-048` остаётся отдельной runtime-приёмкой.
