---
id: finder-frontier-2026-06-23
type: theme
title: FINDER фронтира — рост-бэклог реально-нерешённого (37 пунктов)
status: proposed
date: 2026-06-23
verified_against: 436d5e2
---

FINDER-фронтир: 37 подтверждённых непостроенных пунктов, ранжированных как forward-backlog РОСТА (не cleanup). Полный файл записан в topics/finder-frontier-2026-06-23.md (status:proposed). Ранг = severity x (1/effort): high=3/med=2/low=1; S=1.0/M=0.5/L=0.33/XL=0.2.

РАНЖИРОВАННЫЙ BACKLOG (score|sev|eff|kind|title|next):
P1 2.0 high M untested-risk | agent_queue fencing/complete/fail/release без теста | test
P2 2.0 med S mcp-bridge | T-174 ложно-зелёный status:done | build
P3 2.0 med M execute-sandbox | Gate 9 fake-sandbox строковый enum-чек | build
P4 1.5 high L execute-sandbox | Run-plan нет парсера/валидатора/исполнителя | build
P5 2.0 high M execute-sandbox | Gate 4/5 mount/network preflight-чекер | build
P6 1.0 med S execute-sandbox | Gate 10 human-first-run нет механизма | build
P7 1.0 med S untested-risk | permissions.match() glob без теста | test
P8 1.0 med S untested-risk | risk_gate тиринг без теста | test
P9 1.0 med M execute-sandbox | Gate 6 лимиты enforcement нет | build
P10 1.0 med M execute-sandbox | Gate 7/8 audit+rollback нет runner'а | build
P11 1.0 med M execute-sandbox | preflight-probe команда 10 гейтов go/no-go | build
P12 1.0 med M pyramid-L3L4 | Второй core-export knowledge.py L2->L1 | build
P13 1.0 med M pyramid-L3L4 | L2->L1 move-путь не прогнан | test
P14 1.0 med M mcp-bridge | file-inventory draft@L2 без mcp_server.py | build
P15 1.0 med M capability-gap | RE-MEASURE фаза 5 нет машинного дельта | build
P16 1.0 med M capability-gap | Auto-archive stale streams sweep нет | build
P17 1.0 med M frontier-question | Workflow backlog rescan tool | build
P18 1.0 low S execute-sandbox | Gate 9 позитивный путь end-to-end | test
P19 1.0 low S pyramid-L3L4 | Два L2-портала без workflows.md | build
P20 1.0 low S untested-risk | dispatch DAG без теста | test
P21 1.0 low S untested-risk | metrics сводка без теста | test
P22 1.0 low S untested-risk | drivers_catalog без теста | test
P23 1.0 low S untested-risk | capabilities без теста | test
P24 1.0 low S untested-risk | demo_bridge без теста | test
P25 1.0 low S frontier-question | DOC_CONSENSUS_AGENT runtime recipe | build
P26 0.66 med L pyramid-L3L4 | НОВЫЙ L3-слой над 3 порталами | design
P27 0.66 med L mcp-bridge | codex-local делегирование Codex | design
P28 0.66 med L capability-gap | Детекторы не чинят авто (safe-auto-apply) | design
P29 0.66 med L capability-gap | Петля без авто-триггера | design
P30 0.66 high XL driver-gap | mode:execute непостроен runner L3/L4 | design
P31 0.66 high XL execute-sandbox | Sandbox-runner Gate 3 реальная изоляция | design
P32 0.66 high XL mcp-bridge | Мост AI-OS без execute-режима | design
P33 0.66 high XL mcp-bridge | Sandbox-runner для svend4 репо | design
P34 0.5 low M frontier-question | instruction_freshness_check.py | ratify
P35 0.5 low M frontier-question | MCP async stdio WinError 5 фикс | ratify
P36 0.4 med XL capability-gap | Cross-repo/multi-repo концепт нулевой | design
P37 0.33 low L frontier-question | Q-010 темы->topics миграция | ratify

ПО KIND:
execute-sandbox(10): крупнейший слой, в коде только S1/S3/S7 read-only intake + enum-чек; runner НЕ построен. Порядок P3->P5->P4->P6/P9/P10/P11->P18, сходится к P31(ядро); P4/P5/P6/P9/P10 кормят runner; P11 агрегирует гейты.
untested-risk(8): generate/pipeline УЖЕ покрыты (не gaps). Без теста: agent_queue/permissions/risk_gate/dispatch/metrics/drivers_catalog/capabilities/demo_bridge. P1 верх по concurrency; P22/P23 косвенно прикрыты drift_check.
capability-gap(5): P15 замкнуть RE-MEASURE (числа в --json), P16 stream.py archive/sweep — build окупаемы. P28/P29/P36 design (часть by-design отложена).
pyramid-L3L4(4): P12 reuse-гейт 2/3 блокер verification-ref; P13 move не исполнен (только export-copy); P26 неподъём намеренный ждёт D-018; P19 template-completeness. P12 разблокирует P13.
mcp-bridge(4): P2 ТОП-3; P14 driver-gap CATALOG vs код; P27 high-risk ждёт песочницы; P32/P33 XL пересекаются с P31 (общий runner).
driver-gap(1): P30 тот же execute-runner что P31.
frontier-question(5): P17 авто-refresh бэклога; P25 seam готов рецепт env нет; P34/P35/P37 ratify (currency-migration/wontfix-decision/D-008).

ТОП-3 СТРОИТЬ ПЕРВЫМ:
1. P1 agent_queue fencing-тест (test, 2.0) — единственная защита от затирания чужого done/failed (require_holder/claim_id-fencing) без теста, хотя близнец pipeline.py имеет test_pipeline_fencing.py; concurrency-риск потери чужой работы.
2. P2 T-174 статус-фикс (build, 2.0) — status лжёт на 4 поверхностях (frontmatter/index.json/TASKS.md vs Result+failed-queue), подрывая трекинг блокера; дешёвый data-integrity фикс.
3. P3 Gate 9 anti-fake-sandbox (build, 2.0) — гейт проверяет ярлык sandbox:docker а не механизм; probe runner-бэкенда даёт реальную проверку и фундамент для всего execute-слоя.
Затем: тесты P7/P8 и P20-P24 (S); execute-sandbox цепочка P4-P11 к runner'у (P31/P30/P33); RSI P15/P16 (M) отдельной волной; XL-design (P31/P32/P33/P36) до кода.