---
id: files-driver-cleanup-result-2026-06-21
title: Files driver cleanup result — T-089
status: done
owner: Codex
related: tasks/T-089.md, drivers/files.md, drivers/files/files_driver.py, drivers/redaction.py
---

# Files driver cleanup result — T-089

Дата: 2026-06-21.

## Что изменено

- `drivers/files/files_driver.py` больше не содержит собственные `SECRET_RE`/`AWS_KEY_RE`.
- Redaction теперь идёт через общий `drivers/redaction.py`, как у `data` driver.
- `drivers/files.md` получил `tools: [list_files, read_file, search, summarize]`.
- Устаревшая фраза про `draft` заменена на актуальный статус: files driver логически готов, а MCP acceptance остаётся отдельной runtime-задачей.

## Мнение Codex

Это правильное упрощение: один security-helper лучше двух одинаковых regex-копий. Для большого числа агентов это снижает риск, что один driver начнёт маскировать секреты иначе, чем другой.

Граница ответственности не изменилась: `files` остаётся read-only. Эта задача не должна автоматически разблокировать `T-048`, потому что `T-048` про MCP `call_tool` acceptance в проблемном Windows stdio runtime.
