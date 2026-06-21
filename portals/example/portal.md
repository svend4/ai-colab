---
id: portal-example-l2
type: portal
level: L2
title: Пример портала (L2 — чистовая рабочая область)
description: Первый L2-портал — present-tense область поверх универсального ядра (D-016).
core: knowledge.py + драйвер files (универсальное ядро L1)
corpus_ref: data/portals/example/corpus
topics: [alpha, beta, gamma]
links:
  current_state: current-state.md
  workflows: workflows.md
  history_l3: темы/ai-os-bridge.md
---

# Портал: пример (L2)

Это **чистовая** специализированная рабочая область (L2 пирамиды), построенная поверх универсального
ядра (L1: `tools/knowledge.py`, драйвер `files`). Историю обсуждений тут не держим — она в L3
(`темы/`, `decisions/`). Сырой вход — в L4 (`sandbox/`).

- **Идентичность/настройки** — этот файл.
- **Текущее состояние** — `current-state.md`.
- **Рабочие процессы** — `workflows.md`.
- **Корпус (данные)** — `data/portals/example/corpus/` (операционный слой, строится `tools/portal.py`).

> Открытый вопрос для котла (пирамида Q4 + интеграция `portal.py`): свести ли чистовой портал
> (`portals/`) и операционный корпус (`data/portals/`) под один `portal.py` (читать
> `portals/<name>/portal.md`, данные держать в `data/`), или оставить раздельно. См. stream
> `portal-location` (форк для синтеза с Codex, D-017).
