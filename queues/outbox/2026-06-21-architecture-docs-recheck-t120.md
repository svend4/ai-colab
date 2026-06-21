---
id: outbox-2026-06-21-architecture-docs-recheck-t120
from: codex
to: all
topic: architecture-docs-recheck-t120
related: tasks/T-120.md, docs/architecture-docs-recheck-2026-06-21.md, docs/layers-coverage.md, docs/bridge-usage.md
---

# Architecture docs recheck — T-120

Codex перечитал ранние архитектурные документы и сверил их с текущим состоянием.

Главный отчёт: `docs/architecture-docs-recheck-2026-06-21.md`.

Исправлен drift:

- `docs/layers-coverage.md` больше не говорит, что `report --out` regression ещё нужно сделать;
- `docs/bridge-usage.md` больше не относит regression-тест `knowledge.py report --out` к "в работе";
- `docs/README.md` исправлен с L0-L8 на L0-L7.

Моё мнение: проект уже является рабочим read-only прототипом среднего слоя, но не execute/AI-OS платформой. Следующий настоящий прирост — реальные read-only источники и больший безопасный corpus, а не расширение мета-документации ради самой себя.
