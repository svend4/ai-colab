---
title: Состояние движка — карта для человека и агента
date: 2026-06-22
audience: человек | агент
related: docs/agent-onboarding.md, docs/parallel-work-policy.md, docs/workspace-pyramid-levels.md, core/engine-manifest.md
---

# Движок сейчас: что это и как им пользоваться

Документ — точная карта ТЕКУЩЕГО состояния (что есть на диске на 2026-06-22). Цель: новый агент или человек за 5 минут понимает, ЧТО есть и КАК этим пользоваться. Для входа достаточно одной команды: `python tools/onboard.py [agent]` или панели `python tools/top.py buttons`.

## Что это (середина пирамиды: ОС ↔ слой ↔ агенты/люди)

Это **средний слой** между операционной системой/git (низ) и агентами/людьми (верх). Сам движок — это **одноранговый набор инструментов в `tools/`** (нет иерархии исполнения) плюс **канон Markdown-реестров** (`tasks/`, `decisions/`, `questions/`, генерируемые `STATUS.md`/`board.md`) плюс **политики** (`PROTOCOL.md`, `AGENTS.md`, `docs/*-policy.md`, `decisions/D-016..D-022`).

Ключевые свойства:
- **READ-ONLY по умолчанию.** Любая команда с побочным эффектом требует флага `--run`.
- **Явная синхронизация вместо иерархии:** advisory commit-lock, merge-gate, fencing claim_id в очереди.
- **Канон — единственный источник правды:** навигационные таблицы (`STATUS.md`, `board.md`) генерируются из front-matter через `tools/generate.py`; рассинхрон ловит `tools/drift_check.py`.
- **Домен — плагин, не код ядра** (D-016): универсальное ядро + тематические порталы (модель «Википедия»).
- **Портируемое ядро:** `core/engine-manifest.md` описывает 10-файловый движок координации (validate/generate, next_id/commit_lock/pipeline/dispatch/merge_gate + тесты) — D-021 Q2 export.

## Группы инструментов (36 основных + ~22 теста `test_*.py`)

| Группа | Инструменты | Одна-кнопка-команда | Аудитория |
|---|---|---|---|
| Верхняя панель и координация | `top.py`, `cohort.py`, `onboard.py` | `python tools/onboard.py` ; `python tools/top.py buttons` | человек + агент |
| Параллельная работа и трение | `ownership.py`, `worktree.py`, `flow.py`, `merge_gate.py`, `commit_lock.py`, `stream.py`, `friction.py` | `python tools/cohort.py guard --json` | агент |
| Пирамида областей и синтез | `promote.py`, `portal.py`, `variants.py`, `synthesis_helper.py` | `python tools/promote.py list` | человек + агент |
| Знания и драйверы | `knowledge.py`, `drivers_catalog.py`, `text_extract.py`, `sandbox.py`, `sandbox_intake_demo.py` | `python tools/knowledge.py report <corpus>` | человек + агент |
| Канон и гейты | `_canon.py`, `validate.py`, `generate.py`, `pipeline.py`, `dispatch.py`, `permissions.py`, `next_id.py`, `capabilities.py`, `risk_gate.py` | `python tools/validate.py` ; `python tools/generate.py --check` | агент |
| Утилиты и диагностика | `queue.py`, `drift_check.py`, `metrics.py`, `instructions.py`, `report_diff.py`, `reconcile_state.py`, `demo_bridge.py`, `race_test.py` | `python tools/drift_check.py` ; `python tools/metrics.py` | человек + агент |

`top.py` — фасад для человека и одиночного агента; для многоагентных сценариев он делегирует в `cohort.py`.

## Как работать ОДНОМУ (cohort turn / ship, guard)

1. **Вход:** `python tools/onboard.py <agent>` — сводка манифеста возможностей, состояния конвейера, дрейфа, активных задач. Или `python tools/top.py work-mode` / `buttons`.
2. **Взять задачу:** `python tools/top.py take` или `python tools/pipeline.py next <agent>` (атомарный claim через `O_EXCL`, TTL + fencing). Готовность задачи по DAG — `python tools/dispatch.py`.
3. **Один шаг работы:** `python tools/cohort.py turn <agent>` — единичный ход в общем дереве (Уровень-0).
4. **Перед коммитом — guard:** `python tools/cohort.py guard --json` — детектор триггеров (грязные foreign-файлы, STALE-индексы, hot-files). Если чисто — остаёшься на Уровне-0.
5. **Безопасный ship:** `python tools/cohort.py ship <agent> <твои файлы> --run` — авто-регенерация навигации + selective-add + `commit_lock` (advisory-лок, TTL ~120с, `O_EXCL`) атомарно. Никогда не `git add -A`.
6. **Гейт перед merge/закрытием:** `python tools/cohort.py gate <agent>` или `python tools/merge_gate.py check` — `validate` + `generate --check` + `permissions`, опционально тесты (`--with-tests`).
7. **Закрыть:** `python tools/pipeline.py done <agent> <T-id>` или `python tools/flow.py finish <agent> <task>`.

Правило коммитов (D-019/`docs/commit-stream-policy.md`): только selective-add, только своя задача, никогда не трогай чужую недоделанную работу, один коммит — одна мысль.

## Как работать ПАРАЛЛЕЛЬНО без блокировки

Трёхуровневая дисциплина (D-019 proposed для Level-0, D-021/D-022 accepted для Level-1):

- **Уровень-0 (общее дерево):** по умолчанию. Сериализация коммитов через `commit_lock.py` (advisory, TTL). Подходит, пока `guard` не нашёл триггеров.
- **Решение L0→L1:** `python tools/cohort.py guard --json`. Триггеры из `docs/parallel-work-policy.md` / D-022: грязные foreign-файлы, STALE-индексы, hot-file contention, варианты на одном файле → рекомендация уйти в worktree.
- **Уровень-1 (изоляция):** `python tools/worktree.py spawn <agent> <task> --run` или `python tools/flow.py start <agent> <task> --worktree --run` — git-worktree на ветке `agent/<agent>/<task>`, изолированы рабочее дерево, индекс, генерируемые файлы. Полностью убирает «жду коллегу».
- **Merge назад:** `python tools/merge_gate.py check <agent> <task> [--with-tests]` (dry-by-default, exit 0/1) → владелец (Stefan/интегратор) подтверждает merge.
- **Уровень-2 (форк-варианты):** `python tools/stream.py create|list|adopt|check <topic>` — жизненный цикл пакетов в `streams/<topic>/` (draft → ready-for-review → adopted/superseded/rejected). Для содержательных вариантов (D-017 fork-and-synthesize).
- **Ownership — единый источник правды:** `tools/ownership.py classify(path)` → `mine | generated | volatile | foreign | unknown`. Правило **foreign-only**: трогаешь только своё; foreign-грязь — сигнал для guard/friction, а не повод правки.

## Governance / политики (D-016..D-022 кратко)

- **D-016 (accepted)** — Универсальное ядро + тематические порталы: домен как плагин, не в коде ядра.
- **D-017 (accepted)** — Fork-and-synthesize: параллельные варианты вместо чистого dedup для содержательных работ; перед закрытием обязателен шаг синтеза.
- **D-018 (accepted)** — Коллективное принятие решений через «котёл»: двойная перепроверка (техническая + гуманитарная); агенты предлагают, человек утверждает.
- **D-019 (proposed)** — Политика commit-streams: Level-0 сейчас (selective-add + lock), streams как полу-формат, Level-1 worktree как будущее; ждёт утверждения Stefan.
- **D-020 (proposed)** — Технический синтез T-137: тонкая автоматизация над примитивами, lifecycle streams, generic sandbox intake, promotion gate; фундамент для D-021.
- **D-021 (accepted)** — Ратификация котёл-пакета: Уровень-1 worktrees приняты как явный режим, core-export (10-файловый движок), apex-фасад (`top.py`), ясное владение merge-gate, svend4 честно BLOCKED.
- **D-022 (accepted)** — Детальная политика параллельной работы: матрица 50+ кейсов, когда Level-0 vs Level-1; триггеры STALE-индексов, same-file вариантов, hot-file contention.

Базовые документы: `PROTOCOL.md` (модель «много участников, async, append-only, одно-сообщение-один-файл»), `AGENTS.md` (реестр агентов и прав), `docs/workspace-pyramid-levels.md` (4 слоя: L1 core / L2 portals / L3 collab / L4 sandbox), `docs/parallel-work-policy.md`, `docs/commit-stream-policy.md`.

## Контур friction ↔ parallel-work (детектор ↔ исполнитель)

Два независимо построенных подсистемы сведены в один контроль-контур (см. `topics/friction-subsystems-synthesis-2026-06-22.md`):

- **Детектор (Codex-линия):** `tools/friction.py` — READ-ONLY реестр повторяющихся проблем (F-XXX): симптом → evidence → recipe. Ничего не фиксит автоматически. Учёт в `docs/friction-ledger.md`, рецепты в `docs/friction-playbook.md`. Порог автоматизации: 1 наблюдение → 2-3 playbook → 4+ инструмент → 6+ детектор → 8+ guard/gate.
- **Исполнитель (Claude-линия):** `tools/cohort.py` (`guard` решает Level-0/1, `ship` атомарно коммитит) + `commit_lock` / `worktree` / `merge_gate`.
- **Общий мост — `tools/ownership.py`:** единый классификатор dirty-файлов, которым пользуются и friction, и guard. Граница: **friction наблюдает, движок (cohort) исполняет, governance (Stefan) утверждает**.
- **Эволюция механики:** `topics/parallel-forks-history-2026-06-22.md` (selective-add → commit_lock → worktree → streams → fork-and-synthesize). Инцидент-пример: `topics/gate-poison-situation-2026-06-22.md` (F-020 — недоделанная задача блокирует всех через `validate.py` ERROR).

---
*Чистовик ведётся как живой: при изменении инструментов/политик обновлять таблицу групп и раздел governance. Связано: `core/engine-manifest.md`, `docs/top-agent-operating-manual.md`, `docs/agent-onboarding.md`.*
