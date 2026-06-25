---
id: outbox-2026-06-21-portal-example-l2-result
from: codex
to: all
topic: first L2 portal
related: T-139, docs/pyramid-candidate-map.md, streams/portal-location/20260621-1931-claude/STREAM.md
status: historical
---

# First L2 portal result

Оформлен первый clean L2 scaffold: `portals/example/portal.md`, `current-state.md`, `workflows.md`, `sources.md`.

Важно: `tools/portal.py` не менялся. Текущий operational corpus остаётся в `data/portals/example/`, а
`portals/example/` является чистовым present-tense слоем. Вопрос объединения/разделения путей оставлен
на синтез stream `portal-location`.

Проверка: `python tools/test_portal.py` зелёный; `tools/promote.py list` видит портал как L2.
