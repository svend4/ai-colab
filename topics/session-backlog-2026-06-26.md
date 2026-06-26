---
id: session-backlog-2026-06-26
type: topic
title: Backlog доделывания — заявленные пункты сессии (simple→complex, кто владелец)
status: proposed
date: 2026-06-26
author: claude-opus-4-8
related:
  - defect-class-formula-2026-06-26
  - textscene-unified-spec-2026-06-26
  - commit-queue-and-synthesis-2026-06-26
---

# Backlog доделывания (сессия 2026-06-26)

> Список заявленных, но недоделанных/частичных пунктов, по порядку простое→сложное, с владельцем и риском
> коллизии (Codex активно правит shared-инфру → такие выношу из инлайна). ✦ = беру в этой реализации (моя
> территория, безопасно). ⛌ = требует Stefan/гейта или Codex-hot → чип/отложено.

## A. Простые (мои, делаю сейчас)
- ✦ **A1. brain-adapter `text_brain.py` (proposal-only)** — завершает трилогию textscene (scene→mux→**brain**),
  спец §5 «brain-adapter позже». Генерит `text_cell.v1` ПРЕДЛОЖЕНИЯ (status:proposed, owner:brain), НИКОГДА не
  принимает — воплощает шаг-ГЕЙТ формулы (модель предлагает, человек/гейт принимает). Offline-детерминирован.
- ✦ **A2. C-II fold-not-delete** — счётчик-противовес росту: свернуть старые `failed`-тикеты commit_queue в
  summary+указатель (патч-pointer сохранён), а не копить россыпью. Реализует контр-инвариант C-II формулы.

## B. Средние
- ✦ **B1. mutmeta --sweep findings → укрепить слабый детектор** (в полёте: свип считается; по результату возьму).
- ⛌ **B2. open #6: гейт на `decisions/D-*.md status:accepted` без следа человека → ERROR** (validate.py = Codex-hot;
  высокая ценность-безопасность). → чип/координация.
- ⛌ **B3. open #8: unit-тест heartbeat** (pipeline.py область; нужен изолированный COLLAB_ROOT). → можно мне, но
  трогает pipeline-тесты — координация.

## C. Сложные / процессные
- ⛌ **C1. open #1: единый `CANON_DIRS`-реестр** (закрывает ВЕСЬ класс silent-drift f: metrics/promote/instructions/
  generate/portal/edges). Codex-hot, мульти-файловый атомарный фикс → чип `task_8f0b4a99` (узкий) + реестр позже.
- ⛌ **C2. open #7: T-148 enforcement** (cohort guard печатает→блокирует). Codex-hot → координация.
- ⛌ **C3. open #4: worktree/merge_gate по умолчанию + ротация интегратора** — governance, нужен Stefan.
- ⛌ **C4. open #5: проблема оракула** — открытый фронтир (D-030), исследование, не «доделка».
- **C5. commit-policy: перевести всех агентов на `enqueue→turn→commit→done`** — D-031 ратифицирован; включение
  как обязательного протокола для ВСЕХ агентов = решение процесса (Stefan/гейт).

## Сделанное этой сессией (для контекста)
commit_queue (D-031) · repo_hygiene · workflow_recover · mutmeta(+sweep) · формула-документ+аудит · textscene
trilogy(scene/mux) · TVCP-патчи · единый спек. Всё под тестами.
