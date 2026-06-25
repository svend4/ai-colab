---
id: outbox-2026-06-23-top-process-landed
type: report
status: historical
agent: codex
related: T-170, tools/top.py, tools/test_top.py, docs/top-layer-throughput-methodology.md, skills/top-layer-orchestrator/SKILL.md
---

# Top process-landed — отчёт Codex

Добавлена read-only команда верхнего слоя:

```powershell
python tools\top.py process-landed
python tools\top.py process-landed --json
python tools\top.py process-landed --all --topic <topic>
```

Назначение: превратить landed очередь из “надо помнить в голове” в машинный план обработки.
Команда не делает commit, не ship'ит workflow и не запускает новых агентов. Она только показывает, что делать дальше.

Поведение:

- `state: empty` — landed outputs нет; если conveyor сообщает `IDLE`/`REFILL`, команда передаёт это как advice;
- `state: missing-output` — есть landed без output-ref; новый fan-out надо остановить до привязки или dismiss;
- `state: ready` — выбран первый landed output или все через `--all`; команда печатает verify/synthesis/ship-after-review шаги.

Почему это важно:

- верхний слой теперь имеет первую кнопку для стадии INTAKE -> VERIFY -> SYNTHESIZE;
- это снижает риск потерять output, перепутать дубли с вариантами или повысить target при необработанной очереди;
- автоматизация остаётся безопасной, потому commit и governance остаются ручными/под gate.

Applied instructions:

- `AGENTS.md` / `PROTOCOL.md`: изменения добавлены как отдельная задача, docs, skill update и outbox; чужие сообщения не переписаны.
- `docs/top-layer-throughput-methodology.md`: T-170 реализует запланированный `process-landed` как read-only advisory.
- `docs/instruction-assurance.md`: отчёт содержит applied instructions и проверяемые Checks.
- Checks: `python tools/top.py process-landed --json`; `python tools/test_top.py`; `python tools/generate.py`; `python tools/validate.py`; `python tools/instructions.py check-report queues/outbox/2026-06-23-top-process-landed.md`.