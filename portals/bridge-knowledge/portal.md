---
id: portal-bridge-knowledge-l2
type: portal
level: L2
title: Bridge-knowledge (L2 — поиск по operational knowledge-корпусу)
description: L2-портал поверх универсального ядра (D-016) над РЕАЛЬНЫМ корпусом data/knowledge-corpus/ (8 файлов) — доказывает, что L2 обобщается за пределы 2-файлового demo.
core: knowledge.py + text_extract.py (универсальное ядро L1)
l1_basis: [tools/knowledge.py, tools/text_extract.py]
corpus_ref: data/knowledge-corpus
topics: [handbook, glossary, pipeline, risk, workflows]
links:
  current_state: current-state.md
  sources: sources.md
---

# Портал: bridge-knowledge (L2)

**Чистовая** L2-область поверх универсального ядра L1 (`tools/knowledge.py` + `tools/text_extract.py`),
построенная над **уже существующим** корпусом `data/knowledge-corpus/` (8 файлов: agent-handbook,
glossary, pipeline-faq, risk-register, workflow-table, operations-note, README, corpus-manifest).
Ноль новых данных — чистое переиспользование ядра через `tools/portal.py` (build → `knowledge.build`,
report → FTS5/bm25). Назначение портала — доказать, что L2-слой обобщается за пределы 2-файлового
`portals/example`, и дать второго реального потребителя ядра (закрывает корень orphan-L1: портал был один).

- **Идентичность/настройки** — этот файл (`l1_basis` = машинная опора на L1).
- **Текущее состояние** — `current-state.md`.
- **Источники** — `sources.md`.
- **Корпус (данные)** — `data/knowledge-corpus/` (операционный слой, строится `tools/portal.py`).

> Split-модель (D-021/D-016): этот L2-manifest читается `portal.py`, данные/runtime — в `data/` через `corpus_ref`.
