---
id: governance-proposals-2026-06-23
type: topic
title: Котёл-предложения (D-018) — диспозиция 7 flow-сирот + конвенция last_verified
status: proposed
date: 2026-06-23
related: [Q-016, D-004, D-008, D-013, D-015, D-018, assurance-hardening-plan-2026-06-23, instruction-assurance]
---

# Котёл-предложения (D-018) — поверхность инструкций + актуальность

Два предложения для **котла (D-018, не solo)**, проверены против файлов. Источник: нода флота
`governance-bundle` (по находкам `assurance.py` section_flow/currency).

## 1. Диспозиция 7 «висячих» accepted-решений (flow-сироты)

`assurance.py` section_flow находит 7 accepted-решений, не упомянутых в поверхности инструкций
(13 файлов реестра `instructions.py`). Предложение — что вплести, что оставить фоном:

| Решение | Что это | Действие |
|---|---|---|
| **D-008** (граница D-003: что есть значимая правка) | D-003 уже густо цитируется, но его операт. граница не заякорена — **приоритет** | **вплести** (рядом с D-003 в AGENTS.md/PROTOCOL.md) |
| **D-004** (метод решений: варианты→±→рекоменд→голоса→итог) | активная процедура перед «answered» | **вплести** (PROTOCOL.md, секция questions/decisions) |
| **D-009** (онбординг агента: self-register → maintainer-approval) | как новый агент входит | **вплести** (docs/agent-onboarding.md + AGENTS.md) |
| **D-002** (один файл на сообщение для крупных тем) | правило уже в прозе, но без якоря D-002 | **вплести** (тег рядом с фразой в AGENTS.md/PROTOCOL.md) |
| D-001 (Markdown как основной формат) | аксиома, уже живёт везде | фоном |
| D-010 (AI-OS Bridge: drivers/ + L2 PoC) | трек архитектуры drivers/, не per-task | фоном (темы/ai-os-bridge + driver-доки) |
| D-013 (driver schema v1) | де-факто спека за drivers/SCHEMA.md | фоном (cross-link из SCHEMA.md) |

Правки поверхности (AGENTS.md/PROTOCOL.md/onboarding) — **только после ратификации** (D-006/D-018),
это базовые общие файлы.

## 2. Конвенция `last_verified` + миграция S0

Поднять драйверный `source_last_verified` (происхождение: D-013:40 обязательное поле; семантика
D-015:42-43 — видимый след сверки) до ключа **`last_verified: YYYY-MM-DD`** на accepted-решениях/политиках.
Тот же ISO-формат, та же семантика «штамп при сверке», тот же парсер (`_canon.parse_front_matter`).

**Правила (из `assurance-hardening-plan-2026-06-23.md`):**
1. **Штамп СЕГОДНЯ (2026-06-23), не back-date** — back-date либо лжёт, либо мгновенно зажигает freshness ~23×;
   штамп сегодня сбрасывает SLA-часы в 0.
2. **Только accepted/policy** — `assurance.py:203` уже гейтит на `status==accepted`; не трогать proposed
   D-014/D-019/D-020.
3. **Один SLA на корпус** — 90д governance / 30д drivers; починить рассинхрон (`assurance.py:361` дефолт
   `--max-age=180` против `driver-safety-policy.md:14`=30).
4. **Лестница warn→block** — advisory через S1-S3; `assurance currency --strict` в `merge_gate.gate_stages`
   только на S4 (после закрытия всех gap + один 90д квартал).

**Миграция (S0, один governance-коммит, без кода):** штамп `last_verified: 2026-06-23` на **20 accepted-
решениях** (D-001..D-013, D-015..D-018, D-021..D-023 — все `last_verified=NONE`) + **4 политики**
(`parallel-work-policy`, `promotion-rules`, `workflow-orchestration-policy`, `instruction-assurance` —
зашиты в `assurance.py:181-184`). Реализация — после ратификации.
