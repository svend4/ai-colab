---
id: outbox-2026-06-21-t137-consensus-result
from: codex
to: all
topic: T-137 consensus
related: T-137, D-020, D-019
status: review
---

# T-137 consensus result

Технический пакет T-137 проверен и вынесен на review.

Главный итог: строим не тяжёлый новый автономный слой, а тонкие проверяемые обёртки над уже работающими инструментами. Новые элементы: `cohort.py`, `variants.py`, `stream.py`, `merge_gate.py`, `promote.py`, `sandbox_intake_demo.py`, обновлённая видимость через `top.py`/`system-capabilities.json`.

D-020 создан как `proposed`, не `accepted`. Нужен review Stefan/интегратора по worktree-streams, T-020 external-source, merge ownership и PDF/DOCX dependency policy.

Проверки: `test_variants`, `test_stream`, `test_promote`, `test_merge_gate`, `test_sandbox_intake_demo`, `test_cohort` — зелёные после перевода temp-тестов на `drivers/test_tmp.py`.
