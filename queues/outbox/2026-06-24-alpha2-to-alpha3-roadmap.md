---
type: report
id: 2026-06-24-alpha2-to-alpha3-roadmap
status: historical
agent: codex
task: T-245
related: [alpha2-to-alpha3-roadmap-2026-06-24]
---

# Alpha-2 -> Alpha-3 roadmap package

По просьбе пользователя кодовая реализация приостановлена до согласования плана. Подготовлен proposed-roadmap:

- `topics/alpha2-to-alpha3-roadmap-2026-06-24.md`

Ключевая рекомендация: не добавлять новые документы ради документов, а переводить повторяющиеся рекомендации в машинные проверки, top-команды, тесты и workflow.

Ближайшая предлагаемая очередь:

- [ ] `top.py cli-risk` - верхняя команда над `cli_inventory.py`.
- [ ] `top.py actions` - верхняя команда над `action_tracker.py status`.
- [ ] `top.py alpha-status` - текущая стадия и score проекта.
- [ ] report footer validator для `Applied instructions` и `Checks:`.
- [ ] CLI-risk batch 2 для маленьких read-only tools.

Статус: `proposed`, не `accepted`. Следующий кодовый шаг должен начинаться только после коллективного подтверждения или явного продолжения.

## Applied instructions

- AGENTS.md
- docs/protocol-machine-layer.md
- User request: сначала план, потом применение

Checks:
- python tools/generate.py -> OK
- python tools/validate.py -> OK
- python tools/generate.py --check -> OK