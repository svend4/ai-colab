---
type: report
agent: codex
date: 2026-06-24
topic: document-synthesis-v2
status: historical
related: 
applied: AGENTS.md, PROTOCOL.md, decisions/D-017.md, decisions/D-018.md, docs/document-synthesis-mechanism-2026-06-24.md, tools/doc_synthesis.py, tools/top.py, Checks
---

# Отчёт: document synthesis v2

## Что сделано

Закрыт следующий слой `doc_synthesis`:

1. `python tools\doc_synthesis.py candidates architecture-core` — поиск документов-кандидатов.
2. Source-line evidence — темы и lanes получают refs вида `file:line`.
3. `python tools\doc_synthesis.py scan architecture-core --with-streams` — явное создание stream scaffold.
4. `python tools\top.py synthesize-docs architecture-core ...` — верхняя обёртка для людей и агентов.
5. Существующий `streams/architecture-core/divergence.md` не перезаписывается: при наличии ручного файла создаётся `streams/architecture-core/divergence.generated.md`.

## Проверенный пример

```powershell
python tools\doc_synthesis.py candidates architecture-core --limit 5 --json
python tools\top.py synthesize-docs architecture-core --json
python tools\top.py synthesize-docs architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md --with-streams
```

Результаты:

- обновлён `docs/architecture-core-documents-synthesis-2026-06-24.md`;
- создан `streams/architecture-core/README.generated.md`;
- создан `streams/architecture-core/divergence.generated.md`;
- обновлены `docs/document-synthesis-mechanism-2026-06-24.md`, `docs/cauldron-two-lane-board-2026-06-24.md`, `docs/top-layer-command-groups.md`;
- обновлён `system-capabilities.json`.

## Safety

Решение остаётся `proposed`. Инструмент не принимает accepted-решения, не стирает чужие divergence-позиции и пишет только по явному `--out` или `--with-streams`.

Checks:
- python -m py_compile tools\doc_synthesis.py tools\top.py tools\test_doc_synthesis.py tools\test_top.py
- python tools\test_doc_synthesis.py
- python tools\test_top.py
- python tools\doc_synthesis.py candidates architecture-core --limit 5 --json
- python tools\top.py synthesize-docs architecture-core --json
- python tools\top.py synthesize-docs architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md --with-streams
- python tools\capabilities.py snapshot
- python tools\generate.py
- python tools\validate.py
- python tools\generate.py --check
- python tools\drift_check.py
- python tools\assurance.py all