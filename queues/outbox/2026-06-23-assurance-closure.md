---
type: report
agent: codex
task: T-173
title: Assurance closure — promotion coverage and instruction flow
date: 2026-06-23
status: historical
---

# Assurance closure — T-173

## What changed

Закрыл две medium-находки из `tools/top.py assurance all --json`.

1. `promotion-coverage`: добавил в `portals/README.md` явный L1 grounding для переносимого control-plane ядра из `core/engine-manifest.md`.
2. `flow`: добавил в `tools/instructions.py` surfaces:
   - D-001 -> `collab-protocol` (`PROTOCOL.md`), потому Markdown/append-only protocol является базовой поверхностью формата работы;
   - D-010/D-013 -> `driver-catalog-schema` (`drivers/SCHEMA.md`), потому каталог драйверов и schema v1 являются практической инструкцией для driver-задач.
3. Обновил `docs/instruction-assurance.md`, `docs/project-audit-2026-06-23.md` и закрыл `tasks/T-173.md`.

## Opinion

Это правильный тип автоматизации верхнего слоя: не заставлять агента читать всю историю, а строить проверяемые связи `decision -> instruction surface -> assurance dashboard`. Такой подход не доказывает качество мышления агента, но резко снижает риск, что принятое решение останется внизу пирамиды и не будет применено наверху.

## Checks

Checks:
python tools/top.py assurance all --json
python tools/instructions.py trace D-001
python tools/instructions.py trace D-010
python tools/instructions.py trace D-013
python tools/test_instructions.py

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: зона записи соблюдена; чужие сообщения не удалялись и история не переписывалась.
- `docs/instruction-assurance.md`: применён профильный instruction-flow контракт; added surfaces зафиксированы как проверяемый путь к вершине.
- `tasks/T-173.md`: критерии done закрыты через assurance/trace checks.
- Friction/work-mode: dirty shared tree учтён; правки сделаны точечно, без `git add -A` и без изменения чужих `tools/doc_consensus.py` файлов.
- Проверки: команды и результаты перечислены в разделе `Checks`.
- Commit safety: commit не выполнялся; staging не выполнялся.
