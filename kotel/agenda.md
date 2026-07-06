---
id: kotel-agenda
type: agenda
title: "Kotel agenda — manual pilot"
status: proposed
date: 2026-07-06
author: codex
generated: false
mode: manual-pilot
related:
  - D-035
  - T-273
  - T-276
  - orchestrator-cycle-proposal-2026-07-06
  - closed-loop-agent-cauldron-conveyor
---

# KOTEL AGENDA

> **manual pilot, future generated (T-276 / agenda-generator).** Этот файл ведётся
> вручную только на время пилота. Целевое состояние: генерируется из front-matter
> пакетов, вопросов, демонстраций и полос котла материализатором T-276. Источник
> истины остаётся `tasks/`, `questions/`, `decisions/`, front-matter пакетов и
> reports/.

## 1. Packages

| Package | Status | Risk | Task | Orchestrator | Lead | Zones | Next |
|---|---|---|---|---|---|---|---|
| `PKG-20260706-pilot-t273` | **demonstrated** | medium | T-273 | pool | claude (build/run/report) + codex (safety/package) | inputs: `docs/`, `drivers/`; outputs: `reports/`, `tmp-work/` | решение котла: принять package/agenda-слой (Q1 a/b) или отложить; при принятии — оформить `l2_inventory` в CATALOG |
| `PKG-20260706-codex-delegation-refill` | **agreed** | low | package-only | codex | codex + future `subagent-worker` roles | inputs: `AGENTS.md`, `PROTOCOL.md`, `docs/`, `reports/`, `tools/`; outputs: `reports/`, `queues/outbox/`, `kotel/packages/` | готово к внешнему запуску ролей `governance-scout`, `tooling-scout`, `process-scout`; Codex уже сделал первый integration review |

## 2. Questions For Kotel-Day

### Q1. Принять ли package/agenda-слой после пилота? (проп. §9 a/b — главный вопрос)

- question: Пилот `PKG-20260706-pilot-t273` отработан (см. §3). Принять ли
  оркестраторный цикл — двухслойная модель + пакеты + повестка — как стандартный
  режим работы главных агентов? (проп. `orchestrator-cycle-proposal-2026-07-06` §9)
- variants (из §9 предложения):
  - **a**: принять целиком — оставить `kotel/agenda.md` и шаблон пакета, добавить
    advisory-проверки (после успешного пилота c → a).
  - **b**: принять только §2 (цикл) и §4 (риск-правила) как конвенцию, без новых
    файлов — повестку вести внутри существующего `kotel/`.
  - c: отклонить/переработать слой, продолжить только конвейером.
- recommendation: a — пилот прошёл (оба verify ok, ERROR=0), риск оказался
  управляемым; модель уже де-факто работала, пилот её формализовал.
- evidence: `reports/t273-l2-payload-2026-07-06.md` (payload + вердикт verify);
  `reports/t273-pilot-divergence-reconcile-2026-07-06.md`;
  `docs/orchestrator-cycle-proposal-2026-07-06.md` §9.
- impact: пропускная способность многоагентной работы; нагрузка на человека
  сводится к чтению повестки и котёл-дней.
- deadline: ближайший котёл-день.

### Q2. Who leads the pilot?

- question: Should the first pilot be led by Claude, Codex, or co-led?
- variants:
  - a: Claude leads because `T-273` was already reserved by Claude.
  - b: Codex leads package mechanics while Claude leads L2 content.
  - c: pool/co-lead, with explicit handoff notes.
- recommendation: b, because it separates package mechanics from L2 driver content.
- evidence: `tasks/T-273.md` has `reserved_by: claude`; Codex created package/agenda draft.
- impact: avoids accidental claim conflict.
- deadline: before package status moves from draft to agreed.

### Q3. Which data source for first L2 payload?

- question: What should the first L2 payload inspect?
- variants:
  - a: small local fixture or synthetic corpus;
  - b: small Stefan-approved local folder;
  - c: svend4/infon read-only intake;
  - d: external repo execution.
- recommendation: a or b first; c second; d not allowed without separate execute gate.
- evidence: `T-273`, sandbox policy, external-code safety discussions.
- impact: keeps the first pilot focused on the AI-OS Bridge route, not external execution risk.
- deadline: before execution phase.

### Q4. Which driver route first?

- question: Which driver/tool route should be first?
- variants:
  - a: `files` / `file-inventory` on small fixture or Stefan-approved local folder;
  - b: `data`/`sqlite` on selected local structured file;
  - c: `repo-runner` on local repo inventory;
  - d: gateway/workbench composition.
- recommendation: a first; b/c after route report; d later.
- evidence: driver manifests show `files` is read-only low-risk; `data` has interface drift; `workbench` is safe-write; execute is blocked by D-014.
- impact: keeps pilot narrow and demonstrably safe.
- deadline: before execution phase.

### Q5. Adopt the safety-then-build sequence from divergence reconciliation?

- question: Should the pilot use the sequence proposed in `reports/t273-pilot-divergence-reconcile-2026-07-06.md`?
- variants:
  - a: yes, run `W_safety -> GATE -> W_build -> W_run -> W_verify -> W_report`;
  - b: keep only read-only route planning for now;
  - c: use build-first route and treat safety as post-check;
  - d: pause until formal kotel-day.
- recommendation: a, but only after lead, source path and exact commands are written into the package or a run report.
- evidence: divergence report preserves both variants and turns them into a compatible sequence.
- impact: demonstrates that the closed-loop model handles disagreements without overwriting variants.
- deadline: before package status changes from `draft` to `in-swarm`.

## 3. Demonstrations

| Demo | Status | Report | Notes |
|---|---|---|---|
| T-273 L2 pilot (первый живой груз) | **demonstrated** | `reports/t273-l2-payload-2026-07-06.md` (payload); `reports/t273-pilot-divergence-reconcile-2026-07-06.md` (синтез); `reports/T-273-l2-pilot-safety-gate-2026-07-06.md` (safety) | end-to-end read-only inventory реального бэкапа: `W_safety→GATE→W_build→W_run→W_verify x2→W_report`. Оба verify `ok=true`, `validate.py` ERROR=0. Содержательный итог: бэкап 06-24 отстаёт от канона (121/121 канон-файла отсутствуют). T-273 → status `review`. |

## 4. Manual Pilot Notes

1. This file is not generated yet.
2. Manual edits are allowed only during the pilot.
3. If the package/agenda layer is accepted later, this file should become generated.
4. Source of truth remains `tasks/`, `questions/`, `decisions/`, package front matter and reports.

