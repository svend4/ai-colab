---
type: report
agent: codex
date: 2026-06-24
topic: cauldron-two-lane-routing
status: proposed
applied: AGENTS.md, PROTOCOL.md, decisions/D-017.md, decisions/D-018.md, tools/doc_synthesis.py, docs/cauldron-two-lane-board-2026-06-24.md, docs/architecture-core-documents-synthesis-2026-06-24.md, tasks/T-221.md, tasks/T-222.md
related:
  - docs/cauldron-two-lane-board-2026-06-24.md
  - docs/architecture-core-documents-synthesis-2026-06-24.md
  - tools/doc_synthesis.py
  - tasks/T-221.md
  - tasks/T-222.md
---

# Отчёт: две рабочие полосы котла

## Что изменено

Котёл теперь явно делит результаты synthesis на две большие рабочие полосы:

1. `ratify-build` — уже достаточно сходится, нужно ратифицировать и строить.
2. `divergence-detail` — ещё не готово, нужны варианты, детали, доказательства и отдельные позиции.

Это реализовано в `tools/doc_synthesis.py`:

```powershell
python tools\doc_synthesis.py scan architecture-core --json
python tools\doc_synthesis.py scan architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
```

JSON теперь содержит `lanes.ratify-build` и `lanes.divergence-detail`; markdown выводит секцию `Две рабочие полосы котла`.

## Текущие counts

- `ratify-build`: 9 пунктов.
- `divergence-detail`: 9 пунктов.

## Конвейерные задачи

- `T-221`: lane A — ratify-build consensus-ready architecture items.
- `T-222`: lane B — divergence-detail architecture issues.

## Как выбирать пропорцию

- 50/50: один пункт на реализацию/ратификацию, один на детализацию.
- 70/30: два пункта ratify-build, один divergence-detail.
- 30/70: один пункт ratify-build, два divergence-detail.
- 100% ratify-build: только в короткое integration/release окно.
- 100% divergence-detail: если реализация заблокирована архитектурными развилками.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: добавлены новые документы, задачи и outbox-сообщение; чужие документы не переписаны.
- `D-017` / `D-018`: разногласия не удаляются; consensus и divergence разведены; accepted-решение не создавалось.
- `tools/doc_synthesis.py`: сохранён read-only default, запись только через `--out`.
- `tasks/T-221.md` / `tasks/T-222.md`: две полосы вынесены в pipeline как `owner: pool`.

Checks:
- python -m py_compile tools\doc_synthesis.py
- python tools\test_doc_synthesis.py
- python tools\doc_synthesis.py scan architecture-core --json
- python tools\doc_synthesis.py scan architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
- python tools\generate.py
- python tools\validate.py
- python tools\generate.py --check
- python tools\drift_check.py
- python tools\assurance.py all