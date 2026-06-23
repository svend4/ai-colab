---
type: report
agent: codex
task: T-179
title: conveyor regulate advisory
status: proposed
date: 2026-06-23
---

# T-179 — conveyor regulate advisory

## What changed

Добавлен read-only advisory для workflow-conveyor target sizing: `tools/conveyor.py regulate`.

Команды:

```powershell
python tools\conveyor.py regulate
python tools\conveyor.py regulate --json
python tools\conveyor.py regulate --json --no-assurance
```

Рекомендации:

- `increase`: можно поднять target на 1;
- `hold`: target не менять, сначала refill/fix текущую цель;
- `decrease`: orchestration stale/idle, снизить давление или tick/land/ship;
- `process-first`: есть landed/missing-output, сначала обработать результаты.

Команда не мутирует state: `mutates: false`. Она не вызывает `conveyor.py target`, не запускает агентов и не ship'ит workflows.

## Result

T-179 закрывает следующий слой после T-178: теперь верхний слой имеет не только классификатор результата, но и advisory, который объясняет, можно ли масштабировать workflow-флот.

Текущий smoke на реальном `logs/conveyor.json`: recommendation `decrease`, reason `orchestrator idle ...; tick/land/ship before growing fleet`.

## Checks

Checks:
python -m py_compile tools\conveyor.py tools\test_conveyor.py
python tools\test_conveyor.py
python tools\conveyor.py regulate --json --no-assurance
python tools\conveyor.py regulate --no-assurance
python tools\validate.py
python tools\generate.py --check

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: задача взята через pipeline claim; результат вынесен в `queues/outbox/`.
- `tasks/T-179.md`: критерии advisory regulate, no mutation, tests закрыты.
- `tools/conveyor.py`: добавлены `regulate`, `render_regulate`, assurance summary и landed classification hook.
- `tools/test_conveyor.py`: добавлены сценарии increase/hold/process-first/decrease/assurance-hold.
- `tools/result_intake.py`: используется best-effort для классификации landed outputs.
- `tools/README.md` и `docs/top-layer-throughput-methodology.md`: документация обновлена.
- `topics/perspective-backlog-2026-06-23.md`: T-179 перенесён в shipped/closed.
- Checks: команды перечислены выше; результаты проверяются перед закрытием задачи.
- Commit safety: commit и staging не выполнялись в dirty shared tree.