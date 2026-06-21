---
id: layer-coverage-update-result-2026-06-21
title: Layer coverage update result — T-096
status: done
owner: Codex
related: tasks/T-096.md, docs/layers-coverage.md, docs/middle-layer-guide.md, drivers/CATALOG.md
---

# Layer coverage update result — T-096

Дата: 2026-06-21.

## Что обновлено

`docs/layers-coverage.md` оставлен каноническим источником нумерации L0-L7, но его таблица покрытия обновлена под фактическое состояние после T-087..T-095.

Ключевые уточнения:

- L2 больше не описан как `MCP-серверов нет`: есть 7 driver manifest, MCP wrappers/tools-list контур, sync probe, manifest-tools validation и gateway in-process regression.
- L6 больше не описан как только спроектированная схема: `workbench` SQLite driver, ingest/search tests, CLI acceptance и `gateway.memory_query` уже есть.
- L1 получил честную оговорку: Python/PowerShell работают, но стандартный Windows `tempfile` и `asyncio` stdio pipes остаются runtime-шероховатостями.
- Рекомендуемый порядок сдвинут с “сделать первый MCP PoC” на “acceptance hardening → knowledge workflow → project skills → Docker/WSL2 sandbox”.

## Мнение Codex

Это важная синхронизация терминологии. После последних задач проект уже не находится в стадии “только концепция”; он находится в стадии рабочего read-only прототипа среднего слоя. Но называть его зрелой платформой рано: `tools/call` acceptance, knowledge workflow и песочница для execute ещё не закрыты.
