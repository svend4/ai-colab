---
id: portal-example-current-state
portal: portal-example-l2
updated: 2026-06-21
---

# Текущее состояние — портал «пример»

- **Назначение:** демонстрация модели D-016 (универсальное ядро + тематический портал-плагин, «как
  портал на Википедии»).
- **Корпус:** 2 файла (`note-alpha.md`, `note-beta.txt`) в `data/portals/example/corpus/`.
- **Темы:** alpha, beta, gamma (gamma пока без покрытия — это видно в отчёте `portal.py report`).
- **Движок:** read-only `tools/knowledge.py` (поиск FTS5+bm25 по содержимому через `text_extract`,
  с redaction секретов).
- **Статус:** зелёный демо — `tools/test_portal.py` проходит.
- **Что сюда НЕ входит:** споры и история разработки (→ L3 `темы/`/`decisions/`), сырой внешний
  непроверенный вход (→ L4 `sandbox/`), half-done эксперименты.
