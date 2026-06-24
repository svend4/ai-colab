---
id: pipeline-reconciliation-current-blockers-2026-06-24
title: Pipeline reconciliation — current blockers and cleanup
status: proposed
owner: Codex
related: tasks/T-194.md, tasks/T-202.md, queues/outbox/2026-06-24-pipeline-reconciliation-cleanup-report.md, docs/stale-work-cleanup-policy-2026-06-21.md, docs/state-reconciliation-layer.md
---

# Pipeline reconciliation — current blockers and cleanup

Дата: 2026-06-24.

## Что проверено

Перед cleanup конвейер показывал пять not-ready/blocker пунктов и ни одной ready-задачи:

- `T-020` — внешний источник/репозиторий ещё не передан; блокер реальный.
- `T-174` — async stdio MCP acceptance заблокирован Windows/Python runtime; sync gateway работает, но официальный async путь не закрыт.
- `T-194` — пустой placeholder без работы; ложный шум.
- `T-202` — commit-задача со stale claim; реальная интеграционная проблема, но старый scope уже небезопасен.
- `T-208` — execute sandbox runner заблокирован до human/governance gate; блокер реальный.

## Что изменено

1. `T-194` закрыт как `Retired placeholder — no task assigned`.
2. Создан `queues/done/T-194.done.md`, чтобы `reconcile_state.py` не считал закрытие неполным.
3. `T-202` переведён из ложного `doing` в явный `blocked`.
4. Старый claim `queues/claimed/T-202.claim.md` не удалялся: это чужой временный след, его можно отдельно убрать только по принятой cleanup-политике или через назначенного интегратора.

## Почему T-202 не коммитится автоматически

Commit-задача — это не обычный текстовый cleanup. Она меняет историю Git и может случайно включить чужие незавершённые файлы. Старый список `T-202` уже не совпадает с текущим `git status`: появились новые направления работы и файлы других агентов.

Правильный следующий шаг — свежий commit-intake:

1. Сначала человек или назначенный интегратор выбирает scope: какие задачи и файлы входят в commit.
2. Агент запускает `git status --short` и сверяет scope с реальными изменениями.
3. Агент запускает `python tools/generate.py`, `python tools/validate.py`, `python tools/generate.py --check`, `python tools/drift_check.py`.
4. Агент проверяет `python tools/commit_lock.py`.
5. Только после этого делается selective-add и commit.

## Методологический вывод

Для верхнего слоя управления важен не максимум параллельных агентов, а качество intake/synthesis/landing. Если ready-pool пустой, агент не должен бесконечно ждать или брать placeholder. Он должен выполнить reconciliation: отделить реальные blockers от ложного шума, закрыть пустые резервы по политике, а рискованные действия перевести в явные gated tasks.

Это уменьшает задержки и делает систему более динамичной: агенты видят не просто “всё заблокировано”, а точную карту — что можно исправить автоматически, что требует человека, что требует внешнего источника, а что требует отдельного интегратора.