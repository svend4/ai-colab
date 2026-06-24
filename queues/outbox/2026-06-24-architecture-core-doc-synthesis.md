---
type: report
agent: codex
date: 2026-06-24
topic: architecture-core-document-synthesis
status: proposed
applied: AGENTS.md, PROTOCOL.md, decisions/D-017.md, decisions/D-018.md, tools/doc_synthesis.py, docs/document-synthesis-mechanism-2026-06-24.md, docs/architecture-core-documents-synthesis-2026-06-24.md, streams/architecture-core/divergence.md, tasks/T-218.md
related:
  - docs/document-synthesis-mechanism-2026-06-24.md
  - docs/architecture-core-documents-synthesis-2026-06-24.md
  - streams/architecture-core/README.md
  - streams/architecture-core/divergence.md
  - tools/doc_synthesis.py
  - tasks/T-218.md
---

# Отчёт: сверка архитектурных документов

## Что сделано

Проверен и применён существующий механизм котла:

- `tools/variants.py` — находит зарегистрированные варианты;
- `tools/synthesis_helper.py` — строит skeleton для тем из streams;
- `streams/` — хранит divergence/форки;
- `D-017` / `D-018` — запрещают стирать разногласия и принимать спорное без человека.

Найден пробел: обычные `docs/*.md` и `queues/outbox/*.md`, написанные разными агентами, не всегда зарегистрированы как stream-варианты. Поэтому добавлен read-only инструмент:

```powershell
python tools\doc_synthesis.py scan architecture-core
```

## Корпус

Просканировано 10 документов:

1. `docs/optimal-information-architecture-2026-06-24.md`
2. `docs/workspace-pyramid-levels.md`
3. `docs/top-layer-throughput-methodology.md`
4. `docs/top-layer-command-groups.md`
5. `docs/orchestration-architecture-2026-06-23.md`
6. `docs/workflow-conveyor-policy.md`
7. `docs/agent-capacity-methodology.md`
8. `docs/agent-onboarding.md`
9. `queues/outbox/2026-06-23-lagrange-nested-system.md`
10. `queues/outbox/2026-06-23-lagrange-nested-system-continuation.md`

## Результаты

Сформирован proposed-синтез:

- `docs/architecture-core-documents-synthesis-2026-06-24.md`

Counts:

- Documents scanned: 10
- Consensus themes: 9
- Near-consensus themes: 1
- Minority useful themes: 1
- Divergences listed: 7
- Question snippets: 26
- Proposal snippets: 42

## Верхний consensus

Сильный consensus найден по темам:

1. L1/L2/L3/L4 и разделение чистовика/истории/хаоса.
2. Верхний фасад команд.
3. Workflow-conveyor и дисциплина intake -> verify -> synthesize -> integrate.
4. Варианты не удалять: synthesis + divergence streams.
5. Evidence/assurance/checks/applied instructions.
6. Worktree/merge-gate/commit-lock для параллельной работы.
7. Metadata/front-matter/indexes/navigation.
8. Execute OFF до backend/human/preflight/decision gate.
9. Recursive self-improvement: friction -> playbook -> tool -> guard -> assurance.

## Средний слой

`universal core + portals` найден как 4/10 по keyword scan. Это не отменяет `D-016`; наоборот, показывает propagation gap: принятое решение есть, но не все новые документы явно повторяют core and portal vocabulary.

## Нижний слой / разногласия

Создан stream:

- `streams/architecture-core/divergence.md`

Там вынесены 7 спорных пунктов:

1. L3 physical `collab/` migration vs logical layer.
2. New `indexes/` folder vs extending existing generated files.
3. File cards for all significant files vs L1/L2/policy-first.
4. Portal-local tools vs shared tools only.
5. GUI now vs CLI contract first.
6. Scale more agents vs strengthen upper-layer synthesis/drain first.
7. Runner core done vs umbrella execute-track remains blocked until backend/human/scenario gate.

## Следующая задача

Создана `T-218`: Document synthesis v2 — candidates, source-line evidence, `--with-streams`, top.py wrapper.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: добавлены новые документы, outbox-сообщение, stream и task, чужие документы не переписывались.
- `D-017` / `D-018`: consensus отделён от divergence; статус proposed; accepted-решение не создавалось.
- Локальный cauldron-synthesis skill: разногласия вынесены в stream, mainline synthesis не скрывает спорные пункты.
- `tools/doc_synthesis.py`: новый инструмент read-only по умолчанию; запись только через `--out`.

Checks:
- python tools\doc_synthesis.py scan architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
- python tools\test_doc_synthesis.py
- python tools\generate.py
- python tools\validate.py
- python tools\generate.py --check
- python tools\drift_check.py
- python tools\assurance.py all