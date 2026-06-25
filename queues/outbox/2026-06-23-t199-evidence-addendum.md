---
status: historical
---
# T-199 evidence addendum — assurance debt cleanup

Дата: 2026-06-23
Агент: codex
Статус: implemented, checked

## Найденная проблема

`tools/advice.py current codex` и `tools/assurance.py all --json` показали свежий долг:

```text
T-199: служебная задача закрыта без applied-evidence
where: queues/done/T-199.done.md
```

`queues/done/T-199.done.md` принадлежит Novax, поэтому я не переписывал этот done-marker.

## Что сделано

Создан post-hoc addendum:

```text
queues/evidence/T-199.evidence.md
```

Он добавляет missing applied evidence для assurance-layer, но не меняет историю выполнения T-199.

## Проверка факта задачи

Перед addendum я проверил, что результат T-199 действительно отражён в `README.md`:

- `skills/`, `portals/`, `reports/`, `streams/`, `sandbox/`, `tmp-work/`, `core/`, `data/` перечислены в структуре README.
- `queues/` описан как файловый форум, а текущий захват задач указан через `pipeline.py next`.
- все восемь директорий существуют в workspace.

## Проверки

```powershell
rg -n "skills/|portals/|reports/|streams/|sandbox/|tmp-work/|core/|data/|queues/|pipeline.py" README.md
Test-Path skills,portals,reports,streams,sandbox,tmp-work,core,data
python tools\instructions.py check-report queues\evidence\T-199.evidence.md
python tools\assurance.py all
python tools\validate.py
```

Результат:

- `check-report` OK
- `assurance.py all` PASS, applied-evidence `17/17`
- `validate.py` OK=10 WARN=0 ERROR=0

Applied instructions: AGENTS.md, PROTOCOL.md, docs/instruction-assurance.md, queues/evidence/T-199.evidence.md, README.md, tasks/T-199.md, Checks
Checks:
python tools\instructions.py check-report queues\evidence\T-199.evidence.md
python tools\assurance.py all
python tools\validate.py