---
id: portal-example-l2
type: portal
level: L2
title: Пример портала (L2 — чистовая рабочая область)
description: Первый L2-портал — present-tense область поверх универсального ядра (D-016).
l1_basis: [tools/knowledge.py]
corpus_ref: data/portals/example/corpus
topics: [alpha, beta, gamma]
links:
  current_state: current-state.md
  workflows: workflows.md
  history_l3: topics/ai-os-bridge.md
---

# Портал: пример (L2)

Это **чистовая** специализированная рабочая область (L2 пирамиды), построенная поверх универсального
ядра (L1: `tools/knowledge.py`, драйвер `files`). Историю обсуждений тут не держим — она в L3
(`topics/`, `decisions/`). Сырой вход — в L4 (`sandbox/`).

- **Идентичность/настройки** — этот файл.
- **Текущее состояние** — `current-state.md`.
- **Рабочие процессы** — `workflows.md`.
- **Корпус (данные)** — `data/portals/example/corpus/` (операционный слой, строится `tools/portal.py`).

> Решение D-021/T-145: split-модель принята. `portal.py` читает этот L2 manifest, а данные/runtime остаются в `data/portals/example/` через `corpus_ref`.
