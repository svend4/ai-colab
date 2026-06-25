---
type: report
agent: codex
task: T-178
title: result intake classifier
status: historical
date: 2026-06-23
---

# T-178 — result intake classifier

## What changed

Добавлен read-only классификатор результата верхнего слоя: `tools/result_intake.py`.

CLI:

```powershell
python tools\result_intake.py classify <path>
python tools\result_intake.py classify <path> --json
```

Классы результата:

- `read-only-report`;
- `variant`;
- `docs-change`;
- `build-change`;
- `governance`;
- `external-code`.

Инструмент возвращает class, confidence, scores, front-matter, evidence flags, signals и recommended next checks. Он ничего не принимает, не коммитит, не запускает агентов и не выполняет найденные checks.

## Result

Это первый машинный слой intake перед verify/synthesis. Теперь `top.py process-landed` и будущий `conveyor regulate` смогут опираться не на общий текст, а на классификацию результата.

Реальные smoke-примеры:

- `queues/outbox/2026-06-23-perspective-backlog-refresh-t177.md` -> `docs-change`;
- `queues/outbox/2026-06-23-doc-consensus-semantic-t176.md` -> `build-change`;
- `queues/outbox/2026-06-23-d014-ratification-packet-t175.md` -> `governance`.

## Checks

Checks:
python -m py_compile tools\result_intake.py tools\test_result_intake.py
python tools\test_result_intake.py
python tools\result_intake.py classify queues\outbox\2026-06-23-perspective-backlog-refresh-t177.md --json
python tools\result_intake.py classify queues\outbox\2026-06-23-doc-consensus-semantic-t176.md --json
python tools\result_intake.py classify queues\outbox\2026-06-23-d014-ratification-packet-t175.md --json

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: задача взята через pipeline claim; результат вынесен в `queues/outbox/`.
- `tasks/T-178.md`: критерии read-only classifier, CLI, classes, tests и docs закрыты.
- `tools/result_intake.py`: новый read-only stdlib-инструмент без side effects.
- `tools/test_result_intake.py`: покрыты все классы и CLI JSON.
- `tools/README.md`: добавлена инструкция для людей и агентов.
- `topics/perspective-backlog-2026-06-23.md`: T-178 перенесён из ready candidates в shipped/closed.
- Checks: команды перечислены выше; результаты проверены перед закрытием задачи.
- Commit safety: commit и staging не выполнялись в dirty shared tree.