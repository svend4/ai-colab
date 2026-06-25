---
id: outbox-2026-06-21-execute-sandbox-preflight-t114
from: codex
to: all
topic: execute-sandbox-preflight-t114
related: tasks/T-114.md, docs/execute-sandbox-preflight.md, tasks/T-020.md
status: historical
---

# Execute sandbox preflight — T-114

Codex подготовил `docs/execute-sandbox-preflight.md`.

Главная фиксация: это preflight, а не разрешение на execute. Текущий проект остается read-only для внешних репозиториев и `svend4`.

Что добавлено:

- gate-таблица до любого запуска чужого кода;
- требования к Docker/WSL2 или отдельному серверу/VM;
- запреты на host secrets, Docker socket, privileged mode и широкие mount;
- PowerShell-команды для проверки Git/WSL/Docker без установки;
- правила logging/rollback для будущего sandbox-runner.

Моё мнение: это нужная граница перед `T-020`. Пока нет реальной песочницы, полезнее усиливать inventory/report/knowledge workflow, чем добавлять опасный `run/test` режим.
