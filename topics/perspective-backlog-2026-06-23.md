---
id: perspective-backlog-2026-06-23
type: topic
title: Перспективный бэклог — ранжированная очередь следующих волн конвейера (самопополнение)
status: proposed
date: 2026-06-23
last_verified: 2026-06-23
related: [workflow-conveyor-policy, Q-016, Q-017, Q-013, Q-010, Q-009, T-166, T-173, T-176, T-177, T-178, T-179]
---

# Перспективный бэклог конвейера

Этот файл — стоячий источник будущих заданий для `tools/conveyor.py next`. Он должен отражать не историю всех прежних предложений, а **актуальные** кандидаты дозалива. История выполненных пунктов остаётся ниже в секции shipped/closed, чтобы верхний слой не запускал повторно уже закрытую работу.

## Состояние конвейера и что запускать дальше

Проверка T-177 после закрытия T-176:

- `python tools\top.py assurance all --json` показывает findings `[]` по applied-evidence, currency, promotion-coverage и flow;
- Q-017 semantic doc-merge закрыт в T-176: `tools/doc_consensus.py` поддерживает opt-in `report --semantic`, `--semantic-budget`, CLI/stub-agent regression-test и `status: proposed` render;
- Q-016 done-gate больше не является raw TODO: `pipeline.py done` имеет applied-evidence warning/strict gate через `_evidence_gaps`;
- F-020 gate-poison detector присутствует в `tools/friction.py` и покрыт `tools/test_friction_f020.py`;
- instruction check-report reference advisory закрыт T-166;
- orphan-L1/promotion coverage закрыт T-173, текущий assurance metric: `orphan-L1: 0`.

Вывод: предыдущий список “готовы к запуску” был полезен как исторический снимок, но больше не должен кормить workflow-conveyor. Новые кандидаты ниже направлены на следующий слой автоматизации: приём результата, регулирование флота, синтез и классификация landed outputs.

## Готовы к запуску (независимые, по out-degree)

## Готовы к запуску (независимые, по out-degree)

1. DOC_CONSENSUS_AGENT runtime recipe and safe examples
2. Workflow backlog rescan tool

## Ранжированный бэклог

| # | Тема | Value | Effort | Вид | Зависит | Почему сейчас |
|---|---|---|---|---|---|---|
| 1 | ~~Result intake classifier: classify landed/outbox outputs before verification~~ | done | M | shipped T-178 | none | Реализовано: `tools/result_intake.py classify <path> [--json]` + `tools/test_result_intake.py` + README. |
| 2 | ~~Conveyor regulate: advisory target recommendation from intake/verify/synthesis metrics~~ | done | S | shipped T-179 | T-178 | Реализовано: `tools/conveyor.py regulate` |
| 3 | ~~Synthesis gate: validate consensus/disagreement report structure~~ | done | M | shipped T-182 | none | Реализовано: проверка структуры синтеза добавлена в `validate.py` |
| 4 | ~~Process-landed classification hardening: use result-intake classes in `top.py process-landed`~~ | done | M | shipped T-183 | Result intake classifier | Реализовано: интеграция result_intake.py в команду process-landed |
| 5 | DOC_CONSENSUS_AGENT runtime recipe and safe examples | medium | S | docs/test | T-176 | T-176 закрыл seam и budget guard, но широкая semantic-сборка требует безопасного рецепта настройки `DOC_CONSENSUS_AGENT`, без auto-accept и без скрытого fan-out. |
| 6 | Workflow backlog rescan tool | medium | M | workflow | none | Этот файл пока обновляется вручную. Нужен scanner, который сверяет backlog с tasks done, assurance findings, shipped workflows и docs TODO, затем предлагает patch. |
| 7 | D-014 execute OFF ratification follow-up | high | S | governance | human approval | D-014 подготовлен T-175, но остаётся blocked до явного решения человека. Не запускать execute-build до acceptance. |
| 8 | MCP async stdio Windows follow-up | medium | M | blocked-build | T-174 unblocked | T-174 доказал, что sync gateway работает, а async stdio падает до MCP с WinError 5. Нужен отдельный runtime/env fix после появления нового факта. |
| 9 | Q-009/T-020 external code source decision | medium | S | decision | Stefan provides source or chooses generic path | Старый долг svend4/внешнего кода остаётся blocked: нужен read-only source или решение закрыть как generic local-repo sandbox path. |

## Shipped / closed после первичного бэклога

| Тема | Статус | Доказательство |
|---|---|---|
| Q-016 done-gate | shipped | `pipeline.py done --strict`, `_evidence_gaps`, applied-evidence warning/strict path; см. `docs/engine-subsystems-overview-2026-06-23.md`. |
| friction F-020 gate-poison detector | shipped | `tools/friction.py`, `tools/test_friction_f020.py`, `docs/engine-subsystems-overview-2026-06-23.md`. |
| Q-017 semantic doc-merge | shipped T-176/T-191 | `tools/doc_consensus.py`, `tools/test_doc_consensus.py`, `tools/README.md`, `queues/outbox/2026-06-23-doc-consensus-semantic-t176.md`. |
| Instruction check-report reference advisory | shipped T-166 | `tools/instructions.py`, `tools/test_instructions.py`, `tasks/T-166.md`. |
| Promotion coverage orphan-L1 closure | shipped T-173 | `portals/README.md`, `tools/assurance.py`, `tasks/T-173.md`; current assurance `orphan-L1: 0`. |
| Currency missing last_verified finding | closed/currently clean | current assurance: `0 находок актуальности; без last_verified: 0`. |
| Result intake classifier | shipped T-178 | `tools/result_intake.py`, `tools/test_result_intake.py`, `tools/README.md`. |
| Conveyor regulate advisory | shipped T-179 | `tools/conveyor.py regulate`, `tools/test_conveyor.py`, `tools/README.md`. |
| Synthesis gate | shipped T-182 | Добавлена строгая проверка в `validate.py`. |
| Process-landed classification hardening | shipped T-183 | Интеграция `result_intake.py` в `top.py process-landed`. |

## Как пользоваться

1. `python tools\conveyor.py next` должен показывать только секцию “Готовы к запуску”.
2. Если пункт из этой секции реализован, его надо перенести в shipped/closed в этом же файле или завести workflow label, который `conveyor.py` сможет дедуплицировать.
3. Если assurance/validate снова дают findings, scanner или агент должен добавить новый candidate с доказательством, а не возвращать старые закрытые формулировки.

## Моё мнение

Самая важная правка здесь не текстовая, а управленческая: бэклог не должен быть архивом старых диагнозов. Архив полезен в outbox, задачах и отчётах, но `conveyor.py next` питается именно этим файлом. Поэтому верхний слой обязан регулярно делать refresh: что закрыто — в shipped, что заблокировано — в blocked/decision, что реально следующее — в “Готовы к запуску”. Иначе система начинает тратить параллелизм на повторное выполнение уже закрытых работ.