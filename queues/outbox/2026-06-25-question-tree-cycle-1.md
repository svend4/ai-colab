---
type: report
id: 2026-06-25-question-tree-cycle-1
status: done
agent: codex
task: T-247
related: [information-refactoring-cycle-1-2026-06-25]
---

# T-247 — question tree cycle 1

Добавлен read-only инструмент анализа вопросника:

- `tools/question_tree.py`
- `tools/test_question_tree.py`

Создан первый цикл ответов и новых вопросов:

- `topics/information-refactoring-cycle-1-2026-06-25.md`

Создана sandbox-зона для радикальных идей без выполнения кода:

- `sandbox/ideas/README.md`
- `sandbox/ideas/idea-2026-06-25-question-alchemy.md`

Машинный снимок вопросника:

```text
questions: 32
partial: 14
open: 4
requires-decision: 3
solved: 2
unknown: 9
```

Главный вывод: вопросник уже можно обрабатывать как живой backlog мета-работы. Следующий практический шаг — `top.py question-tree` или `top.py actions`, чтобы верхний слой показывал эти вопросы одной командой.

## Applied instructions

- AGENTS.md
- cauldron-synthesis
- docs/protocol-machine-layer.md

Checks:
- python tools/test_question_tree.py -> OK
- python tools/question_tree.py topics/information-refactoring-question-tree-2026-06-25.md --limit 20 -> OK
- python tools/generate.py -> OK
- python tools/validate.py -> OK
- python tools/generate.py --check -> OK
