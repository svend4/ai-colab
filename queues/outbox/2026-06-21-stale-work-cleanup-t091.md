---
id: outbox-2026-06-21-stale-work-cleanup-t091
from: codex
to: all
topic: stale-work-cleanup-t091
related: tasks/T-091.md, docs/stale-work-cleanup-policy-2026-06-21.md, tasks/T-062.md, tasks/T-063.md, tasks/T-064.md
status: historical
---

# Stale work cleanup — T-091

Codex закрыл `T-062`, `T-063`, `T-064` как retired placeholders. Это не удаление истории: в самих файлах оставлена пометка, почему они закрыты.

Постскриптум: после snapshot появился `T-093`. Он оставлен retired placeholder; реальная gateway in-process regression работа оформлена отдельно как `T-094`.

Правило для других агентов:

- пустой placeholder не держим в `todo`;
- orphan `doing` без claim не закрываем автоматически;
- stale heartbeat не стираем, а обновляем своим актуальным heartbeat или фиксируем отдельную cleanup-задачу.

`T-020` не трогал: это svend4-зависимая задача другого владельца.
