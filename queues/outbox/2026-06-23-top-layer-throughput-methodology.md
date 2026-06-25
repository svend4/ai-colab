---
id: outbox-2026-06-23-top-layer-throughput-methodology
type: report
status: historical
agent: codex
related: T-169, docs/top-layer-throughput-methodology.md, skills/top-layer-orchestrator/SKILL.md, docs/agent-capacity-methodology.md
---

# Top-layer throughput methodology — отчёт Codex

По запросу Stefan оформлена методология верхнего слоя: как обрабатывать результаты множества агентов,
чтобы реальный bottleneck был управляемым.

Главное: верхний слой — это не ещё один worker, а control plane:

```text
SENSE -> INTAKE -> TRIAGE -> VERIFY -> SYNTHESIZE -> DECIDE -> COMMIT -> FEEDBACK
```

Что добавлено:

- `docs/top-layer-throughput-methodology.md` — подробная схема обработки landed/outbox результатов;
- `skills/top-layer-orchestrator/SKILL.md` — короткая процедура для агента-диспетчера;
- `tasks/T-169.md` — задача закрыта как done.

Ключевые решения:

- не запускать новые workflow, если есть `PROCESS` или landed без output-ref;
- не считать одинаковые темы дублями автоматически: сначала отделять duplicate noise от variant/confirmation/conflict;
- build и governance не обрабатывать как обычный read-only report;
- commit делать коротким batch под lock, после проверки и synthesis;
- `target` повышать только когда верхний слой реально успевает обрабатывать очередь.

Applied instructions:

- `AGENTS.md` / `PROTOCOL.md`: чужие сообщения и чужие изменения не переписаны; добавлены `docs/top-layer-throughput-methodology.md`, `skills/top-layer-orchestrator/SKILL.md`, `queues/outbox/2026-06-23-top-layer-throughput-methodology.md`, `tasks/T-169.md`.
- `docs/instruction-assurance.md`: отчёт содержит evidence, related files и Checks.
- `docs/skills-usage.md`: `skills/top-layer-orchestrator/SKILL.md` оформлен как project-local L3 skill, не как plugin.
- Checks: `python tools/generate.py`; `python tools/validate.py`; `python tools/instructions.py check-report queues/outbox/2026-06-23-top-layer-throughput-methodology.md`.