---
id: 2026-07-07-additive-enrichment-and-bulk-range-codex
type: outbox
status: proposed
agent: codex
date: 2026-07-07
related: [T-294, T-295, T-296, D-026]
---

# Additive enrichment and bulk range gate

Codex вынес на обсуждение additive-список задач и начал реализацию с T-294.

## Итог

- Созданы задачи T-294, T-295, T-296.
- T-294 реализован как новый режим `tools/bulk_guard.py --range BASE..HEAD --json`.
- Добавлен тест `tools/tests/test_bulk_guard_range.py`.
- Подагенты Nash и Meitner работали read-only и подтвердили выбор T-294 как полезного первого hardening-направления.

## Следующие безопасные additive-задачи

1. T-295 — cauldron materializer: превращать отчёты агентов в варианты для synthesis.
2. Package handoff: выдавать worker/scout пакет в JSON/prompt без ложного claim.
3. Package gate wakeup advisory: показывать зависшие medium-пакеты без автоматического утверждения.
4. D-033 brief-only: подготовить human-gate справку, не ратифицируя решение.

## Проверки

См. `reports/bulk-guard-range-gate-implementation-2026-07-07.md`.