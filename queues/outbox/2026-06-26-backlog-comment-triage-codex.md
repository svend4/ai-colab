---
type: outbox
title: Backlog comment triage - 2026-06-26
date: 2026-06-26
author: codex
status: outbox
related:
  - D-031
  - commit-queue-and-synthesis-2026-06-26
---

# Backlog comment triage

## Что перепроверено

После накопления нескольких блоков комментариев/отчетов рабочее дерево было разделено на безопасные группы.
Цель: не смешивать смысловые отчеты, generated indexes, временные runtime-логи и sandbox-материалы в один commit.

## Блок A — уже закрыт

Generated-синхронизация для принятого решения D-031 зафиксирована отдельно. Это были только:

- `DECISIONS.md`
- `index.json`
- `indexes/decisions.md`

Причина: source decision `decisions/D-031.md` уже был в истории, а generated summaries отставали.

## Блок B — безопасные outbox-отчеты

Эти файлы являются осмысленными сообщениями для людей и агентов, их можно фиксировать отдельным commit:

- `queues/outbox/2026-06-26-conceptual-stage-recheck-codex.md`
- `queues/outbox/2026-06-26-full-audit-codex.md`
- `queues/outbox/reconcile-20260624-202016.md`
- `queues/outbox/reconcile-20260624-202016.json`

Проверки:

- JSON reconcile читается и имеет `status=warning`, `error=0`, `warning=50`, `info=1`.
- `full-audit` получил front-matter, чтобы его было легче индексировать/читать агентам.

## Блок C — пока не коммитить без отдельной ревизии

Эти материалы оставлены как рабочие черновики или тяжелые runtime-артефакты:

- `reports/audit_*.json` и `reports/output_*.log` — диагностические логи, требуют политики retention.
- `sandbox/tvcp_fetched/` — внешний код/документы TVCP; нужен отдельный provenance/README и возможно размерная проверка.
- `sandbox/tvcp_design/` — полезные design variants, но это отдельный смысловой пакет.
- `sandbox/canvas-demo/` — demo-data для text_mux/text_scene, нужен отдельный тест или README.
- `sandbox/paradigm_shift/` — экспериментальный код, нужен sandbox review.
- `test_guard.md` — похоже на искусственный guard/test fixture, не коммитить без задачи.
- `topics/alchemy_synthesis_20260625_144041.md` — тема без front-matter; требует нормализации как topic или переноса в sandbox/outbox.

## Рекомендация следующего шага

1. Зафиксировать Блок B отдельным commit.
2. Затем взять `sandbox/tvcp_design/` как отдельный пакет: проверить README/источник/ценность и решить, делать topic или оставить sandbox.
3. После этого отдельно обработать `sandbox/tvcp_fetched/`, потому это внешний материал и его нельзя смешивать с собственными выводами.
