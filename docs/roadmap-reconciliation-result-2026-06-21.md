---
id: roadmap-reconciliation-result-2026-06-21
title: Roadmap reconciliation result — T-110
status: done
owner: Codex
related: tasks/T-110.md, tasks/T-048.md, tasks/T-051.md, docs/layers-coverage.md
---

# Roadmap reconciliation result — T-110

Дата: 2026-06-21.

## Что исправлено

Синхронизированы старые blocker-формулировки и roadmap после T-100/T-103/T-107/T-109.

Изменения:

- `T-048` больше не выглядит заблокированной: добавлен reconciliation-блок, что `files` покрыт sync MCP `tools/call` acceptance.
- `T-051` больше не выглядит заблокированной: добавлен reconciliation-блок, что `repo-runner` покрыт sync MCP `tools/call` acceptance.
- `docs/layers-coverage.md` обновлён до текущего состояния: 8 драйверов, sync acceptance 23/23, L3 project skills есть, L6 knowledge workflow есть.

## Текущая честная формула

Read-only средний слой работает как прототип:

- L2: driver/MCP sync acceptance 23/23;
- L3: project skills оформлены;
- L6: SQLite workbench + knowledge workflow.

Но execute/svend4 остаётся отдельной темой с обязательной песочницей. Официальный async MCP stdio client в проблемной Windows-среде остаётся compatibility-задачей, а не блокером регулярной приёмки.
