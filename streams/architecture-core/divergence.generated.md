---
topic: architecture-core
type: divergence-scaffold
status: proposed
agent: codex
date: 2026-06-24
---

# Divergence scaffold: architecture-core

Generated scaffold. If `divergence.md` already exists, merge manually; do not overwrite other agents.

## universal-core-portals — Универсальное ядро + тематические порталы

Evidence: 5/10 docs

Refs: `docs/optimal-information-architecture-2026-06-24.md:15`, `docs/optimal-information-architecture-2026-06-24.md:26`, `docs/optimal-information-architecture-2026-06-24.md:37`, `docs/workspace-pyramid-levels.md:5`, `docs/workspace-pyramid-levels.md:9`, +3

Claim: Доменная специфика должна жить в порталах/плагинах, а не в ядре.

Next: Clarify why accepted D-016 is under-propagated in newer architecture docs.

Позиции агентов/людей:

- (добавить позицию)

## file-section-cards — File cards / section cards / semantic elevator

Evidence: 2/10 docs

Refs: `docs/optimal-information-architecture-2026-06-24.md:26`, `docs/optimal-information-architecture-2026-06-24.md:28`, `docs/optimal-information-architecture-2026-06-24.md:44`, `docs/agent-onboarding.md:13`

Claim: Файл должен быть читаем сверху вниз: карточка, краткая карта, детали, evidence, next.

Next: Collect more variants, define minimum card schema, then decide coverage scope.

Позиции агентов/людей:

- (добавить позицию)

## DVG-001 — Физически переносить L3 в collab/ или оставить логическим слоем

Evidence: open divergence

Refs: —

Claim: Физический перенос делает архитектуру чище, но создаёт noisy diff и риск сломанных ссылок.

Next: Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.

Позиции агентов/людей:

- (добавить позицию)

## DVG-002 — Отдельная папка indexes/ или расширение существующих generated files

Evidence: open divergence

Refs: —

Claim: Новый слой улучшает понятность, но может дублировать уже работающий index.json/STATUS/board.

Next: Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.

Позиции агентов/людей:

- (добавить позицию)

## DVG-003 — File cards обязательны для всех файлов или только для важных L1/L2/policy/manual

Evidence: open divergence

Refs: —

Claim: Полное покрытие удобно машинам, но может перегрузить мелкие файлы и увеличить ритуал.

Next: Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.

Позиции агентов/людей:

- (добавить позицию)

## DVG-004 — Portal-local tools в portals/<name>/tools/ или только общий tools/

Evidence: open divergence

Refs: —

Claim: Локальные tools делают портал похожим на мини-приложение, но усложняют discovery и safety.

Next: Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.

Позиции агентов/людей:

- (добавить позицию)

## DVG-005 — GUI/кнопки сейчас или сначала CLI-контракт top.py

Evidence: open divergence

Refs: —

Claim: GUI удобен людям, но без стабильного CLI-контракта быстро станет декоративной оболочкой.

Next: Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.

Позиции агентов/людей:

- (добавить позицию)

## DVG-006 — Расширять число агентов или сначала усиливать synthesis/drain слой

Evidence: open divergence

Refs: —

Claim: Параллелизм производит больше результатов, но узкое место часто в проверке, синтезе и интеграции.

Next: Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.

Позиции агентов/людей:

- (добавить позицию)

## DVG-007 — Runner core считать завершением execute-track или только компонентом blocked umbrella

Evidence: open divergence

Refs: —

Claim: Код runner существует, но без backend/human/scenario gate execute не должен считаться operationally accepted.

Next: Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.

Позиции агентов/людей:

- (добавить позицию)
