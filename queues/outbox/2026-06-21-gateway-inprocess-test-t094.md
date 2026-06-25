---
id: outbox-2026-06-21-gateway-inprocess-test-t094
from: codex
to: all
topic: gateway-inprocess-test-t094
related: tasks/T-094.md, docs/gateway-inprocess-test-result-2026-06-21.md, drivers/gateway/test_gateway.py
status: historical
---

# Gateway in-process test — T-094

Codex перепроверил gateway in-process regression test и адаптировал его под локальный Windows runtime:

- стандартный `tempfile.mkdtemp()` заменён на общий `drivers/test_tmp.py`;
- `python drivers\gateway\test_gateway.py` проходит;
- проверяется composition, redaction, allowed-root confinement и audit без MCP stdio.

Моё мнение: это полезная регрессия рядом с `T-088`, но она не заменяет отдельную MCP `call_tool` acceptance.
