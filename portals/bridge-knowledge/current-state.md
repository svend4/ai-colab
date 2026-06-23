# Bridge-knowledge — текущее состояние

- **Корпус:** `data/knowledge-corpus/` — 8 файлов (готовый, проверенный); отчёт прогона —
  `reports/knowledge-corpus-report.md`.
- **Ядро (L1):** `tools/knowledge.py` (FTS5 + bm25, files-драйвер) + `tools/text_extract.py` (извлечение).
- **Построение:** `python tools/portal.py` над `corpus_ref` (см. `portal.md`) — нового кода нет, чистое
  переиспышользование ядра.
- **Статус:** present-tense L2; история обсуждений — в L3 (`topics/`, `decisions/`), не здесь.
