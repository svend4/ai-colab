---
id: outbox-2026-06-25-agent-approval-matrix
type: report
status: proposed
from: codex
to: all
related: [T-250, Q-023, D-027]
created: 2026-06-25
---

# Outbox - T-250 agent approval matrix

## Что сделано

- Запущены два platform sub-agents как read-only scouts:
  - Huygens: audit существующих policies и approval gaps.
  - Planck: audit question-tree/action-plan и следующих долгов.
- Оба workflow зафиксированы в `tools/conveyor.py` как `t250-huygens` и `t250-planck`.
- Scout outputs сохранены:
  - `queues/outbox/2026-06-25-scout-huygens-approval-policy.md`
  - `queues/outbox/2026-06-25-scout-planck-question-tree.md`
- Создан `docs/agent-approval-matrix.md`.
- Создан proposed decision `decisions/D-027.md`.
- Q-023 получил proposed answer, но остаётся open до human/appointed integrator acceptance.
- `docs/agent-roles-matrix.md` получил cross-link: роли отдельно, полномочия отдельно.

## Consensus scouts

- Матрица полномочий нужна до расширения числа агентов.
- Read-only scout fan-out безопаснее build fan-out.
- Observer/coordinator должен сводить 2-3 scout outputs.
- Accepted governance, execute sandbox, strict validators и массовые изменения требуют человека или appointed integrator.
- Следующий `top.py actions` должен учитывать permission lane.

## Remaining decisions

1. Кто может быть appointed integrator?
2. Где фиксировать human approval?
3. Какие Red-ladder действия всегда требуют явного approval?
4. Когда advisory check можно переводить в strict?
5. Нужно ли поле `approval_required` во front matter?

## Applied instructions

- AGENTS.md: решения не утверждены как accepted; subagents работали read-only.
- PROTOCOL.md: T-250 claim/done workflow; отчеты в outbox.
- docs/agent-launch-workflow.md: platform launcher отделён от repo-flow.
- docs/workflow-conveyor-policy.md: workflow зафиксированы через conveyor land/output.
- cauldron-synthesis: scout consensus и divergence сохранены; governance remains proposed.

## Checks

- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> OK=12 WARN=0 ERROR=0
- OK: `python tools\generate.py --check`
- OK: `python tools\conveyor.py land t250-planck --output queues\outbox\2026-06-25-scout-planck-question-tree.md`
- OK: `python tools\conveyor.py land t250-huygens --output queues\outbox\2026-06-25-scout-huygens-approval-policy.md`
- OK: `python tools\conveyor.py ship t250-planck`
- OK: `python tools\conveyor.py ship t250-huygens`
- NOTE: final `python tools\conveyor.py status --json` shows landed=0, shipped=52, deficit=2/REFILL for the next workflow wave.

Checks:
python tools\instructions.py check-report queues\outbox\2026-06-25-agent-approval-matrix.md

Note: included as proposed evidence for T-250/D-027/Q-023; no accepted decision made.
