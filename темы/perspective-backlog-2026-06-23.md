---
id: perspective-backlog-2026-06-23
type: topic
title: Перспективный бэклог — ранжированная очередь следующих волн конвейера (самопополнение)
status: proposed
date: 2026-06-23
related: [workflow-conveyor-policy, Q-016, Q-017, Q-013, Q-010, Q-009]
---

# Перспективный бэклог конвейера

> Стоячий источник будущих заданий (см. `docs/workflow-conveyor-policy.md` §3-bis): пополняется
> рекуррентным воркфлоу-сканером поверхностей (открытые `Q-*`, `todo`, находки `assurance.py`,
> разделы «Дальше»). Чтобы конвейер не осушался — следующая волна берётся отсюда.

## Состояние конвейера и что запускать дальше

Проверил репозиторий: assurance.py = ATTENTION (3 находки: currency-20, orphan-L1-12, flow-7); friction.py без gate-poison-пробы; doc_consensus.py без --semantic; instruction_freshness_check.py и promotion_coverage.py не построены; pre-commit hook существует (значит claim в parallel-work-policy устарел); открыто 5 вопросов (Q-009/010/013/016/017). В TASKS.md форвард-работы нет — всё живёт в котле.

После дедупликации 25 сырых пунктов свернулись в 13 ранжированных. Самые ценные независимые сборки можно запускать прямо сейчас, чтобы держать 2-4 потока в работе:

1. Q-016 done-gate (rank 1, S, build) — самый дешёвый высокорычажный фикс: cmd_done (pipeline.py:342-343) только печатает WARN, не зовёт check_report. Закрывает дыру «формальный evidence».
2. friction F-020 gate-poison (rank 2, S, build) — детектор слеп к самому опасному состоянию shared-tree (класс инцидента T-150). Независим.
3. Q-017 semantic doc-merge (rank 3, M, build) — направление ратифицировано, спека готова, остаётся реализация + fixture «одна идея — разные слова».

Эти три не зависят друг от друга и покрывают разные подсистемы (gate / friction / doc-merge), поэтому параллелятся без конфликта по файлам. Четвёртым в волну — портал-наполнение orphan-L1 (rank 4, build), независимое и закрывающее главную машинную находку assurance; оно же разблокирует Wave-3 checker (rank 9). Параллельно дешёвый currency-rollout (rank 6) разблокирует Wave-2 freshness (rank 7). Решенческие пункты (Q-010 rename, Q-013 onboarding, gate-poison contract, two-commit divergences, T-020) идут через котёл/голосование отдельным decision-треком и не блокируют сборки — держим их параллельно, а не в основном конвейере.</answer_md>
</invoke>

## Готовы к запуску (независимые, по out-degree)

1. Currency convention: adopt last_verified across accepted docs
2. Populate L2 portals for orphan-L1 core modules
3. Q-016 done-gate: wire check_report into cmd_done
4. friction F-020 gate-poison detector
5. Q-017 semantic doc-merge (report --semantic)
6. Instruction check-report: verify referenced files/commands exist

## Ранжированный бэклог

| # | Тема | Value | Effort | Вид | Зависит |
|---|---|---|---|---|---|
| 1 | Q-016 done-gate: make pipeline.py cmd_done verify applied-instruction evidence (call check_report, block on empty/formal evidence for service/governance tasks) | high | S | worktree-build | none |
| 2 | Wire gate-poison / validate-ERROR probe into friction.py as the F-020 detector | high | S | worktree-build | none |
| 3 | Q-017 semantic doc-merge: add report --semantic to doc_consensus.py (mechanical high-thr pre-cluster + subprocess agent-pass over residue, _merge by unit-id, status:proposed output) + 'one idea, different words' fixture | high | M | worktree-build | none |
| 4 | Populate L2 portals for the 12 orphan-L1 core modules (only portals/example/portal.md exists), closing the highest-signal assurance finding | high | M | worktree-build | none |
| 5 | Instruction-assurance follow-up: extend instructions.py check-report to verify referenced files and check-commands actually exist (not just token presence) | medium | S | worktree-build | none |
| 6 | Currency convention: adopt last_verified front-matter across the 20 accepted decisions/policies that lack it, moving currency-gate from observe to enforce | medium | S | cauldron-task | none |
| 7 | Assurance Wave-2: build tools/instruction_freshness_check.py and integrate into drift_check.py + capabilities.json to catch stale-but-present instructions | medium | M | workflow | Currency convention: adopt last_verified across accepted docs (rank 6) |
| 8 | Update stale 'not yet implemented' claims in docs/parallel-work-policy.md (stream.py check and selective-add pre-commit hook both already shipped) | medium | S | worktree-build | none |
| 9 | Assurance Wave-3: build tools/promotion_coverage.py to verify L2 portals actually use L1 core knowledge (reverse upward-flow check) | medium | L | workflow | Populate L2 portals for orphan-L1 core modules (rank 4) |
| 10 | reconcile_state.py fix subcommand: implement stage-2 reconcile (derive state from queues/done snapshots) instead of the current report-only stub | medium | M | worktree-build | none |
| 11 | Flow orphans: decide whether to wire the 7 dangling accepted decisions (D-001/002/004/008/009/010/013) into the instruction surface or mark them background-only | medium | S | cauldron-task | none |
| 12 | Decision batch (vote-gated): Q-010 temy->topics rename, Q-013 onboarding/manual roadmap points, gate-poison shared-gate contract (S1 quarantine), two-commit worktree-timeline divergence (D-018) | medium | M | decision | none |
| 13 | Q-009/T-020 svend4 source access: decide A (provide read-only source), B (generic local-repo inventory), or C (close as blocked/orphan) - the one remaining blocked task | low | S | decision | Stefan provides read-only svend4 source or chooses B/C |

