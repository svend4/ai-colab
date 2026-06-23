---
id: concept-map
type: doc
title: Концептуальная карта — навигируемый индекс концептов, связей и держащих доков
status: proposed
date: 2026-06-23
related: [engine-subsystems-overview-2026-06-23, orchestration-architecture-2026-06-23, workflow-conveyor-policy, finder-solver-pipeline-methodology, nested-orchestration-3to1, blocks-layer, workspace-pyramid-levels, parallel-work-policy, instruction-assurance, agent-capacity-methodology]
---

# Концептуальная карта проекта

> **Навигируемый индекс концептов.** Узлы = концепты (FINDER-SOLVER, конвейер, бригады 3:1, блоки,
> пирамида, adoption, friction, two-spine, cohort/flow и др.); рёбра = зависимости/ссылки между ними.
> Для каждого концепта указан **держащий док** (канон) и **код**, если есть. Цель карты двойная:
> (1) дать одну точку входа в концептуальный слой репозитория; (2) **вылечить orphan-методички** —
> доки без входящих ссылок (`adoption`, `blocks-layer`, `finder-solver-pipeline-methodology`,
> `workspace-pyramid-levels`) получают inbound-ссылку отсюда и перестают быть сиротами (детектор
> `tools/adoption.py --list orphan`).

Карта read-only и описательная: она **не** дублирует содержание доков, а связывает их. Канон по каждому
концепту — в его держащем доке; здесь — навигация и рёбра. Статусы концептов в основном `proposed`
(ещё не через котёл `D-018`), но большинство механизмов уже подкреплены кодом.

## 1. Граф концептов (ASCII)

```
                          ┌──────────────────────── ОРКЕСТРАЦИЯ ────────────────────────┐
                          │                                                              │
   FINDER ──найдено──► РОУТЕР (я) ──отобрано──► SOLVER                                    │
   (широкий скан)       триаж/дедуп/приоритет   (широкое решение)                         │
        │                    │                       │                                    │
        │ зацикливает        ▼                       ▼                                    │
        └───────────► КОНВЕЙЕР (поток воркфлоу) ──► БРИГАДА {N producer + 1 integrator} ──┤
                          │  ▲ надзиратель                  │ фрактал 3:1                  │
                          │  conveyor.py                    ▼                              │
                          │                          ВЛОЖЕННОСТЬ 3:1 (reduce-дерево)       │
                          ▼                                                                │
                    ПОЛОСА КОММИТА (agent-capacity) ◄─── единственная серийная точка ──────┘
                          │
                          ▼
                  ┌─ COLLAB-SAFETY ─┐   ┌─ DRIVERS / AI-OS BRIDGE ─┐   ┌─ ASSURANCE (Q-016) ─┐
                  │ cohort · friction│   │ driver-схема · gateway   │   │ instruction-assurance│
                  │ flow · ownership │   │ read-only intake · L2    │   │ two-spine · trace    │
                  │ L0/L1 изоляция   │   │ порталы (knowledge)      │   │ adoption · blocks    │
                  └────────┬─────────┘   └────────────┬─────────────┘   └──────────┬─────────┘
                           └──────────── всё лежит в ───┴── ПИРАМИДЕ L1..L4 ───────┘
                                            core/ portals/ collab/ sandbox/
```

Сквозная нить движка (`engine-subsystems-overview-2026-06-23`): **advisory-по-умолчанию,
strict-по-триггеру** — дешёвый наблюдательный дефолт, ужесточаемый до блокирующего только по явному
триггеру.

## 2. Концепты, держащие доки, код

| Концепт | Что это (одной строкой) | Держащий док (канон) | Код |
|---|---|---|---|
| **FINDER → роутер → SOLVER** | Два больших воркфлоу (поиск проблем / решение) с оркестратором-барьером в середине | `docs/finder-solver-pipeline-methodology.md` | — (поверх conveyor) |
| **Конвейер воркфлоу** | ≥2 воркфлоу как ПОТОК, а не партия; запуск со сдвигом, возврат-к-первому | `docs/workflow-conveyor-policy.md`, свод `docs/orchestration-architecture-2026-06-23.md` | `tools/conveyor.py` |
| **Надзиратель конвейера** | Внешний глаз: REFILL/PROCESS/IDLE, чтобы не осушить in-flight до нуля | `docs/workflow-conveyor-policy.md` §3-ter | `tools/conveyor.py status` |
| **БРИГАДА {N producer + 1 integrator}** | Атомарная ячейка параллелизма: produce+integrate в один готовый артефакт | `docs/orchestration-architecture-2026-06-23.md` §БРИГАДА | (Workflow, 1-уровень вложения) |
| **Вложенность 3:1 (reduce-дерево)** | Продюсеры → бригады → дирижёры → оркестр; новый уровень при детях >3 | `docs/nested-orchestration-3to1.md` | `tools/conveyor.py plan N` |
| **Полоса коммита (agent-capacity)** | Узкое место — не воркеры, а сколько успеваешь извлечь+закоммитить | `docs/agent-capacity-methodology.md` | — (binds, не agents) |
| **adoption** | Применение, не накопление: dormant-инструменты, doc-only решения, orphan-доки | `темы/adoption-statistics-2026-06-23.md` | `tools/adoption.py` |
| **Блок-слой (blocks)** | Сборка проверенных примитивов в кластерные блоки, запускаемые одной командой | `docs/blocks-layer.md` | `tools/blocks.py`, `tools/adoption.py` |
| **friction** | Read-only ledger повторяющихся проблем (F-001..F-020), advisory-сигнал | `docs/friction-retrospective-2026-06-22.md`, `friction-ledger/playbook.md` | `tools/friction.py` |
| **cohort / flow** | Ownership-aware отгрузка когортой (L0 ship / L1 worktree) + git-flow гейт | `docs/parallel-work-policy.md`, `docs/commit-stream-policy.md` | `tools/cohort.py`, `tools/flow.py`, `tools/ownership.py` |
| **L0/L1 изоляция** | Бинарная модель: общее дерево + commit_lock (L0) ↔ per-agent worktree (L1) | `docs/parallel-work-policy.md`, `D-021..D-023` | `tools/commit_lock.py`, `tools/worktree.py`, `tools/merge_gate.py` |
| **two-spine / instruction-trace** | Доказуемое применение инструкций: shared surfaces-ключ + read-only trace база→вершина | `docs/instruction-assurance.md` | `tools/instructions.py`, `tools/assurance.py` |
| **Assurance (Q-016)** | Апекс-дашборд «инструкции применяются и свежи» + лестница S0→S4 | `docs/instruction-assurance.md`, `q016-assurance-state-2026-06-23` | `tools/assurance.py` |
| **Drivers / AI-OS Bridge** | Проверяемый driver-манифест + read-only intake + L2-gateway | `docs/agent-layer-design.md`, `темы/drivers-subsystem-state-2026-06-23.md`, `D-010/D-013` | `drivers/*`, `tools/validate.py` |
| **Порталы (knowledge engine)** | Драйверы → generic engine → тематические L2-порталы без правки core | `docs/middle-layer-guide.md`, `D-016` | `tools/knowledge.py`, `tools/portal.py` |
| **Пирамида L1..L4** | core/ (ядро) · portals/ (чистовые домены) · collab/ (история) · sandbox/ (хаос-вход) | `docs/workspace-pyramid-levels.md`, `docs/promotion-rules.md` | `core/ portals/ collab/ sandbox/` |

## 3. Рёбра (зависимости и ссылки)

Читать «A → B» как «A опирается на B / ссылается на B / является слоем над B».

- **FINDER-SOLVER → конвейер.** FINDER/SOLVER — это два больших конвейерных контура; роутер-барьер
  живёт поверх потоковой механики (`finder-solver-pipeline-methodology.md` §6 регистрирует
  `conveyor.py launch`).
- **Конвейер → надзиратель → полоса коммита.** Конвейер держит поток; надзиратель сигналит дозалив;
  ширина потока ограничена не воркерами, а **полосой коммита** (`agent-capacity-methodology.md`).
- **Конвейер → БРИГАДА → вложенность 3:1.** Бригада — атомарная единица конвейера; когда бригад >3,
  фрактально появляется слой дирижёров (`nested-orchestration-3to1.md` §2).
- **БРИГАДА / конвейер → cohort/flow → L0/L1 изоляция.** Серийная точка (commit) проходит через
  `cohort.py guard` → L0 ship или L1 worktree+merge_gate; ownership-классификатор решает уровень.
- **cohort/flow → friction.** `friction.py` сигналит (advisory), `cohort.py` исполняет; F-020/gate-poison
  — общий триггер (`engine-subsystems-overview` §1).
- **Assurance → two-spine → adoption → блоки.** Assurance доказывает применение инструкций; two-spine/trace
  даёт read-only трассу база→вершина; `adoption.py` находит, что НЕ применяется; `blocks.py` собирает
  проверки в исполняемые кластеры (рекурсивное само-улучшение: `blocks-layer.md`).
- **Drivers / Bridge → порталы.** Драйверы переиспользуются движком `knowledge.py`, порталы (`portal.py`,
  D-016) добавляют домен как данные поверх ядра.
- **Всё → Пирамида.** Каждая подсистема приписана к уровню: code/tools — кандидаты L1 `core/`; порталы —
  L2; темы/задачи/решения/streams — L3 `collab/`; внешний вход — L4 `sandbox/` (`workspace-pyramid-levels.md`).

## 4. Лечение orphan-методичек

`tools/adoption.py --list orphan` помечает доки с 0 входящих ссылок по имени файла. Эта карта даёт им
inbound-ссылку и возвращает в навигируемый граф:

- `docs/blocks-layer.md` — связан из §2 (блок-слой) и §3 (adoption→блоки).
- `темы/adoption-statistics-2026-06-23.md` / `tools/adoption.py` — связаны как держащий док концепта adoption.
- `docs/finder-solver-pipeline-methodology.md` — корень оркестрационного контура §1.
- `docs/workspace-pyramid-levels.md` — концепт пирамиды §2, ребро «всё → пирамида» §3.

Поддержание карты: при добавлении нового концепт-дока — добавить строку в §2 и ребро в §3, чтобы
новый док сразу имел inbound-ссылку и не становился сиротой.
