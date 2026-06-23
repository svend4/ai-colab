---
type: report
agent: codex
task: T-176
title: doc_consensus semantic hybrid opt-in
date: 2026-06-23
---

# T-176 — doc_consensus semantic hybrid

## What changed

Закрыта прикладная часть Q-017 для `tools/doc_consensus.py`: семантическое слияние документов оформлено как opt-in режим `report --semantic`, без замены обычного лексического пути.

Сделано:

- `--semantic-budget N` ограничивает максимум subprocess-agent batches и останавливает команду до fan-out, если бюджет недостаточен;
- `analyze_semantic(..., budget=N)` использует тот же guard, что и CLI;
- regression-test фиксирует слепое пятно Jaccard: две разные формулировки одной идеи остаются divergent в обычном режиме, но stub-agent в semantic режиме поднимает их в consensus;
- CLI-тест проверяет реальный `DOC_CONSENSUS_AGENT` seam, запись отчёта и `status: proposed`;
- `tools/README.md` описывает режим как proposed-material для D-017/D-018, без auto-accept.

## Result

T-176 можно считать выполненной как инфраструктурную задачу. Реальная широкая semantic-сборка по policy-докам остаётся отдельным runtime-шагом: ей нужен настроенный `DOC_CONSENSUS_AGENT` и явный бюджет.

## Checks

Checks:
python -m py_compile tools\doc_consensus.py tools\test_doc_consensus.py
python tools\test_doc_consensus.py
python tools\doc_consensus.py report --semantic --semantic-budget 0 --files docs\parallel-work-policy.md docs\commit-stream-policy.md

Последняя команда ожидаемо возвращает exit code 1 и текст `semantic budget exceeded: need 7 agent calls, budget 0`; это проверка fail-fast guard, а не регрессия.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: задача взята через pipeline claim; общий итог записан в `queues/outbox/` и `tasks/T-176.md`.
- `tasks/T-176.md`: критерии opt-in semantic, regression-test, budget guard и документация закрыты.
- `tools/doc_consensus.py`: режим `--semantic` оставлен opt-in; default lexical mode не заменён.
- `tools/test_doc_consensus.py`: добавлен тест subprocess-agent seam и fail-fast budget guard.
- `tools/README.md`: добавлена инструкция для людей и агентов, когда включать semantic hybrid.
- `decisions/D-017.md` и `decisions/D-018.md`: результат остаётся `status: proposed`; consensus не принимается автоматически.
- Commit safety: commit и staging не выполнялись из-за общего dirty-tree.