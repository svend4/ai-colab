---
id: roadmap-usage-refresh-result-2026-06-21
title: Roadmap and usage refresh — T-118
status: done
owner: Codex
related: tasks/T-118.md, docs/layers-coverage.md, docs/bridge-usage.md, tasks/T-117.md
---

# Roadmap and usage refresh — T-118

Дата: 2026-06-21.

## Что обновлено

Синхронизированы два актуальных входных документа:

- `docs/layers-coverage.md`;
- `docs/bridge-usage.md`.

## Основные изменения

- L2 обновлён до 9 driver manifests.
- Sync MCP `tools/call` acceptance обновлён до `27/27`.
- Добавлен `sqlite` как read-only L2 driver после второй приёмки `T-117`.
- Добавлены FTS5/search, `report --out`, `reports/` и `data/knowledge-corpus/` в L6.
- Добавлен `docs/skills-usage.md` в описание L3 skills.
- Добавлен `docs/execute-sandbox-preflight.md` в L1/runtime boundary.
- `docs/bridge-usage.md` теперь показывает `git-log`, `sqlite`, sqlite-only acceptance и команды `knowledge.py report --out`.

## Что не изменялось

Исторические отчёты и старые review-документы не переписывались. Они остаются хроникой, а актуальный quick-start теперь находится в `docs/bridge-usage.md` и `docs/layers-coverage.md`.

## Мнение Codex

Это важная уборка после нескольких быстрых технических шагов. Когда код идёт быстрее документации, новые агенты начинают видеть старую картину и принимать неверные решения. Теперь быстрый вход снова отражает факты: L2 read-only слой сильнее, L6 получил reproducible reports, но execute всё ещё отдельно и только через песочницу.
