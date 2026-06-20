---
id: file-inventory
type: driver
title: File inventory driver — project file map with metadata and risk flags
status: draft
level: L2
mode: read-only
owner: Codex
risk: low
activation: manual
interfaces: [scan, render_markdown]
inputs: [path, base, max-files, include-hidden, hash]
outputs: [file-list, summary, json, markdown]
sandbox: not-required-for-read-only
secrets: forbidden-in-repo
source_last_verified: 2026-06-20
timeout_seconds: 30
max_output_bytes: 1048576
audit: false
related: темы/ai-os-bridge.md, tasks/T-059.md
---

# Driver: file-inventory

## Назначение

Read-only карта файлов проекта или указанной папки: путь, размер, mtime, тип, MIME, risk flags и опциональный SHA-256.

## Контракт

- `scan(path, max_files=1000, include_hidden=false, hash=false, base=None)` — JSON-отчёт.
- `render_markdown(report)` — Markdown-таблица для человека.

## Безопасность

- Только чтение.
- Поддерживает `base_dir` / `--base` для allowed-root.
- Пропускает `.git`, `node_modules`, `__pycache__`, `.venv`, `target`, `build`, `dist`.
- Не читает файлы целиком, кроме опционального hash в пределах лимита.
- Не отправляет данные наружу.

## Путь развития

- L2 draft: no-deps CLI/stdout driver.
- Следующий шаг: runtime-приёмка после `T-039`.
- После приёмки решить, нужен ли merge с `drivers/files/inventory.py`.

