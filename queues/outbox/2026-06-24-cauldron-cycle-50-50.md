---
type: report
agent: codex
date: 2026-06-24
topic: cauldron-cycle-50-50
status: historical
related: 
applied: AGENTS.md, PROTOCOL.md, decisions/D-017.md, decisions/D-018.md, docs/cauldron-two-lane-board-2026-06-24.md, tasks/T-221.md, tasks/T-222.md, Checks
---

# Отчёт: цикл котла 50/50

## Что сделано

Выполнен один цикл по модели 50/50:

1. `ratify-build`: выбран пункт `top-layer-facade` из `T-221`.
2. `divergence-detail`: выбран спор `DVG-006` из `T-222`.

## Lane A — build result

Добавлена верхняя команда:

```powershell
python tools\top.py cauldron-lanes architecture-core
python tools\top.py cauldron-lanes architecture-core --json
python tools\top.py cauldron-lanes architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
```

Смысл: человек или агент больше не обязан помнить внутреннюю команду `doc_synthesis.py scan ...`; две полосы котла доступны через верхнюю панель `top.py`.

## Lane B — detail result

Создана детализация `DVG-006`:

```text
streams/architecture-core/DVG-006-scale-vs-upper-layer.md
```

Предложенный компромисс: `gated scale`.

- read-only fan-out можно расширять шире;
- build в shared tree держать узким;
- governance/accepted оставлять за human/integrator gate;
- если landed/outbox/results не обработаны, сначала drain/synthesis, потом новый запуск агентов.

## Почему так

Работа выполнена по `cauldron-synthesis` skill: разногласия не стирались, accepted-решение не создавалось. Это реализует правило двух полос: consensus-ready пункт превращён в кодовую обёртку, а спорный пункт не стёрт и не принят молча, а вынесен в отдельный divergence-detail с evidence и критерием перехода в `ratify-build`.

Checks:
- python -m py_compile tools\top.py tools\doc_synthesis.py
- python tools\test_top.py
- python tools\test_doc_synthesis.py
- python tools\top.py cauldron-lanes architecture-core --json
- python tools\capabilities.py snapshot
- python tools\generate.py
- python tools\validate.py
- python tools\generate.py --check
- python tools\drift_check.py
- python tools\assurance.py all
- python tools\pipeline.py status